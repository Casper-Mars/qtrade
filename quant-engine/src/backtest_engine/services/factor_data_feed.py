"""因子数据源模块

本模块实现Backtrader兼容的因子数据源：
- 集成因子服务和市场数据
- 提供统一的数据接口
- 支持历史数据回放
- 数据预处理和格式化
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import backtrader as bt
import pandas as pd

from ...clients.tushare_client import TushareClient
from ...factor_engine.services.factor_service import FactorService
from ..models.backtest_models import BacktestFactorConfig

logger = logging.getLogger(__name__)


class FactorDataFeed(bt.feeds.PandasData):
    """基于因子的数据源

    继承自Backtrader的PandasData，添加因子数据支持
    """

    # 扩展数据列定义
    lines = ('factor_data',)  # 添加因子数据线

    # 参数定义
    params = (
        ('factor_service', None),      # 因子服务实例
        ('data_client', None),         # 数据客户端
        ('stock_code', None),          # 股票代码
        ('start_date', None),          # 开始日期
        ('end_date', None),            # 结束日期
        ('factor_combination', None),   # 因子组合配置
        ('datetime', 0),               # 日期时间列索引
        ('open', 1),                   # 开盘价列索引
        ('high', 2),                   # 最高价列索引
        ('low', 3),                    # 最低价列索引
        ('close', 4),                  # 收盘价列索引
        ('volume', 5),                 # 成交量列索引
        ('factor_data', 6),            # 因子数据列索引
    )

    def __init__(self, **kwargs):
        """初始化数据源"""
        # 提取自定义参数
        self.factor_service: FactorService = kwargs.pop('factor_service', None)
        self.data_client: TushareClient = kwargs.pop('data_client', None)
        self.stock_code: str = kwargs.pop('stock_code', None)
        self.start_date: str = kwargs.pop('start_date', None)
        self.end_date: str = kwargs.pop('end_date', None)
        self.factor_combination: BacktestFactorConfig = kwargs.pop('factor_combination', None)

        # 验证必要参数
        if not all([self.factor_service, self.data_client, self.stock_code,
                   self.start_date, self.end_date, self.factor_combination]):
            raise ValueError("缺少必要的初始化参数")

        # 准备数据
        dataframe = self._prepare_data()

        # 调用父类初始化
        super().__init__(dataname=dataframe, **kwargs)

        logger.info(f"因子数据源初始化完成: {self.stock_code}, {len(dataframe)} 条记录")

    def _prepare_data(self) -> pd.DataFrame:
        """准备回测数据

        Returns:
            包含价格和因子数据的DataFrame
        """
        try:
            # 1. 获取价格数据
            price_data = self._get_price_data()

            # 2. 获取因子数据
            factor_data = self._get_factor_data()

            # 3. 合并数据
            merged_data = self._merge_data(price_data, factor_data)

            # 4. 数据预处理
            processed_data = self._preprocess_data(merged_data)

            return processed_data

        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            raise

    def _get_price_data(self) -> pd.DataFrame:
        """获取价格数据

        Returns:
            价格数据DataFrame
        """
        try:
            # 使用Tushare客户端获取日线数据
            price_data = self.data_client.get_daily_data(
                ts_code=self.stock_code,
                start_date=self.start_date.replace('-', ''),
                end_date=self.end_date.replace('-', '')
            )

            if price_data.empty:
                raise ValueError(f"未获取到价格数据: {self.stock_code}")

            # 数据格式化
            price_data['trade_date'] = pd.to_datetime(price_data['trade_date'], format='%Y%m%d')
            price_data = price_data.sort_values('trade_date')
            price_data.set_index('trade_date', inplace=True)

            # 重命名列以匹配Backtrader格式
            column_mapping = {
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume'
            }


            price_data = price_data.rename(columns=column_mapping)

            # 选择需要的列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            price_data = price_data[required_columns]

            logger.info(f"获取价格数据成功: {len(price_data)} 条记录")
            return price_data

        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            raise

    def _get_factor_data(self) -> pd.DataFrame:
        """获取因子数据

        Returns:
            因子数据DataFrame
        """
        try:
            # 提取因子名称列表
            factor_names = [factor.factor_name for factor in self.factor_combination.factors]

            # 分类因子（预留用于后续扩展）
            # technical_factors = [name for name in factor_names if 'technical' in name.lower()]
            # fundamental_factors = [name for name in factor_names if 'fundamental' in name.lower()]
            # market_factors = [name for name in factor_names if 'market' in name.lower()]

            # 获取因子历史数据
            # 注意：这里需要根据实际的FactorService接口进行调整
            factor_data_list = []

            # 模拟获取因子数据的过程
            # 实际实现中需要调用factor_service的相应方法
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')

            current_dt = start_dt
            while current_dt <= end_dt:
                # 跳过周末
                if current_dt.weekday() < 5:  # 0-4 表示周一到周五
                    factor_record = {
                        'trade_date': current_dt,
                        'stock_code': self.stock_code
                    }

                    # 为每个因子生成模拟数据
                    # 实际实现中应该调用factor_service获取真实数据
                    for factor_name in factor_names:
                        # 生成模拟因子值
                        import random
                        factor_record[factor_name] = random.uniform(0.3, 0.7)

                    factor_data_list.append(factor_record)

                current_dt += timedelta(days=1)

            # 转换为DataFrame
            factor_data = pd.DataFrame(factor_data_list)

            if not factor_data.empty:
                factor_data.set_index('trade_date', inplace=True)

            logger.info(f"获取因子数据成功: {len(factor_data)} 条记录, {len(factor_names)} 个因子")
            return factor_data

        except Exception as e:
            logger.error(f"获取因子数据失败: {e}")
            # 返回空DataFrame，避免程序崩溃
            return pd.DataFrame()

    def _merge_data(self, price_data: pd.DataFrame, factor_data: pd.DataFrame) -> pd.DataFrame:
        """合并价格和因子数据

        Args:
            price_data: 价格数据
            factor_data: 因子数据

        Returns:
            合并后的数据
        """
        try:
            if factor_data.empty:
                # 如果没有因子数据，创建空的因子数据列
                merged_data = price_data.copy()
                merged_data['factor_data'] = None
            else:
                # 按日期合并数据
                merged_data = price_data.join(factor_data, how='left')

                # 将因子数据打包到factor_data列
                factor_columns = [col for col in merged_data.columns
                                if col not in ['open', 'high', 'low', 'close', 'volume']]

                def pack_factors(row):
                    factor_dict = {}
                    for col in factor_columns:
                        if col != 'stock_code':  # 排除非因子列
                            factor_dict[col] = row[col]
                    return factor_dict

                merged_data['factor_data'] = merged_data.apply(pack_factors, axis=1)

                # 删除原始因子列，只保留打包后的factor_data列
                merged_data = merged_data[['open', 'high', 'low', 'close', 'volume', 'factor_data']]

            logger.info(f"数据合并完成: {len(merged_data)} 条记录")
            return merged_data

        except Exception as e:
            logger.error(f"数据合并失败: {e}")
            raise

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理

        Args:
            data: 原始数据

        Returns:
            预处理后的数据
        """
        try:
            # 1. 处理缺失值
            data = data.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

            # 2. 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

            # 3. 数据验证
            # 确保价格数据的逻辑性
            invalid_rows = (
                (data['high'] < data['low']) |
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close']) |
                (data['volume'] < 0)
            )

            if invalid_rows.any():
                logger.warning(f"发现 {invalid_rows.sum()} 条无效数据，已删除")
                data = data[~invalid_rows]

            # 4. 重置索引确保连续性
            data = data.sort_index()

            logger.info(f"数据预处理完成: {len(data)} 条有效记录")
            return data

        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            raise

    def get_data_info(self) -> dict[str, Any]:
        """获取数据源信息

        Returns:
            数据源信息字典
        """
        return {
            'stock_code': self.stock_code,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'factor_count': len(self.factor_combination.factors) if self.factor_combination else 0,
            'factor_names': [f.factor_name for f in self.factor_combination.factors] if self.factor_combination else [],
            'data_length': len(self.dataname) if hasattr(self, 'dataname') else 0
        }
