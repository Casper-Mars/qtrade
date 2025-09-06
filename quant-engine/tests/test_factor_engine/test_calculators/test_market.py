"""市场因子计算器测试模块

测试市场因子计算器的各种功能
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import numpy as np
import pytest

from src.clients.data_collector_client import DataCollectorClient
from src.factor_engine.calculators.market import MarketFactorCalculator
from src.utils.exceptions import DataNotFoundError


class TestMarketFactorCalculator:
    """市场因子计算器测试类"""

    @pytest.fixture
    def mock_data_client(self):
        """创建模拟数据客户端"""
        client = AsyncMock(spec=DataCollectorClient)

        # 模拟当日行情数据（包含股本信息）
        current_data = {
            "close": 10.0,
            "volume": 50000000,  # 5000万成交量
            "amount": 500000000,  # 5亿成交额
            "total_share": 1000000,  # 100万万股（10亿股）
            "float_share": 800000,   # 80万万股（8亿股）
        }

        # 模拟历史数据
        historical_data = []
        for i in range(30):
            price = 10.0 + np.random.normal(0, 0.5)  # 基准价格10元，波动0.5元
            historical_data.append({
                "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "close": max(price, 1.0),  # 确保价格为正
                "volume": np.random.randint(10000000, 100000000),
                "amount": np.random.randint(100000000, 1000000000),
            })

        # 为不同的调用配置不同的返回值
        def mock_get_stock_data(stock_code, start_date, end_date):
            # 如果是单日查询，返回当日数据
            if start_date == end_date:
                return [current_data]
            # 如果是历史数据查询，返回历史数据
            else:
                return historical_data

        client.get_stock_data.side_effect = mock_get_stock_data

        return client

    @pytest.fixture
    def calculator(self, mock_data_client):
        """创建市场因子计算器实例"""
        return MarketFactorCalculator(mock_data_client)

    @pytest.mark.asyncio
    async def test_calculate_factors_single_factor(self, calculator):
        """测试单个因子计算"""
        result = await calculator.calculate_factors("000001", ["MARKET_CAP"], "2024-01-15")

        assert "MARKET_CAP" in result
        assert isinstance(result["MARKET_CAP"], float)
        assert result["MARKET_CAP"] > 0

    @pytest.mark.asyncio
    async def test_calculate_factors_multiple_factors(self, calculator, mock_data_client):
        """测试多个因子计算"""
        # 模拟完整的股票数据
        mock_data_client.get_stock_data.return_value = [
            {
                "close": 10.0,
                "total_share": 1000000,  # 万股
                "float_share": 800000,   # 万股
                "volume": 50000,         # 手
            }
        ]

        factors = ["MARKET_CAP", "FLOAT_MARKET_CAP"]
        result = await calculator.calculate_factors("000001", factors, "2024-01-15")

        for factor in factors:
            assert factor in result
            assert isinstance(result[factor], float)

    @pytest.mark.asyncio
    async def test_calculate_factors_unsupported_factor(self, calculator):
        """测试不支持的因子"""
        # 不支持的因子会被跳过，返回空字典
        result = await calculator.calculate_factors("000001", ["UNSUPPORTED_FACTOR"], "2024-01-15")
        assert result == {}

    @pytest.mark.asyncio
    async def test_calculate_market_cap_normal(self, calculator):
        """测试正常情况下的总市值计算"""
        result = await calculator.calculate_market_cap("000001", "2024-01-15")

        # 总市值 = 收盘价 * 总股本 = 10.0 * 1000000 = 10000000万元
        expected_market_cap = 10.0 * 1000000  # 价格 * 总股本(万股) = 1000万万元
        assert result == expected_market_cap
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculate_float_market_cap_normal(self, calculator):
        """测试正常情况下的流通市值计算"""
        result = await calculator.calculate_float_market_cap("000001", "2024-01-15")

        # 流通市值 = 流通股本 × 股价 = 8亿 × 10元 = 80亿
        expected_float_market_cap = 10.0 * 800000  # 价格 * 流通股本(万股) = 800万万元
        assert result == expected_float_market_cap
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculate_turnover_rate_normal(self, calculator, mock_data_client):
        """测试正常情况下的换手率计算"""
        # 模拟历史数据
        historical_data = []
        for i in range(20):
            historical_data.append({
                "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "volume": 50000 + i * 1000,  # 递增的成交量
                "float_share": 800000,  # 流通股本（万股）
            })

        # 为历史数据查询设置不同的返回值
        def mock_get_data(stock_code, start_date, end_date):
            if start_date == end_date:
                return [{
                    "close": 10.0,
                    "volume": 50000,  # 5万手
                    "float_share": 800000,  # 80万万股（8亿股）
                }]
            else:
                return historical_data

        mock_data_client.get_stock_data.side_effect = mock_get_data

        result = await calculator.calculate_turnover_rate("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculate_volume_ratio_normal(self, calculator):
        """测试正常情况下的成交量比率计算"""
        result = await calculator.calculate_volume_ratio("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    @pytest.mark.asyncio
    async def test_calculate_price_volatility_normal(self, calculator):
        """测试正常情况下的价格波动率计算"""
        result = await calculator.calculate_price_volatility("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_calculate_return_volatility_normal(self, calculator):
        """测试正常情况下的收益率波动率计算"""
        result = await calculator.calculate_return_volatility("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_calculate_price_momentum_normal(self, calculator):
        """测试正常情况下的价格动量计算"""
        result = await calculator.calculate_price_momentum("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_return_momentum_normal(self, calculator):
        """测试正常情况下的收益率动量计算"""
        result = await calculator.calculate_return_momentum("000001", "2024-01-15")

        assert result is not None
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_edge_case_zero_shares(self, mock_data_client, calculator):
        """测试股本为零的边界情况"""
        # 修改模拟数据
        def mock_zero_shares(stock_code, start_date, end_date):
            return [{
                "close": 10.0,
                "volume": 50000000,
                "amount": 500000000,
                "total_share": 0,  # 总股本为0
                "float_share": 0,  # 流通股本为0
            }]

        mock_data_client.get_stock_data.side_effect = mock_zero_shares

        # 零股本会计算出0.0的市值 (10.0 * 0 = 0.0)
        result = await calculator.calculate_market_cap("000001", "2024-01-15")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_edge_case_zero_volume(self, mock_data_client, calculator):
        """测试成交量为零的边界情况"""
        # 模拟20天的历史数据，成交量都为零
        historical_data = []
        for i in range(20):
            historical_data.append({
                "trade_date": (datetime.now() - timedelta(days=19-i)).strftime("%Y-%m-%d"),
                "volume": 0,  # 成交量为0
                "float_share": 800000,  # 流通股本（万股）
            })

        def mock_get_data(stock_code, start_date, end_date):
            if start_date == end_date:
                return [{
                    "close": 10.0,
                    "volume": 0,  # 当日成交量为0
                    "float_share": 800000,  # 80万万股（8亿股）
                }]
            else:
                return historical_data

        mock_data_client.get_stock_data.side_effect = mock_get_data

        turnover_rate = await calculator.calculate_turnover_rate("000001", "2024-01-15")
        assert turnover_rate == 0.0

    @pytest.mark.asyncio
    async def test_edge_case_insufficient_historical_data(self, calculator, mock_data_client):
        """测试历史数据不足的边界情况"""
        # 模拟只有少量历史数据
        limited_data = []
        for i in range(5):  # 只有5天数据，少于默认的20天
            limited_data.append({
                "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "close": 10.0 + i * 0.1,
                "volume": 50000000,
                "amount": 500000000,
            })

        mock_data_client.get_stock_data.side_effect = lambda stock_code, start_date, end_date: limited_data

        with pytest.raises((ValueError, RuntimeError)):
            await calculator.calculate_price_volatility("000001", "2024-01-15")

    @pytest.mark.asyncio
    async def test_edge_case_no_historical_data(self, calculator, mock_data_client):
        """测试无历史数据的边界情况"""
        mock_data_client.get_stock_data.side_effect = lambda stock_code, start_date, end_date: []

        with pytest.raises((ValueError, RuntimeError)):
            await calculator.calculate_price_volatility("000001", "2024-01-15")

    @pytest.mark.asyncio
    async def test_edge_case_extreme_volatility(self, calculator, mock_data_client):
        """测试极端波动率的边界情况"""
        # 模拟极端波动的数据
        extreme_data = []
        for i in range(20):
            price = 10.0 if i % 2 == 0 else 20.0  # 价格在10和20之间剧烈波动
            extreme_data.append({
                "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "close": price,
                "volume": 50000000,
                "amount": 500000000,
            })

        mock_data_client.get_stock_data.side_effect = lambda stock_code, start_date, end_date: extreme_data

        result = await calculator.calculate_price_volatility("000001", "2024-01-15")
        assert result > 0  # 应该有较高的波动率
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_edge_case_constant_prices(self, mock_data_client, calculator):
        """测试价格恒定的边界情况"""
        # 模拟价格恒定的历史数据
        constant_data = []
        for i in range(21):  # 21天数据
            constant_data.append({
                "trade_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "close": 10.0,  # 价格恒定
                "volume": 50000000,
                "amount": 500000000,
            })

        mock_data_client.get_stock_data.return_value = constant_data

        volatility = await calculator.calculate_price_volatility("000001", "2024-01-15")
        # 价格恒定时，波动率应该接近0，但可能不完全为0
        assert volatility >= 0

        momentum = await calculator.calculate_return_momentum("000001", "2024-01-15")
        # 价格恒定时，动量应该接近0，但可能不完全为0
        assert isinstance(momentum, float)

    @pytest.mark.asyncio
    async def test_edge_case_missing_data_fields(self, calculator, mock_data_client):
        """测试数据字段缺失的边界情况"""
        # 模拟缺失字段的数据 - close 和 total_share 为 None
        def mock_missing_data(stock_code, start_date, end_date):
            return [{
                "close": None,
                "total_share": None,
            }]

        mock_data_client.get_stock_data.side_effect = mock_missing_data

        with pytest.raises(DataNotFoundError):
            await calculator.calculate_market_cap("000001", "2024-01-15")
