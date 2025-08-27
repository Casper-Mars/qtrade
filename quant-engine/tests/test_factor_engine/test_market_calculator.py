"""市场因子计算器测试

测试市场因子计算器的各种计算方法。
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from src.factor_engine.calculators.market import MarketFactorCalculator
from src.clients.data_collector_client import DataCollectorClient
from src.utils.exceptions import DataNotFoundError


class TestMarketFactorCalculator:
    """市场因子计算器测试类"""

    @pytest.fixture
    def mock_data_client(self):
        """模拟数据客户端"""
        client = MagicMock(spec=DataCollectorClient)
        return client

    @pytest.fixture
    def calculator(self, mock_data_client):
        """创建计算器实例"""
        return MarketFactorCalculator(mock_data_client)

    @pytest.mark.asyncio
    async def test_calculate_total_market_cap(self, calculator, mock_data_client):
        """测试总市值计算"""
        # 模拟股票数据
        mock_data_client.get_stock_data.return_value = [
            {
                "trade_date": "2024-01-15",
                "close": 10.50,
                "volume": 50000000,
                "amount": 525000000,
                "total_share": 1000000000,  # 10亿股
                "float_share": 800000000,   # 8亿流通股
            }
        ]

        result = await calculator.calculate_market_cap("000001.SZ", "2024-01-15")
        
        # 总市值 = 总股本 * 收盘价 = 1000000000 * 10.50 = 10500000000
        assert result == 10500000000.0

    @pytest.mark.asyncio
    async def test_calculate_tradable_market_cap(self, calculator, mock_data_client):
        """测试流通市值计算"""
        # 模拟股票数据
        mock_data_client.get_stock_data.return_value = [
            {
                "trade_date": "2024-01-15",
                "close": 10.50,
                "volume": 50000000,
                "amount": 525000000,
                "total_share": 1000000000,
                "float_share": 800000000,
            }
        ]

        result = await calculator.calculate_float_market_cap("000001.SZ", "2024-01-15")
        
        # 流通市值 = 流通股本 * 收盘价 = 800000000 * 10.50 = 8400000000
        assert result == 8400000000.0

    @pytest.mark.asyncio
    async def test_calculate_turnover_rate(self, calculator, mock_data_client):
        """测试换手率计算"""
        # 模拟20天的股票数据
        mock_data = []
        for i in range(20):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": 10.50,
                "volume": 50000000,  # 成交量5000万手
                "amount": 525000000,
                "total_share": 1000000000,
                "float_share": 800000000,  # 流通股本8亿万股
            })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_turnover_rate("000001.SZ", "2024-01-20")
        
        # 换手率 = 成交量（手）* 100 / 流通股本（万股） / 10000 * 100 = 50000000 * 100 / 800000000 / 10000 * 100 = 6.25%
        # 实际计算：50000000 * 100 / (800000000 * 10000) * 100 = 0.0625%
        assert result == 0.0625

    @pytest.mark.asyncio
    async def test_calculate_volume_ratio(self, calculator, mock_data_client):
        """测试量比计算"""
        # 模拟21天的历史数据（当前日期+前20天）
        mock_data = []
        # 前20天的数据，成交量为40000000
        for i in range(20):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "volume": 40000000
            })
        # 当日数据，成交量为50000000
        mock_data.append({
            "trade_date": "2024-01-21",
            "volume": 50000000
        })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_volume_ratio("000001.SZ", "2024-01-21")
        
        # 平均成交量 = 40000000
        # 量比 = 50000000 / 40000000 = 1.25
        assert result == 1.25

    @pytest.mark.asyncio
    async def test_calculate_price_volatility(self, calculator, mock_data_client):
        """测试价格波动率计算"""
        # 模拟历史数据（20天）
        prices = [10.0, 10.5, 9.8, 11.2, 10.8, 9.5, 10.3, 11.0, 10.2, 9.9,
                 10.7, 11.5, 10.1, 9.6, 10.9, 11.3, 10.4, 9.7, 10.6, 11.1]
        
        mock_data = []
        for i, price in enumerate(prices):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": price
            })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_price_volatility("000001.SZ", "2024-01-20")
        
        # 结果应该是一个正数（标准差）
        assert result > 0
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_return_volatility(self, calculator, mock_data_client):
        """测试收益率波动率计算"""
        # 模拟历史数据（21天）
        prices = [10.0, 10.5, 9.8, 11.2, 10.8, 9.5, 10.3, 11.0, 10.2, 9.9,
                 10.7, 11.5, 10.1, 9.6, 10.9, 11.3, 10.4, 9.7, 10.6, 11.1, 10.8]
        
        mock_data = []
        for i, price in enumerate(prices):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": price
            })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_return_volatility("000001.SZ", "2024-01-21")
        
        # 结果应该是一个正数（收益率标准差）
        assert result > 0
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_price_momentum(self, calculator, mock_data_client):
        """测试价格动量计算"""
        # 模拟历史数据（11天，包含当前日期和10天前的数据）
        mock_data = []
        # 前10天的数据
        for i in range(10):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": 10.0
            })
        # 当日数据
        mock_data.append({
            "trade_date": "2024-01-11",
            "close": 11.0
        })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_price_momentum("000001.SZ", "2024-01-11", 10)
        
        # 价格动量 = (11.0 - 10.0) / 10.0 * 100 = 10.0%
        assert result == 10.0

    @pytest.mark.asyncio
    async def test_calculate_return_momentum(self, calculator, mock_data_client):
        """测试收益率动量计算"""
        # 模拟历史数据（11天）
        prices = [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 11.0]
        
        mock_data = []
        for i, price in enumerate(prices):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": price
            })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_return_momentum("000001.SZ", "2024-01-11", 10)
        
        # 结果应该是累计收益率
        assert result > 0

    @pytest.mark.asyncio
    async def test_data_not_found(self, calculator, mock_data_client):
        """测试数据不存在的情况"""
        mock_data_client.get_stock_data.return_value = []

        # 测试总市值计算 - 应该抛出DataNotFoundError
        with pytest.raises(DataNotFoundError):
            await calculator.calculate_market_cap("000001.SZ", "2024-01-15")

        # 测试换手率计算 - 应该抛出DataNotFoundError
        with pytest.raises(DataNotFoundError):
            await calculator.calculate_turnover_rate("000001.SZ", "2024-01-15")

    @pytest.mark.asyncio
    async def test_invalid_data(self, calculator, mock_data_client):
        """测试无效数据处理"""
        # 模拟20天的无效数据
        mock_data = []
        for i in range(20):
            mock_data.append({
                "trade_date": f"2024-01-{i+1:02d}",
                "close": 10.50,
                "volume": 50000000,
                "amount": 525000000,
                "total_share": 0,  # 无效的总股本
                "float_share": 0,  # 无效的流通股本
            })
        
        mock_data_client.get_stock_data.return_value = mock_data

        result = await calculator.calculate_turnover_rate("000001.SZ", "2024-01-20")
        assert result == 0.0  # 流通股本为0时应返回0