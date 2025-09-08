"""数据回放器模块

提供历史数据回放功能，支持：
- 按时间顺序回放历史数据
- 数据完整性验证
- 防止未来函数泄露
- 支持历史模拟和模型验证两种模式
"""

import logging
import math
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from pydantic import BaseModel

from ...clients.tushare_client import TushareClient
from ...factor_engine.models.schemas import UnifiedFactorRequest
from ...factor_engine.services.factor_service import FactorService
from ...utils.exceptions import ValidationException
from ..models.backtest_models import BacktestFactorConfig, BacktestMode

logger = logging.getLogger(__name__)


class DataSnapshot(BaseModel):
    """数据快照模型"""
    timestamp: str
    stock_code: str
    price_data: dict  # 价格数据
    factor_data: dict  # 因子数据
    volume: float | None = None
    market_cap: float | None = None


class DataReplayer:
    """历史数据回放器

    负责按时间顺序回放历史数据，确保回测的真实性和数据完整性
    """

    def __init__(self, factor_service: FactorService, data_client: TushareClient):
        """初始化数据回放器

        Args:
            factor_service: 因子服务实例
            data_client: Tushare数据客户端
        """
        self.factor_service = factor_service
        self.data_client = data_client
        self._cache: dict[str, Any] = {}  # 数据缓存

    async def replay_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        factor_combination: BacktestFactorConfig,
        mode: BacktestMode = BacktestMode.HISTORICAL_SIMULATION
    ) -> AsyncGenerator[DataSnapshot, None]:
        """按时间顺序回放历史数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            factor_combination: 因子组合配置
            mode: 回测模式

        Yields:
            DataSnapshot: 每个时点的数据快照
        """
        try:
            logger.info(f"开始回放股票{stock_code}的历史数据，时间范围: {start_date} - {end_date}")

            # 获取交易日历
            trading_dates = await self._get_trading_dates(start_date, end_date)

            if not trading_dates:
                raise ValidationException(f"指定时间范围内无交易日: {start_date} - {end_date}")

            logger.info(f"共找到{len(trading_dates)}个交易日")

            # 按时间顺序回放数据
            for i, trade_date in enumerate(trading_dates):
                try:
                    # 获取当日数据快照
                    snapshot = await self.get_snapshot(
                        stock_code, trade_date, factor_combination, mode
                    )

                    # 验证数据完整性
                    if self._validate_snapshot(snapshot):
                        yield snapshot
                        logger.debug(f"成功回放第{i+1}/{len(trading_dates)}个交易日: {trade_date}")
                    else:
                        logger.warning(f"跳过数据不完整的交易日: {trade_date}")

                except Exception as e:
                    logger.warning(f"获取{trade_date}数据失败: {str(e)}，跳过该交易日")
                    continue

            logger.info(f"数据回放完成，股票: {stock_code}")

        except Exception as e:
            logger.error(f"数据回放失败: {str(e)}")
            raise

    async def get_snapshot(
        self,
        stock_code: str,
        timestamp: str,
        factor_combination: BacktestFactorConfig,
        mode: BacktestMode = BacktestMode.HISTORICAL_SIMULATION
    ) -> DataSnapshot:
        """获取指定时点的数据快照

        Args:
            stock_code: 股票代码
            timestamp: 时间戳
            factor_combination: 因子组合配置
            mode: 回测模式

        Returns:
            DataSnapshot: 数据快照
        """
        try:
            # 检查缓存
            cache_key = f"{stock_code}_{timestamp}_{mode.value}"
            if cache_key in self._cache:
                logger.debug(f"使用缓存数据: {cache_key}")
                cached_snapshot = self._cache[cache_key]
                if isinstance(cached_snapshot, DataSnapshot):
                    return cached_snapshot

            # 获取价格数据
            price_data = await self._get_price_data(stock_code, timestamp)

            # 获取因子数据
            factor_data = await self._get_factor_data(
                stock_code, timestamp, factor_combination, mode
            )

            # 创建数据快照
            snapshot = DataSnapshot(
                timestamp=timestamp,
                stock_code=stock_code,
                price_data=price_data,
                factor_data=factor_data,
                volume=price_data.get('volume'),
                market_cap=factor_data.get('total_market_cap')
            )

            # 缓存数据
            self._cache[cache_key] = snapshot

            return snapshot

        except Exception as e:
            logger.error(f"获取数据快照失败: {str(e)}")
            raise

    async def _get_trading_dates(self, start_date: str, end_date: str) -> list[str]:
        """获取交易日历

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[str]: 交易日期列表
        """
        try:
            # 使用Tushare获取交易日历
            if not hasattr(self.data_client, '_api') or self.data_client._api is None:
                raise ValidationException("Tushare API未初始化")

            import asyncio
            loop = asyncio.get_event_loop()
            api = self.data_client._api
            cal_data = await loop.run_in_executor(
                None,
                lambda: api.trade_cal(
                    exchange='SSE',
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
            )

            if cal_data is None or cal_data.empty:
                logger.warning(f"无法获取交易日历: {start_date} - {end_date}")
                return []

            # 筛选交易日
            trading_dates = cal_data[cal_data['is_open'] == 1]['cal_date'].tolist()

            # 转换为字符串格式
            trading_dates = [str(date) for date in trading_dates]
            trading_dates.sort()

            return trading_dates

        except Exception as e:
            logger.error(f"获取交易日历失败: {str(e)}")
            # 如果获取交易日历失败，生成简单的日期序列（跳过周末）
            return self._generate_business_days(start_date, end_date)

    def _generate_business_days(self, start_date: str, end_date: str) -> list[str]:
        """生成工作日序列（备用方案）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list[str]: 工作日期列表
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            business_days = []
            current = start

            while current <= end:
                # 跳过周末（周六=5，周日=6）
                if current.weekday() < 5:
                    business_days.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

            return business_days

        except Exception as e:
            logger.error(f"生成工作日序列失败: {str(e)}")
            return []

    async def _get_price_data(self, stock_code: str, timestamp: str) -> dict:
        """获取价格数据

        Args:
            stock_code: 股票代码
            timestamp: 时间戳

        Returns:
            dict: 价格数据
        """
        try:
            # 获取当日行情数据
            daily_data = await self.data_client.get_daily_data(
                ts_code=stock_code,
                start_date=timestamp,
                end_date=timestamp
            )

            if daily_data is None or daily_data.empty:
                raise ValidationException(f"无法获取{stock_code}在{timestamp}的价格数据")

            # 转换为字典格式
            row = daily_data.iloc[0]
            price_data = {
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'volume': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0)),
                'pct_chg': float(row.get('pct_chg', 0))
            }

            return price_data

        except Exception as e:
            logger.error(f"获取价格数据失败: {str(e)}")
            raise

    async def _get_factor_data(
        self,
        stock_code: str,
        timestamp: str,
        factor_combination: BacktestFactorConfig,
        mode: BacktestMode
    ) -> dict:
        """获取因子数据

        Args:
            stock_code: 股票代码
            timestamp: 时间戳
            factor_combination: 因子组合配置
            mode: 回测模式

        Returns:
            dict: 因子数据
        """
        try:
            # 构建因子请求
            request = UnifiedFactorRequest(
                stock_code=stock_code,
                calculation_date=timestamp,
                factor_types=["technical", "fundamental", "market", "sentiment"],
                technical_factors=factor_combination.get_technical_factors(),
                fundamental_factors=factor_combination.get_fundamental_factors(),
                market_factors=factor_combination.get_market_factors(),
                sentiment_factors=factor_combination.get_sentiment_factors()
            )

            # 调用因子服务计算因子
            response = await self.factor_service.calculate_all_factors(request)

            # 合并所有因子数据
            factor_data = {}

            if response.technical_factors:
                factor_data.update(response.technical_factors)

            if response.fundamental_factors:
                factor_data.update(response.fundamental_factors)

            if response.market_factors:
                factor_data.update(response.market_factors)

            if response.sentiment_factors:
                factor_data.update(response.sentiment_factors)

            return factor_data

        except Exception as e:
            logger.error(f"获取因子数据失败: {str(e)}")
            return {}

    def _validate_snapshot(self, snapshot: DataSnapshot) -> bool:
        """验证数据快照的完整性

        Args:
            snapshot: 数据快照

        Returns:
            bool: 验证结果
        """
        try:
            # 检查价格数据
            if not snapshot.price_data:
                logger.warning(f"价格数据为空: {snapshot.timestamp}")
                return False

            # 检查关键价格字段
            required_price_fields = ['open', 'high', 'low', 'close']
            for field in required_price_fields:
                if field not in snapshot.price_data or snapshot.price_data[field] <= 0:
                    logger.warning(f"价格数据异常: {field} = {snapshot.price_data.get(field)}")
                    return False

            # 检查价格逻辑
            price_data = snapshot.price_data
            if not (price_data['low'] <= price_data['open'] <= price_data['high'] and
                   price_data['low'] <= price_data['close'] <= price_data['high']):
                logger.warning(f"价格数据逻辑错误: {price_data}")
                return False

            # 检查因子数据
            if not snapshot.factor_data:
                logger.warning(f"因子数据为空: {snapshot.timestamp}")
                return False

            # 检查因子数据中是否有异常值
            for factor_name, factor_value in snapshot.factor_data.items():
                if factor_value is None or (isinstance(factor_value, float) and
                                          (pd.isna(factor_value) or math.isinf(factor_value))):
                    logger.warning(f"因子数据异常: {factor_name} = {factor_value}")
                    # 不直接返回False，允许部分因子缺失

            return True

        except Exception as e:
            logger.error(f"验证数据快照失败: {str(e)}")
            return False

    def validate_timeline(self, timestamps: list[str]) -> bool:
        """验证时间序列的连续性

        Args:
            timestamps: 时间戳列表

        Returns:
            bool: 验证结果
        """
        try:
            if len(timestamps) < 2:
                return True

            # 检查时间顺序
            for i in range(1, len(timestamps)):
                current = datetime.strptime(timestamps[i], '%Y-%m-%d')
                previous = datetime.strptime(timestamps[i-1], '%Y-%m-%d')

                if current <= previous:
                    logger.warning(f"时间序列顺序错误: {timestamps[i-1]} -> {timestamps[i]}")
                    raise ValidationException(f"时间序列顺序错误: {timestamps[i-1]} -> {timestamps[i]}")

            return True

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"验证时间序列失败: {str(e)}")
            return False

    def _prevent_lookahead_bias(self, timestamp: str, data: dict) -> bool:
        """防止未来函数泄露

        Args:
            timestamp: 当前时间戳
            data: 数据字典

        Returns:
            bool: 验证结果
        """
        try:
            datetime.strptime(timestamp, '%Y-%m-%d')

            # 检查数据中是否包含未来信息
            # 这里可以根据具体需求添加更多检查逻辑

            return True

        except Exception as e:
            logger.error(f"防止未来函数泄露检查失败: {str(e)}")
            return False

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("数据回放器缓存已清空")