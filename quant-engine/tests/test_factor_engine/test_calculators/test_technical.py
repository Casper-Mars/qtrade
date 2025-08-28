"""技术因子计算器测试

测试技术因子计算器的各种技术指标计算方法。
"""

import pandas as pd
import pytest

from src.factor_engine.calculators.technical import TechnicalFactorCalculator


class TestTechnicalFactorCalculator:
    """技术因子计算器测试类"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return TechnicalFactorCalculator()

    @pytest.fixture
    def sample_price_data(self):
        """创建样本价格数据

        构造50天的股票价格数据，包含趋势和波动（满足MACD计算需求）
        """
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

        # 构造有趋势的价格数据
        base_price = 100.0
        prices = []

        for i in range(50):
            # 基础趋势：缓慢上涨
            trend = base_price + i * 0.3
            # 添加随机波动
            volatility = (-1) ** i * (i % 3) * 0.2
            price = trend + volatility
            prices.append(price)

        # 确保价格合理性
        opens = [p * 0.995 for p in prices]  # 开盘价略低于收盘价
        highs = [p * 1.02 for p in prices]   # 最高价
        lows = [p * 0.98 for p in prices]    # 最低价
        volumes = [1000000 + i * 10000 for i in range(50)]  # 成交量

        return pd.DataFrame({
            "date": dates,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes
        })

    @pytest.fixture
    def minimal_price_data(self):
        """创建最小价格数据（用于测试边界条件）"""
        return pd.DataFrame({
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000000, 1100000, 1200000]
        })

    def test_get_supported_factors(self, calculator):
        """测试获取支持的因子列表"""
        factors = calculator.get_supported_factors()
        expected_factors = ["MA", "RSI", "MACD", "BOLL"]

        assert isinstance(factors, list)
        assert len(factors) == 4
        for factor in expected_factors:
            assert factor in factors

    def test_validate_price_data_valid(self, calculator, sample_price_data):
        """测试有效价格数据验证"""
        result = calculator.validate_price_data(sample_price_data)
        assert result is True

    def test_validate_price_data_empty(self, calculator):
        """测试空数据验证"""
        empty_data = pd.DataFrame()
        result = calculator.validate_price_data(empty_data)
        assert result is False

    def test_validate_price_data_missing_columns(self, calculator):
        """测试缺少必要列的数据验证"""
        incomplete_data = pd.DataFrame({
            "open": [100.0],
            "close": [101.0]
            # 缺少 high, low, volume 列
        })

        with pytest.raises(ValueError, match="缺少必要的列"):
            calculator.validate_price_data(incomplete_data)

    def test_calculate_ma_normal(self, calculator, sample_price_data):
        """测试正常MA计算"""
        result = calculator.calculate_ma(sample_price_data, period=5)

        assert isinstance(result, float)
        assert result > 0

        # 手动验证最后5天的平均值
        last_5_closes = sample_price_data["close"].tail(5)
        expected_ma = last_5_closes.mean()
        assert abs(result - expected_ma) < 0.001

    def test_calculate_ma_insufficient_data(self, calculator, minimal_price_data):
        """测试MA计算数据不足的情况"""
        with pytest.raises(ValueError, match="数据长度不足"):
            calculator.calculate_ma(minimal_price_data, period=5)

    def test_calculate_ma_default_period(self, calculator, sample_price_data):
        """测试MA默认周期计算"""
        result = calculator.calculate_ma(sample_price_data)

        # 默认周期是20天
        last_20_closes = sample_price_data["close"].tail(20)
        expected_ma = last_20_closes.mean()
        assert abs(result - expected_ma) < 0.001

    def test_calculate_rsi_normal(self, calculator, sample_price_data):
        """测试正常RSI计算"""
        result = calculator.calculate_rsi(sample_price_data, period=14)

        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_calculate_rsi_insufficient_data(self, calculator, minimal_price_data):
        """测试RSI计算数据不足的情况"""
        with pytest.raises(ValueError, match="数据长度不足"):
            calculator.calculate_rsi(minimal_price_data, period=14)

    def test_calculate_rsi_trending_up(self, calculator):
        """测试上涨趋势的RSI计算"""
        # 构造持续上涨的数据
        uptrend_data = pd.DataFrame({
            "open": [100 + i for i in range(20)],
            "high": [102 + i for i in range(20)],
            "low": [99 + i for i in range(20)],
            "close": [101 + i for i in range(20)],
            "volume": [1000000] * 20
        })

        result = calculator.calculate_rsi(uptrend_data, period=14)

        # 持续上涨应该产生较高的RSI值
        assert result > 50

    def test_calculate_rsi_trending_down(self, calculator):
        """测试下跌趋势的RSI计算"""
        # 构造持续下跌的数据
        downtrend_data = pd.DataFrame({
            "open": [120 - i for i in range(20)],
            "high": [122 - i for i in range(20)],
            "low": [119 - i for i in range(20)],
            "close": [121 - i for i in range(20)],
            "volume": [1000000] * 20
        })

        result = calculator.calculate_rsi(downtrend_data, period=14)

        # 持续下跌应该产生较低的RSI值
        assert result < 50

    def test_calculate_macd_normal(self, calculator, sample_price_data):
        """测试正常MACD计算"""
        result = calculator.calculate_macd(sample_price_data)

        assert isinstance(result, dict)
        assert "MACD" in result
        assert "Signal" in result
        assert "Histogram" in result

        # 验证所有值都是数字
        for _key, value in result.items():
            assert isinstance(value, float)

    def test_calculate_macd_custom_periods(self, calculator, sample_price_data):
        """测试自定义周期的MACD计算"""
        custom_periods = {"fast": 8, "slow": 21, "signal": 5}
        result = calculator.calculate_macd(sample_price_data, custom_periods)

        assert isinstance(result, dict)
        assert len(result) == 3

    def test_calculate_macd_insufficient_data(self, calculator, minimal_price_data):
        """测试MACD计算数据不足的情况"""
        with pytest.raises(ValueError, match="数据长度不足"):
            calculator.calculate_macd(minimal_price_data)

    def test_calculate_bollinger_bands_normal(self, calculator, sample_price_data):
        """测试正常布林带计算"""
        result = calculator.calculate_bollinger_bands(sample_price_data, period=20)

        assert isinstance(result, dict)
        assert "Upper" in result
        assert "Middle" in result
        assert "Lower" in result

        # 验证布林带的逻辑关系
        assert result["Upper"] > result["Middle"]
        assert result["Middle"] > result["Lower"]

        # 验证中轨等于移动平均线
        expected_middle = sample_price_data["close"].tail(20).mean()
        assert abs(result["Middle"] - expected_middle) < 0.001

    def test_calculate_bollinger_bands_custom_std(self, calculator, sample_price_data):
        """测试自定义标准差倍数的布林带计算"""
        result_2std = calculator.calculate_bollinger_bands(sample_price_data, period=20, std_dev=2.0)
        result_1std = calculator.calculate_bollinger_bands(sample_price_data, period=20, std_dev=1.0)

        # 2倍标准差的带宽应该比1倍标准差的更宽
        width_2std = result_2std["Upper"] - result_2std["Lower"]
        width_1std = result_1std["Upper"] - result_1std["Lower"]
        assert width_2std > width_1std

    def test_calculate_bollinger_bands_insufficient_data(self, calculator, minimal_price_data):
        """测试布林带计算数据不足的情况"""
        with pytest.raises(ValueError, match="数据长度不足"):
            calculator.calculate_bollinger_bands(minimal_price_data, period=20)

    def test_calculate_factors_single(self, calculator, sample_price_data):
        """测试计算单个因子"""
        result = calculator.calculate_factors(sample_price_data, ["MA"])

        assert isinstance(result, dict)
        assert "MA" in result
        assert isinstance(result["MA"], float)

    def test_calculate_factors_multiple(self, calculator, sample_price_data):
        """测试计算多个因子"""
        factors = ["MA", "RSI", "MACD", "BOLL"]
        result = calculator.calculate_factors(sample_price_data, factors)

        assert isinstance(result, dict)
        assert len(result) == 4

        # 验证每个因子都被计算
        for factor in factors:
            assert factor in result

        # 验证数据类型
        assert isinstance(result["MA"], float)
        assert isinstance(result["RSI"], float)
        assert isinstance(result["MACD"], dict)
        assert isinstance(result["BOLL"], dict)

    def test_calculate_factors_custom_periods(self, calculator, sample_price_data):
        """测试使用自定义周期计算因子"""
        factors = ["MA", "RSI"]
        periods = {"MA": 10, "RSI": 7}

        result = calculator.calculate_factors(sample_price_data, factors, periods)

        assert "MA" in result
        assert "RSI" in result

        # 验证使用了自定义周期
        expected_ma = sample_price_data["close"].tail(10).mean()
        assert abs(result["MA"] - expected_ma) < 0.001

    def test_calculate_factors_empty_data(self, calculator):
        """测试空数据计算因子"""
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="价格数据不能为空"):
            calculator.calculate_factors(empty_data, ["MA"])

    def test_calculate_factors_unsupported_factor(self, calculator, sample_price_data):
        """测试不支持的因子"""
        with pytest.raises(ValueError, match="不支持的技术因子"):
            calculator.calculate_factors(sample_price_data, ["UNKNOWN_FACTOR"])

    def test_calculate_factors_calculation_error(self, calculator):
        """测试计算过程中的错误处理"""
        # 构造会导致计算错误的数据（数据不足）
        insufficient_data = pd.DataFrame({
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000000]
        })

        with pytest.raises(ValueError, match="计算.*因子时出错"):
            calculator.calculate_factors(insufficient_data, ["MA"], {"MA": 20})

    def test_edge_case_all_same_prices(self, calculator):
        """测试所有价格相同的边界情况"""
        same_price_data = pd.DataFrame({
            "open": [100.0] * 50,
            "high": [100.0] * 50,
            "low": [100.0] * 50,
            "close": [100.0] * 50,
            "volume": [1000000] * 50
        })

        # MA应该等于价格
        ma_result = calculator.calculate_ma(same_price_data, period=20)
        assert abs(ma_result - 100.0) < 0.001

        # RSI应该接近50（没有涨跌）
        rsi_result = calculator.calculate_rsi(same_price_data, period=14)
        assert abs(rsi_result - 50.0) < 0.001

        # 布林带的上下轨应该等于中轨（没有波动）
        boll_result = calculator.calculate_bollinger_bands(same_price_data, period=20)
        assert abs(boll_result["Upper"] - boll_result["Middle"]) < 0.001
        assert abs(boll_result["Lower"] - boll_result["Middle"]) < 0.001

    def test_edge_case_extreme_volatility(self, calculator):
        """测试极端波动的边界情况"""
        # 构造极端波动的数据（50个数据点以满足MACD需求）
        volatile_prices = []
        for i in range(50):
            if i % 2 == 0:
                volatile_prices.append(50.0)  # 低价
            else:
                volatile_prices.append(150.0)  # 高价

        volatile_data = pd.DataFrame({
            "open": volatile_prices,
            "high": [p * 1.01 for p in volatile_prices],
            "low": [p * 0.99 for p in volatile_prices],
            "close": volatile_prices,
            "volume": [1000000] * 50
        })

        # 所有指标都应该能正常计算
        result = calculator.calculate_factors(volatile_data, ["MA", "RSI", "MACD", "BOLL"])

        assert "MA" in result
        assert "RSI" in result
        assert "MACD" in result
        assert "BOLL" in result

        # 布林带应该有较大的带宽
        boll_width = result["BOLL"]["Upper"] - result["BOLL"]["Lower"]
        assert boll_width > 50  # 极端波动应该产生较宽的布林带
