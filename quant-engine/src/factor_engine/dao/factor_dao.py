"""因子数据访问层模块

提供统一的因子数据访问接口，整合数据库操作和缓存操作。
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from redis import Redis
from sqlalchemy.orm import Session

from ..models.database import TechnicalFactor
from .base import FundamentalFactorDAO, TechnicalFactorDAO
from .cache import FactorCacheManager

logger = logging.getLogger(__name__)


class FactorDAO:
    """因子数据访问对象

    整合数据库操作和缓存操作，提供统一的数据访问接口
    """

    def __init__(self, db_session: Session, redis_client: Redis):
        """初始化因子数据访问对象

        Args:
            db_session: 数据库会话
            redis_client: Redis客户端
        """
        self.db_session = db_session
        self.redis_client = redis_client

        # 初始化各类型因子的DAO
        self.technical_dao = TechnicalFactorDAO(db_session)
        self.fundamental_dao = FundamentalFactorDAO(db_session)

        # 初始化缓存管理器
        self.cache_manager = FactorCacheManager(redis_client)

    async def save_technical_factor(
        self,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        trade_date: str
    ) -> bool:
        """保存技术因子数据

        Args:
            stock_code: 股票代码
            factor_name: 因子名称
            factor_value: 因子值
            trade_date: 交易日期

        Returns:
            保存是否成功
        """
        try:
            # 转换日期格式
            trade_date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()

            # 检查是否已存在相同记录
            existing_factors = self.technical_dao.get_by_stock_and_date(
                stock_code=stock_code,
                trade_date=trade_date_obj
            )

            # 查找是否已存在相同因子
            existing_factor: TechnicalFactor | None = None
            for factor in existing_factors:
                if factor.factor_name == factor_name:
                    existing_factor = factor
                    break

            if existing_factor:
                # 更新现有记录
                success = self.technical_dao.update(
                    factor_id=int(existing_factor.id),
                    factor_value=factor_value
                )
            else:
                # 创建新记录
                factor = self.technical_dao.create(
                    stock_code=stock_code,
                    factor_name=factor_name,
                    factor_value=factor_value,
                    trade_date=trade_date_obj
                )
                success = factor is not None

                # 提交事务
                if success:
                    self.db_session.commit()

            # 缓存数据
            if success:
                self.cache_manager.cache_technical_factor(
                    stock_code=stock_code,
                    factor_name=factor_name,
                    trade_date=trade_date_obj,
                    factor_value=factor_value
                )

            return success

        except Exception as e:
            logger.error(f"保存技术因子数据失败: {str(e)}")
            self.db_session.rollback()
            return False

    async def get_factor_history(
        self,
        stock_code: str,
        factor_name: str,
        start_date: str,
        end_date: str
    ) -> list[dict[str, Any]]:
        """获取因子历史数据

        Args:
            stock_code: 股票代码
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据列表
        """
        try:
            # 转换日期格式
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

            # 从数据库查询历史数据
            factors = self.technical_dao.get_by_stock_and_factor(
                stock_code=stock_code,
                factor_name=factor_name,
                start_date=start_date_obj,
                end_date=end_date_obj
            )

            # 转换为字典格式
            result = []
            for factor in factors:
                result.append({
                    'trade_date': factor.trade_date,
                    'factor_value': factor.factor_value,
                    'created_at': factor.created_at,
                    'updated_at': factor.updated_at
                })

            return result

        except Exception as e:
            logger.error(f"获取因子历史数据失败: {str(e)}")
            return []

    async def get_stock_price_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取股票价格数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            价格数据DataFrame
        """
        try:
            # 这里应该调用数据采集服务的API获取价格数据
            # 暂时返回模拟数据用于测试

            # TODO: 实际实现中需要调用data-collector服务的API
            # 或者直接查询股票价格数据表

            # 模拟价格数据
            import numpy as np

            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            n_days = len(date_range)

            if n_days == 0:
                return pd.DataFrame()

            # 生成模拟价格数据
            base_price = 100.0
            price_data = {
                'trade_date': date_range,
                'open': base_price + np.random.normal(0, 2, n_days),
                'high': base_price + np.random.normal(2, 2, n_days),
                'low': base_price + np.random.normal(-2, 2, n_days),
                'close': base_price + np.random.normal(0, 2, n_days),
                'volume': np.random.randint(1000000, 10000000, n_days)
            }

            df = pd.DataFrame(price_data)

            # 确保high >= max(open, close), low <= min(open, close)
            df['high'] = df[['open', 'high', 'close']].max(axis=1)
            df['low'] = df[['open', 'low', 'close']].min(axis=1)

            logger.info(f"获取股票{stock_code}价格数据，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取股票价格数据失败: {str(e)}")
            return pd.DataFrame()

    async def get_cached_factors(
        self,
        stock_code: str,
        factor_names: list[str],
        calculation_date: str
    ) -> dict[str, float]:
        """获取缓存的因子数据

        Args:
            stock_code: 股票代码
            factor_names: 因子名称列表
            calculation_date: 计算日期

        Returns:
            缓存的因子数据
        """
        try:
            cached_factors = {}
            calculation_date_obj = datetime.strptime(calculation_date, '%Y-%m-%d').date()

            for factor_name in factor_names:
                cached_data = self.cache_manager.get_technical_factor(
                    stock_code=stock_code,
                    factor_name=factor_name,
                    trade_date=calculation_date_obj
                )

                if cached_data and 'factor_value' in cached_data:
                    cached_factors[factor_name] = cached_data['factor_value']

            return cached_factors

        except Exception as e:
            logger.warning(f"获取缓存因子数据失败: {str(e)}")
            return {}

    async def cache_factors(
        self,
        stock_code: str,
        calculation_date: str,
        factors_data: dict[str, float],
        ttl: int = 3600
    ) -> None:
        """缓存因子数据

        Args:
            stock_code: 股票代码
            calculation_date: 计算日期
            factors_data: 因子数据
            ttl: 缓存过期时间（秒）
        """
        try:
            calculation_date_obj = datetime.strptime(calculation_date, '%Y-%m-%d').date()

            for factor_name, factor_value in factors_data.items():
                self.cache_manager.cache_technical_factor(
                    stock_code=stock_code,
                    factor_name=factor_name,
                    trade_date=calculation_date_obj,
                    factor_value=factor_value
                )

            logger.debug(f"成功缓存股票{stock_code}的因子数据")

        except Exception as e:
            logger.warning(f"缓存因子数据失败: {str(e)}")

    async def get_latest_factors(
        self,
        stock_code: str,
        factor_names: list[str],
        limit: int = 1
    ) -> list[dict[str, Any]]:
        """获取最新的因子数据

        Args:
            stock_code: 股票代码
            factor_names: 因子名称列表
            limit: 返回记录数量限制

        Returns:
            最新的因子数据列表
        """
        try:
            latest_factors = self.technical_dao.get_latest_by_stock(
                stock_code=stock_code,
                limit=limit * len(factor_names)
            )

            # 过滤指定的因子名称
            filtered_factors = [
                factor for factor in latest_factors
                if factor.factor_name in factor_names
            ]

            # 转换为字典格式
            result = []
            for factor in filtered_factors:
                result.append({
                    'factor_name': factor.factor_name,
                    'factor_value': factor.factor_value,
                    'trade_date': factor.trade_date,
                    'created_at': factor.created_at
                })

            return result

        except Exception as e:
            logger.error(f"获取最新因子数据失败: {str(e)}")
            return []

    def close(self) -> None:
        """关闭数据库连接"""
        if self.db_session:
            self.db_session.close()

        if self.redis_client:
            self.redis_client.close()
