"""市场因子计算器模块

提供各种市场因子的计算功能，包括：
- 市值因子（总市值、流通市值）
- 流动性因子（换手率、成交量比率）
- 波动率因子（价格波动率、收益率波动率）
- 动量因子（价格动量、收益率动量）
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

import numpy as np

from ...clients.tushare_client import TushareClient
from ...utils.exceptions import DataNotFoundError, FactorCalculationException

logger = logging.getLogger(__name__)


class MarketFactorCalculator:
    """市场因子计算器

    提供各种市场因子的计算功能
    """

    def __init__(self, data_client: TushareClient) -> None:
        """初始化市场因子计算器

        Args:
            data_client: Tushare数据客户端
        """
        self.data_client = data_client
        self.supported_factors: dict[str, Callable[[str, str], Awaitable[float]]] = {
            "MARKET_CAP": self.calculate_market_cap,
            "FLOAT_MARKET_CAP": self.calculate_float_market_cap,
            "TURNOVER_RATE": self.calculate_turnover_rate,
            "VOLUME_RATIO": self.calculate_volume_ratio,
            "PRICE_VOLATILITY": self.calculate_price_volatility,
            "RETURN_VOLATILITY": self.calculate_return_volatility,
            "PRICE_MOMENTUM": self.calculate_price_momentum,
            "RETURN_MOMENTUM": self.calculate_return_momentum,
        }

    async def calculate_factors(
        self, stock_code: str, factors: list[str], trade_date: str
    ) -> dict[str, float]:
        """批量计算市场因子

        Args:
            stock_code: 股票代码
            factors: 要计算的因子列表
            trade_date: 交易日期

        Returns:
            因子计算结果字典

        Raises:
            FactorCalculationException: 当因子计算失败时抛出
        """
        try:
            results = {}
            for factor in factors:
                if factor not in self.supported_factors:
                    logger.warning(f"不支持的市场因子: {factor}")
                    continue

                calculator_func = self.supported_factors[factor]
                factor_value = await calculator_func(stock_code, trade_date)
                results[factor] = factor_value

            return results

        except Exception as e:
            logger.error(f"市场因子计算失败: stock_code={stock_code}, error={str(e)}")
            raise FactorCalculationException(f"市场因子计算失败: {str(e)}") from e

    async def calculate_market_cap(
        self, stock_code: str, trade_date: str
    ) -> float:
        """计算总市值

        Args:
            stock_code: 股票代码
            trade_date: 交易日期

        Returns:
            总市值（万元）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 转换日期格式为tushare格式（YYYYMMDD）
            formatted_date = trade_date.replace("-", "")
            
            # 获取每日基本面数据（包含市值信息）
            daily_basic_data = await self.data_client.get_daily_basic(
                ts_code=stock_code, trade_date=formatted_date
            )
            
            if not daily_basic_data:
                raise DataNotFoundError(f"股票每日基本面数据不存在: {stock_code}, {trade_date}")
            
            data = daily_basic_data[0]
            total_mv = data.get("total_mv", 0)  # 总市值（万元）
            
            if total_mv == 0:
                raise DataNotFoundError(f"股票总市值数据不完整: {stock_code}")
            
            return round(float(total_mv), 2)
            
        except Exception as e:
            logger.error(
                f"总市值计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_float_market_cap(
        self, stock_code: str, trade_date: str
    ) -> float:
        """计算流通市值

        Args:
            stock_code: 股票代码
            trade_date: 交易日期

        Returns:
            流通市值（万元）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 转换日期格式为tushare格式（YYYYMMDD）
            formatted_date = trade_date.replace("-", "")
            
            # 获取每日基本面数据（包含流通市值信息）
            daily_basic_data = await self.data_client.get_daily_basic(
                ts_code=stock_code, trade_date=formatted_date
            )
            
            if not daily_basic_data:
                raise DataNotFoundError(f"股票每日基本面数据不存在: {stock_code}, {trade_date}")
            
            data = daily_basic_data[0]
            circ_mv = data.get("circ_mv", 0)  # 流通市值（万元）
            
            if circ_mv == 0:
                raise DataNotFoundError(f"股票流通市值数据不完整: {stock_code}")
            
            return round(float(circ_mv), 2)
            
        except Exception as e:
            logger.error(
                f"流通市值计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_turnover_rate(self, stock_code: str, trade_date: str) -> float:
        """计算换手率

        Args:
            stock_code: 股票代码
            trade_date: 交易日期

        Returns:
            换手率（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 转换日期格式为tushare格式（YYYYMMDD）
            formatted_date = trade_date.replace("-", "")
            
            # 获取每日基本面数据（包含换手率信息）
            daily_basic_data = await self.data_client.get_daily_basic(
                ts_code=stock_code, trade_date=formatted_date
            )
            
            if not daily_basic_data:
                raise DataNotFoundError(f"股票每日基本面数据不存在: {stock_code}, {trade_date}")
            
            data = daily_basic_data[0]
            turnover_rate = data.get("turnover_rate", 0)  # 换手率（%）
            
            if turnover_rate is None:
                return 0.0
            
            return round(float(turnover_rate), 4)
            
        except Exception as e:
            logger.error(f"换手率计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}")
            raise

    async def calculate_volume_ratio(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算成交量比率

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            成交量比率

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史日线数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)
            
            # 转换日期格式为tushare格式（YYYYMMDD）
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")

            quotes = await self.data_client.get_daily_data(
                ts_code=stock_code, start_date=start_date_str, end_date=end_date_str
            )

            if not quotes or len(quotes) < period + 1:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period + 1}天，实际{len(quotes) if quotes else 0}天"
                )

            # 获取当日成交量和历史平均成交量
            current_volume = quotes[-1].get("vol", 0)  # 当日成交量（tushare中成交量字段为vol）
            historical_volumes = [q.get("vol", 0) for q in quotes[-period-1:-1]]  # 前period天的成交量

            if not historical_volumes:
                raise DataNotFoundError(f"历史成交量数据不足: {stock_code}")

            avg_volume = np.mean(historical_volumes)
            if avg_volume == 0:
                return 0.0

            # 成交量比率 = 当日成交量 / 历史平均成交量
            volume_ratio = current_volume / avg_volume
            return round(float(volume_ratio), 4)

        except Exception as e:
            logger.error(
                f"成交量比率计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_price_volatility(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算价格波动率

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            价格波动率（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史日线数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)
            
            # 转换日期格式为tushare格式（YYYYMMDD）
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")

            quotes = await self.data_client.get_daily_data(
                ts_code=stock_code, start_date=start_date_str, end_date=end_date_str
            )

            if not quotes or len(quotes) < period:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period}天，实际{len(quotes) if quotes else 0}天"
                )

            # 计算收盘价的标准差
            close_prices = [q.get("close", 0) for q in quotes[-period:]]
            if not close_prices or all(p == 0 for p in close_prices):
                raise DataNotFoundError(f"收盘价数据无效: {stock_code}")

            # 价格波动率 = 收盘价标准差 / 平均收盘价 * 100%
            price_std = np.std(close_prices)
            price_mean = np.mean(close_prices)

            if price_mean == 0:
                return 0.0

            price_volatility = (price_std / price_mean) * 100
            return round(float(price_volatility), 4)

        except Exception as e:
            logger.error(
                f"价格波动率计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_return_volatility(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算收益率波动率

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            收益率波动率（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史日线数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)
            
            # 转换日期格式为tushare格式（YYYYMMDD）
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")

            quotes = await self.data_client.get_daily_data(
                ts_code=stock_code, start_date=start_date_str, end_date=end_date_str
            )

            if not quotes or len(quotes) < period + 1:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period + 1}天，实际{len(quotes) if quotes else 0}天"
                )

            # 计算日收益率
            close_prices = [q.get("close", 0) for q in quotes[-(period + 1):]]
            if len(close_prices) < 2 or any(p == 0 for p in close_prices):
                raise DataNotFoundError(f"收盘价数据无效: {stock_code}")

            returns = []
            for i in range(1, len(close_prices)):
                daily_return = (close_prices[i] - close_prices[i-1]) / close_prices[i-1] * 100
                returns.append(daily_return)

            if not returns:
                return 0.0

            # 收益率波动率 = 日收益率的标准差
            return_volatility = np.std(returns)
            return round(float(return_volatility), 4)

        except Exception as e:
            logger.error(
                f"收益率波动率计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_price_momentum(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算价格动量

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            价格动量（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史日线数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)
            
            # 转换日期格式为tushare格式（YYYYMMDD）
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")

            quotes = await self.data_client.get_daily_data(
                ts_code=stock_code, start_date=start_date_str, end_date=end_date_str
            )

            if not quotes or len(quotes) < period + 1:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period + 1}天，实际{len(quotes) if quotes else 0}天"
                )

            # 计算价格动量 = (当前价格 - period天前价格) / period天前价格 * 100%
            current_price = quotes[-1].get("close", 0)
            past_price = quotes[-(period + 1)].get("close", 0)

            if current_price == 0 or past_price == 0:
                raise DataNotFoundError(f"价格数据无效: {stock_code}")

            price_momentum = (current_price - past_price) / past_price * 100
            return round(float(price_momentum), 4)

        except Exception as e:
            logger.error(
                f"价格动量计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_return_momentum(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算收益率动量

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            收益率动量（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史日线数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)
            
            # 转换日期格式为tushare格式（YYYYMMDD）
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")

            quotes = await self.data_client.get_daily_data(
                ts_code=stock_code, start_date=start_date_str, end_date=end_date_str
            )

            if not quotes or len(quotes) < period + 1:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period + 1}天，实际{len(quotes) if quotes else 0}天"
                )

            # 计算日收益率
            close_prices = [q.get("close", 0) for q in quotes[-(period + 1):]]
            if len(close_prices) < 2 or any(p == 0 for p in close_prices):
                raise DataNotFoundError(f"收盘价数据无效: {stock_code}")

            returns = []
            for i in range(1, len(close_prices)):
                daily_return = (close_prices[i] - close_prices[i-1]) / close_prices[i-1] * 100
                returns.append(daily_return)

            if not returns:
                return 0.0

            # 收益率动量 = 累计收益率
            return_momentum = sum(returns)
            return round(float(return_momentum), 4)

        except Exception as e:
            logger.error(
                f"收益率动量计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise
