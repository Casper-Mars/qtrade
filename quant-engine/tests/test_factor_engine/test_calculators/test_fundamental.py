"""基本面因子计算器测试模块

测试 FundamentalFactorCalculator 类的各种功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.factor_engine.calculators.fundamental import FundamentalFactorCalculator
from src.clients.data_collector_client import DataCollectorClient


class TestFundamentalFactorCalculator:
    """基本面因子计算器测试类"""

    @pytest.fixture
    def mock_data_client(self):
        """创建模拟数据客户端"""
        client = AsyncMock(spec=DataCollectorClient)
        
        # 模拟财务数据 - 注意返回的是列表格式
        financial_data = {
            "net_profit": 1000000000,  # 10亿净利润
            "total_equity": 5000000000,  # 50亿股东权益
            "total_assets": 10000000000,  # 100亿总资产
            "revenue": 8000000000,  # 80亿营收
            "cost_of_sales": 6000000000,  # 60亿销售成本
            "total_liabilities": 5000000000,  # 50亿总负债
            "current_assets": 3000000000,  # 30亿流动资产
            "current_liabilities": 2000000000,  # 20亿流动负债
        }
        
        # 返回列表格式，因为 _get_financial_data 方法期望列表
        client.get_financial_data.return_value = [financial_data]
        return client

    @pytest.fixture
    def calculator(self, mock_data_client):
        """创建基本面因子计算器实例"""
        return FundamentalFactorCalculator(mock_data_client)

    @pytest.mark.asyncio
    async def test_calculate_factors_single_factor(self, calculator, mock_data_client):
        """测试计算单个因子"""
        result = await calculator.calculate_factors("000001", ["ROE"], "2023Q3")
        
        assert "ROE" in result
        assert isinstance(result["ROE"], (float, type(None)))

    @pytest.mark.asyncio
    async def test_calculate_factors_multiple_factors(self, calculator, mock_data_client):
        """测试计算多个因子"""
        result = await calculator.calculate_factors("000001", ["ROE", "ROA"], "2023Q3")
        
        assert "ROE" in result
        assert "ROA" in result
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_calculate_factors_unsupported_factor(self, calculator, mock_data_client):
        """测试不支持的因子"""
        result = await calculator.calculate_factors("000001", ["UNSUPPORTED"], "2023Q3")
        
        assert "UNSUPPORTED" in result
        assert result["UNSUPPORTED"] is None

    @pytest.mark.asyncio
    async def test_calculate_roe_normal(self, calculator, mock_data_client):
        """测试正常情况下的ROE计算"""
        financial_data = {
            "net_profit": 1000000000,
            "total_equity": 5000000000
        }
        
        result = await calculator.calculate_roe("000001", "2023Q3", financial_data)
        
        # ROE = 净利润 / 股东权益 = 10亿 / 50亿 = 0.2 = 20%
        assert result is not None
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_roe_zero_equity(self, calculator):
        """测试股东权益为零的情况"""
        financial_data = {
            "net_profit": 1000000000,
            "total_equity": 0
        }
        
        result = await calculator.calculate_roe("000001", "2023Q3", financial_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_calculate_roa_normal(self, calculator):
        """测试正常情况下的ROA计算"""
        financial_data = {
            "net_profit": 1000000000,
            "total_assets": 10000000000
        }
        
        result = await calculator.calculate_roa("000001", "2023Q3", financial_data)
        
        # ROA = 净利润 / 总资产 = 10亿 / 100亿 = 0.1 = 10%
        assert result is not None
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_calculate_gross_margin_normal(self, calculator):
        """测试正常情况下的毛利率计算"""
        financial_data = {
            "revenue": 8000000000,
            "cost_of_sales": 6000000000
        }
        
        result = await calculator.calculate_gross_margin("000001", "2023Q3", financial_data)
        
        # 毛利率 = (营收 - 销售成本) / 营收 = (80亿 - 60亿) / 80亿 = 0.25 = 25%
        assert result is not None
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_calculate_net_profit_margin_normal(self, calculator):
        """测试正常情况下的净利率计算"""
        financial_data = {
            "net_profit": 1000000000,
            "revenue": 8000000000
        }
        
        result = await calculator.calculate_net_profit_margin("000001", "2023Q3", financial_data)
        
        # 净利率 = 净利润 / 营收 = 10亿 / 80亿 = 0.125 = 12.5%
        assert result is not None
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_calculate_debt_ratio_normal(self, calculator):
        """测试正常情况下的资产负债率计算"""
        financial_data = {
            "total_liabilities": 5000000000,
            "total_assets": 10000000000
        }
        
        result = await calculator.calculate_debt_ratio("000001", "2023Q3", financial_data)
        
        # 资产负债率 = 总负债 / 总资产 = 50亿 / 100亿 = 0.5 = 50%
        assert result is not None
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_calculate_current_ratio_normal(self, calculator):
        """测试正常情况下的流动比率计算"""
        financial_data = {
            "current_assets": 3000000000,
            "current_liabilities": 2000000000
        }
        
        result = await calculator.calculate_current_ratio("000001", "2023Q3", financial_data)
        
        # 流动比率 = 流动资产 / 流动负债 = 30亿 / 20亿 = 1.5
        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    # 边界条件测试
    @pytest.mark.asyncio
    async def test_edge_case_zero_revenue(self, calculator):
        """测试营收为零的边界情况"""
        financial_data = {
            "net_profit": 1000000000,
            "revenue": 0
        }
        
        result = await calculator.calculate_net_profit_margin("000001", "2023Q3", financial_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_edge_case_zero_assets(self, calculator):
        """测试总资产为零的边界情况"""
        financial_data = {
            "net_profit": 1000000000,
            "total_assets": 0
        }
        
        result = await calculator.calculate_roa("000001", "2023Q3", financial_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_edge_case_zero_current_liabilities(self, calculator):
        """测试流动负债为零的边界情况"""
        financial_data = {
            "current_assets": 3000000000,
            "current_liabilities": 0
        }
        
        result = await calculator.calculate_current_ratio("000001", "2023Q3", financial_data)
        assert result is None

    # 辅助方法测试
    def test_get_previous_period_quarterly(self, calculator):
        """测试季度期间的上一期间计算"""
        assert calculator._get_previous_period("2023Q3") == "2023Q2"
        assert calculator._get_previous_period("2023Q1") == "2022Q4"

    def test_get_previous_period_annual(self, calculator):
        """测试年度期间的上一期间计算"""
        assert calculator._get_previous_period("2023") == "2022"

    def test_get_previous_year_period_quarterly(self, calculator):
        """测试季度期间的上年同期计算"""
        assert calculator._get_previous_year_period("2023Q3") == "2022Q3"

    def test_get_previous_year_period_annual(self, calculator):
        """测试年度期间的上年同期计算"""
        assert calculator._get_previous_year_period("2023") == "2022"