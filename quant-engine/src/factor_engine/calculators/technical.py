"""技术因子计算器模块

实现各种技术指标的计算，包括：
- MA (移动平均线)
- RSI (相对强弱指数)
- MACD (指数平滑移动平均线)
- 布林带 (Bollinger Bands)
"""

from collections.abc import Callable
from typing import Any

import pandas as pd


class TechnicalFactorCalculator:
    """技术因子计算器

    提供各种技术指标的计算功能
    """

    def __init__(self) -> None:
        """初始化技术因子计算器"""
        self.supported_factors: dict[str, Callable[[pd.DataFrame, Any], Any]] = {
            "MA": self.calculate_ma,
            "RSI": self.calculate_rsi,
            "MACD": self.calculate_macd,
            "BOLL": self.calculate_bollinger_bands,
        }

    def calculate_factors(
        self,
        price_data: pd.DataFrame,
        factors: list[str],
        periods: dict[str, int] | None = None,
    ) -> dict[str, float | dict[str, float]]:
        """计算指定的技术因子

        Args:
            price_data: 价格数据，包含open, high, low, close, volume列
            factors: 要计算的因子列表
            periods: 各因子的计算周期，如{'MA': 20, 'RSI': 14}

        Returns:
            计算结果字典
        """
        if price_data.empty:
            raise ValueError("价格数据不能为空")

        # 默认周期设置
        default_periods = {
            "MA": 20,
            "RSI": 14,
            "MACD": {"fast": 12, "slow": 26, "signal": 9},
            "BOLL": 20,
        }

        if periods is None:
            periods = {}

        results = {}

        for factor in factors:
            if factor not in self.supported_factors:
                raise ValueError(f"不支持的技术因子: {factor}")

            # 获取计算周期
            period = periods.get(factor, default_periods[factor])

            try:
                # 调用对应的计算函数
                result = self.supported_factors[factor](price_data, period)
                results[factor] = result
            except Exception as e:
                raise ValueError(f"计算{factor}因子时出错: {str(e)}") from e

        return results

    def calculate_ma(self, price_data: pd.DataFrame, period: int = 20) -> float:
        """计算移动平均线

        Args:
            price_data: 价格数据
            period: 计算周期

        Returns:
            最新的移动平均值
        """
        if len(price_data) < period:
            raise ValueError(f"数据长度不足，需要至少{period}个数据点")

        close_prices = price_data["close"].astype(float)
        ma_values = close_prices.rolling(window=period).mean()

        # 返回最新值
        latest_ma = ma_values.iloc[-1]
        return float(latest_ma) if not pd.isna(latest_ma) else 0.0

    def calculate_rsi(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """计算相对强弱指数

        Args:
            price_data: 价格数据
            period: 计算周期

        Returns:
            最新的RSI值
        """
        if len(price_data) < period + 1:
            raise ValueError(f"数据长度不足，需要至少{period + 1}个数据点")

        close_prices = price_data["close"].astype(float)

        # 计算价格变化
        delta = close_prices.diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均收益和平均损失
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # 返回最新值
        latest_rsi = rsi.iloc[-1]
        return float(latest_rsi) if not pd.isna(latest_rsi) else 50.0

    def calculate_macd(
        self, price_data: pd.DataFrame, periods: dict[str, int] | None = None
    ) -> dict[str, float]:
        """计算MACD指标

        Args:
            price_data: 价格数据
            periods: MACD参数，包含fast, slow, signal

        Returns:
            包含MACD, Signal, Histogram的字典
        """
        if periods is None:
            periods = {"fast": 12, "slow": 26, "signal": 9}

        fast_period = periods["fast"]
        slow_period = periods["slow"]
        signal_period = periods["signal"]

        if len(price_data) < slow_period + signal_period:
            raise ValueError(
                f"数据长度不足，需要至少{slow_period + signal_period}个数据点"
            )

        close_prices = price_data["close"].astype(float)

        # 计算快速和慢速EMA
        ema_fast = close_prices.ewm(span=fast_period).mean()
        ema_slow = close_prices.ewm(span=slow_period).mean()

        # 计算MACD线
        macd_line = ema_fast - ema_slow

        # 计算信号线
        signal_line = macd_line.ewm(span=signal_period).mean()

        # 计算柱状图
        histogram = macd_line - signal_line

        return {
            "MACD": float(macd_line.iloc[-1])
            if not pd.isna(macd_line.iloc[-1])
            else 0.0,
            "Signal": float(signal_line.iloc[-1])
            if not pd.isna(signal_line.iloc[-1])
            else 0.0,
            "Histogram": float(histogram.iloc[-1])
            if not pd.isna(histogram.iloc[-1])
            else 0.0,
        }

    def calculate_bollinger_bands(
        self, price_data: pd.DataFrame, period: int = 20, std_dev: float = 2.0
    ) -> dict[str, float]:
        """计算布林带指标

        Args:
            price_data: 价格数据
            period: 计算周期
            std_dev: 标准差倍数

        Returns:
            包含Upper, Middle, Lower的字典
        """
        if len(price_data) < period:
            raise ValueError(f"数据长度不足，需要至少{period}个数据点")

        close_prices = price_data["close"].astype(float)

        # 计算中轨（移动平均线）
        middle_band = close_prices.rolling(window=period).mean()

        # 计算标准差
        std = close_prices.rolling(window=period).std()

        # 计算上轨和下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return {
            "Upper": float(upper_band.iloc[-1])
            if not pd.isna(upper_band.iloc[-1])
            else 0.0,
            "Middle": float(middle_band.iloc[-1])
            if not pd.isna(middle_band.iloc[-1])
            else 0.0,
            "Lower": float(lower_band.iloc[-1])
            if not pd.isna(lower_band.iloc[-1])
            else 0.0,
        }

    def get_supported_factors(self) -> list[str]:
        """获取支持的技术因子列表

        Returns:
            支持的因子名称列表
        """
        return list(self.supported_factors.keys())

    def validate_price_data(self, price_data: pd.DataFrame) -> bool:
        """验证价格数据格式

        Args:
            price_data: 价格数据

        Returns:
            验证结果
        """
        required_columns = ["open", "high", "low", "close", "volume"]

        if price_data.empty:
            return False

        missing_columns = [
            col for col in required_columns if col not in price_data.columns
        ]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")

        return True
