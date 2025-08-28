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

from ...clients.data_collector_client import DataCollectorClient
from ...utils.exceptions import DataNotFoundError, FactorCalculationException

logger = logging.getLogger(__name__)


class MarketFactorCalculator:
    """市场因子计算器

    提供各种市场因子的计算功能
    """

    def __init__(self, data_client: DataCollectorClient) -> None:
        """初始化市场因子计算器

        Args:
            data_client: 数据采集客户端
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
            # 获取股票数据（包含基础信息和行情数据）
            stock_data = await self.data_client.get_stock_data(
                stock_code, trade_date, trade_date
            )
            if not stock_data:
                raise DataNotFoundError(f"股票数据不存在: {stock_code}, {trade_date}")

            # 从返回数据中提取当日数据
            if isinstance(stock_data, list) and len(stock_data) > 0:
                quote_data = stock_data[0]
            else:
                raise DataNotFoundError(f"股票行情数据不存在: {stock_code}, {trade_date}")

            # 计算总市值 = 收盘价 * 总股本
            close_price = quote_data.get("close")
            total_share = quote_data.get("total_share")  # 总股本（万股）

            if close_price is None or total_share is None:
                raise DataNotFoundError(f"缺少计算市值的必要数据: {stock_code}")

            # 确保类型转换为float
            close_price_float = float(close_price)
            total_share_float = float(total_share)
            market_cap = close_price_float * total_share_float  # 万元
            return round(market_cap, 2)

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
            # 获取股票数据（包含基础信息和行情数据）
            stock_data = await self.data_client.get_stock_data(
                stock_code, trade_date, trade_date
            )
            if not stock_data:
                raise DataNotFoundError(f"股票数据不存在: {stock_code}, {trade_date}")

            # 从返回数据中提取当日数据
            if isinstance(stock_data, list) and len(stock_data) > 0:
                quote_data = stock_data[0]
            else:
                raise DataNotFoundError(f"股票行情数据不存在: {stock_code}, {trade_date}")
            if not quote_data:
                raise DataNotFoundError(
                    f"股票行情数据不存在: {stock_code}, {trade_date}"
                )

            # 计算流通市值 = 收盘价 * 流通股本
            close_price = quote_data.get("close")
            float_share = quote_data.get("float_share")  # 流通股本（万股）

            if close_price is None or float_share is None:
                raise DataNotFoundError(f"缺少计算流通市值的必要数据: {stock_code}")

            # 确保类型转换为float
            close_price_float = float(close_price)
            float_share_float = float(float_share)
            float_market_cap = close_price_float * float_share_float  # 万元
            return round(float_market_cap, 2)

        except Exception as e:
            logger.error(
                f"流通市值计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
            raise

    async def calculate_turnover_rate(
        self, stock_code: str, trade_date: str, period: int = 20
    ) -> float:
        """计算换手率

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            period: 计算周期（天数）

        Returns:
            平均换手率（%）

        Raises:
            DataNotFoundError: 当数据不存在时抛出
        """
        try:
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)  # 多取一些数据以防节假日

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
            )

            if not quotes or len(quotes) < period:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period}天，实际{len(quotes) if quotes else 0}天"
                )

            # 计算每日换手率
            if not quotes or len(quotes) == 0:
                raise DataNotFoundError(f"历史行情数据不足: {stock_code}")

            # 从最新数据中获取流通股本
            float_share = quotes[-1].get("float_share")  # 流通股本（万股）
            if float_share is None:
                raise DataNotFoundError(f"缺少流通股本数据: {stock_code}")

            # 如果流通股本为0，返回0
            if float_share == 0:
                return 0.0

            turnover_rates = []
            for quote in quotes[-period:]:  # 取最近period天的数据
                volume = quote.get("volume", 0)  # 成交量（手）
                # 换手率 = 成交量（股） / 流通股本（股） * 100%
                # 1手 = 100股，流通股本单位是万股
                daily_turnover = (volume * 100) / (float_share * 10000) * 100
                turnover_rates.append(daily_turnover)

            # 计算平均换手率
            avg_turnover_rate = np.mean(turnover_rates)
            return round(float(avg_turnover_rate), 4)

        except Exception as e:
            logger.error(
                f"换手率计算失败: stock_code={stock_code}, trade_date={trade_date}, error={str(e)}"
            )
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
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
            )

            if not quotes or len(quotes) < period + 1:
                raise DataNotFoundError(
                    f"历史行情数据不足: {stock_code}, 需要{period + 1}天，实际{len(quotes) if quotes else 0}天"
                )

            # 获取当日成交量和历史平均成交量
            current_volume = quotes[-1].get("volume", 0)  # 当日成交量
            historical_volumes = [q.get("volume", 0) for q in quotes[-period-1:-1]]  # 前period天的成交量

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
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
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
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
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
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
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
            # 获取历史行情数据
            end_date = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=period + 10)

            quotes = await self.data_client.get_stock_data(
                stock_code, start_date.strftime("%Y-%m-%d"), trade_date
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
