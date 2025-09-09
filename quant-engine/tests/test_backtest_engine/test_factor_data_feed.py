"""FactorDataFeed单元测试模块

测试FactorDataFeed类的所有功能，包括：
- 数据源初始化
- 数据准备和获取
- 价格数据获取
- 因子数据获取
- 数据合并
- 数据预处理
- 异常处理
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from src.backtest_engine.services.factor_data_feed import FactorDataFeed
from src.backtest_engine.models.backtest_models import FactorCombination, Factor, BacktestFactorConfig, FactorItem
from tests.test_backtest_engine.test_utils import TestDataFactory, MockTushareClient, MockFactorService


class TestFactorDataFeed:
    """FactorDataFeed测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.test_data = TestDataFactory()
        self.mock_tushare_client = MockTushareClient()
        self.mock_factor_service = MockFactorService()
        
        # 创建测试用的因子组合
        self.factor_combination = self._create_test_factor_combination()
        
        # 测试参数
        self.stock_code = "000001.SZ"
        self.start_date = "2023-01-01"
        self.end_date = "2023-12-31"
    
    def test_init_success(self):
        """测试成功初始化"""
        # 执行测试
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 验证结果
        assert data_feed.stock_code == self.stock_code
        assert data_feed.start_date == self.start_date
        assert data_feed.end_date == self.end_date
        assert data_feed.factor_combination == self.factor_combination
        assert data_feed.data_client == self.mock_tushare_client
        assert data_feed.factor_service == self.mock_factor_service
    
    def test_init_with_invalid_stock_code(self):
        """测试无效股票代码初始化"""
        # 测试空股票代码
        with pytest.raises(ValueError) as exc_info:
            FactorDataFeed(
                stock_code="",
                start_date=self.start_date,
                end_date=self.end_date,
                factor_combination=self.factor_combination,
                data_client=self.mock_tushare_client,
                factor_service=self.mock_factor_service
            )
        assert "股票代码不能为空" in str(exc_info.value)
        
        # 测试None股票代码
        with pytest.raises(ValueError) as exc_info:
            FactorDataFeed(
                stock_code=None,
                start_date=self.start_date,
                end_date=self.end_date,
                factor_combination=self.factor_combination,
                data_client=self.mock_tushare_client,
                factor_service=self.mock_factor_service
            )
        assert "股票代码不能为空" in str(exc_info.value)
    
    def test_init_with_invalid_dates(self):
        """测试无效日期初始化"""
        # 测试开始日期晚于结束日期
        with pytest.raises(ValueError) as exc_info:
            FactorDataFeed(
                stock_code=self.stock_code,
                start_date="2023-12-31",
                end_date="2023-01-01",
                factor_combination=self.factor_combination,
                data_client=self.mock_tushare_client,
                factor_service=self.mock_factor_service
            )
        assert "开始日期不能晚于结束日期" in str(exc_info.value)
        
        # 测试无效日期格式
        with pytest.raises(ValueError):
            FactorDataFeed(
                stock_code=self.stock_code,
                start_date="invalid-date",
                end_date=self.end_date,
                factor_combination=self.factor_combination,
                data_client=self.mock_tushare_client,
                factor_service=self.mock_factor_service
            )
    
    def test_init_with_none_clients(self):
        """测试客户端为None的初始化"""
        with pytest.raises(ValueError) as exc_info:
            FactorDataFeed(
                stock_code=self.stock_code,
                start_date=self.start_date,
                end_date=self.end_date,
                factor_combination=self.factor_combination,
                data_client=None,
                factor_service=self.mock_factor_service
            )
        assert "数据客户端不能为空" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_prepare_data_success(self):
        """测试成功准备数据"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        result = await data_feed.prepare_data()
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'low' in result.columns
        assert 'close' in result.columns
        assert 'volume' in result.columns
        assert 'factor_data' in result.columns
        
        # 验证数据类型
        assert result.index.dtype == 'datetime64[ns]'
        assert pd.api.types.is_numeric_dtype(result['open'])
        assert pd.api.types.is_numeric_dtype(result['close'])
    
    @pytest.mark.asyncio
    async def test_prepare_data_with_empty_price_data(self):
        """测试价格数据为空的情况"""
        # 准备测试数据
        mock_client = Mock()
        mock_client.get_daily_data = AsyncMock(return_value=pd.DataFrame())
        
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=mock_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试并验证异常
        with pytest.raises(ValueError) as exc_info:
            await data_feed.prepare_data()
        
        assert "未获取到价格数据" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_price_data_success(self):
        """测试成功获取价格数据"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        price_data = await data_feed._get_price_data()
        
        # 验证结果
        assert isinstance(price_data, pd.DataFrame)
        assert not price_data.empty
        assert list(price_data.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert price_data.index.dtype == 'datetime64[ns]'
        
        # 验证数据逻辑性
        assert (price_data['high'] >= price_data['low']).all()
        assert (price_data['high'] >= price_data['open']).all()
        assert (price_data['high'] >= price_data['close']).all()
        assert (price_data['volume'] >= 0).all()
    
    @pytest.mark.asyncio
    async def test_get_price_data_with_client_error(self):
        """测试客户端错误时的价格数据获取"""
        # 准备测试数据
        mock_client = Mock()
        mock_client.get_daily_data = AsyncMock(side_effect=Exception("网络错误"))
        
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=mock_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试并验证异常
        with pytest.raises(Exception) as exc_info:
            await data_feed._get_price_data()
        
        assert "网络错误" in str(exc_info.value)
    
    def test_get_factor_data_success(self):
        """测试成功获取因子数据"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        factor_data = data_feed._get_factor_data()
        
        # 验证结果
        assert isinstance(factor_data, pd.DataFrame)
        if not factor_data.empty:
            assert 'stock_code' in factor_data.columns
            # 验证因子列存在
            factor_names = [f.factor_name for f in self.factor_combination.factors]
            for factor_name in factor_names:
                assert factor_name in factor_data.columns
    
    def test_get_factor_data_with_no_factors(self):
        """测试无因子情况下的因子数据获取"""
        # 准备测试数据
        empty_combination = FactorCombination(
            combination_id=1,
            combination_name="空组合",
            factors=[],
            weights=[]
        )
        
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=empty_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        factor_data = data_feed._get_factor_data()
        
        # 验证结果
        assert isinstance(factor_data, pd.DataFrame)
        # 空因子组合应该返回空DataFrame或只包含基础列的DataFrame
    
    def test_merge_data_success(self):
        """测试成功合并数据"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 创建测试数据
        price_data = self._create_test_price_data()
        factor_data = self._create_test_factor_data()
        
        # 执行测试
        merged_data = data_feed._merge_data(price_data, factor_data)
        
        # 验证结果
        assert isinstance(merged_data, pd.DataFrame)
        assert not merged_data.empty
        assert 'open' in merged_data.columns
        assert 'high' in merged_data.columns
        assert 'low' in merged_data.columns
        assert 'close' in merged_data.columns
        assert 'volume' in merged_data.columns
        assert 'factor_data' in merged_data.columns
        
        # 验证factor_data列的内容
        assert merged_data['factor_data'].iloc[0] is not None
        assert isinstance(merged_data['factor_data'].iloc[0], dict)
    
    def test_merge_data_with_empty_factor_data(self):
        """测试因子数据为空时的数据合并"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 创建测试数据
        price_data = self._create_test_price_data()
        empty_factor_data = pd.DataFrame()
        
        # 执行测试
        merged_data = data_feed._merge_data(price_data, empty_factor_data)
        
        # 验证结果
        assert isinstance(merged_data, pd.DataFrame)
        assert not merged_data.empty
        assert 'factor_data' in merged_data.columns
        assert merged_data['factor_data'].iloc[0] is None
    
    def test_preprocess_data_success(self):
        """测试成功预处理数据"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 创建包含异常数据的测试数据
        test_data = self._create_test_data_with_anomalies()
        
        # 执行测试
        processed_data = data_feed._preprocess_data(test_data)
        
        # 验证结果
        assert isinstance(processed_data, pd.DataFrame)
        assert len(processed_data) <= len(test_data)  # 异常数据应被删除
        
        # 验证数据逻辑性
        assert (processed_data['high'] >= processed_data['low']).all()
        assert (processed_data['high'] >= processed_data['open']).all()
        assert (processed_data['high'] >= processed_data['close']).all()
        assert (processed_data['volume'] >= 0).all()
    
    def test_preprocess_data_with_missing_values(self):
        """测试包含缺失值的数据预处理"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 创建包含缺失值的测试数据
        test_data = self._create_test_price_data()
        test_data.loc[test_data.index[0], 'open'] = None
        test_data.loc[test_data.index[1], 'close'] = None
        
        # 执行测试
        processed_data = data_feed._preprocess_data(test_data)
        
        # 验证结果
        assert isinstance(processed_data, pd.DataFrame)
        assert len(processed_data) < len(test_data)  # 缺失值行应被删除
        assert not processed_data.isnull().any().any()  # 不应有缺失值
    
    def test_get_data_info(self):
        """测试获取数据源信息"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        info = data_feed.get_data_info()
        
        # 验证结果
        assert isinstance(info, dict)
        assert info['stock_code'] == self.stock_code
        assert info['start_date'] == self.start_date
        assert info['end_date'] == self.end_date
        assert info['factor_count'] == len(self.factor_combination.factors)
        assert info['factor_names'] == [f.factor_name for f in self.factor_combination.factors]
        assert 'data_length' in info
    
    def test_get_data_info_with_no_factor_combination(self):
        """测试无因子组合时的数据源信息获取"""
        # 准备测试数据
        data_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            factor_combination=None,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        # 执行测试
        info = data_feed.get_data_info()
        
        # 验证结果
        assert info['factor_count'] == 0
        assert info['factor_names'] == []
    
    def test_edge_cases_and_boundary_conditions(self):
        """测试边界条件和特殊情况"""
        # 测试单日数据
        single_day_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date="2023-01-01",
            end_date="2023-01-01",
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        info = single_day_feed.get_data_info()
        assert info['start_date'] == info['end_date']
        
        # 测试极长时间范围
        long_range_feed = FactorDataFeed(
            stock_code=self.stock_code,
            start_date="2020-01-01",
            end_date="2023-12-31",
            factor_combination=self.factor_combination,
            data_client=self.mock_tushare_client,
            factor_service=self.mock_factor_service
        )
        
        info = long_range_feed.get_data_info()
        assert info['start_date'] == "2020-01-01"
        assert info['end_date'] == "2023-12-31"
    
    def _create_test_factor_combination(self):
        """创建测试用因子组合"""
        factors = [
            FactorItem(
                factor_name="rsi_14",
                factor_type="technical",
                weight=0.3
            ),
            FactorItem(
                factor_name="ma_20",
                factor_type="technical",
                weight=0.4
            ),
            FactorItem(
                factor_name="pe_ratio",
                factor_type="fundamental",
                weight=0.3
            )
        ]
        
        return BacktestFactorConfig(
            combination_id="test_combination_1",
            factors=factors,
            description="测试用因子组合"
        )
    
    def _create_test_price_data(self):
        """创建测试用价格数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
        data = {
            'open': [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9],
            'high': [10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9, 12.3, 12.5, 12.2],
            'low': [9.8, 10.2, 10.5, 10.3, 10.8, 11.0, 10.9, 11.3, 11.5, 11.4],
            'close': [10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9, 12.1],
            'volume': [1000000, 1200000, 800000, 1500000, 900000, 1100000, 1300000, 1400000, 1600000, 1000000]
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def _create_test_factor_data(self):
        """创建测试用因子数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
        data = {
            'stock_code': ['000001.SZ'] * len(dates),
            'rsi_14': [0.6, 0.65, 0.7, 0.68, 0.72, 0.75, 0.73, 0.78, 0.8, 0.79],
            'ma_20': [0.5, 0.52, 0.55, 0.53, 0.57, 0.6, 0.58, 0.62, 0.65, 0.63],
            'pe_ratio': [0.4, 0.42, 0.45, 0.43, 0.47, 0.5, 0.48, 0.52, 0.55, 0.53]
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def _create_test_data_with_anomalies(self):
        """创建包含异常数据的测试数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-01-05', freq='D')
        data = {
            'open': [10.0, 10.5, 11.0, 10.8, 11.2],
            'high': [9.5, 11.2, 11.5, 11.3, 11.8],  # 第一行high < open，异常
            'low': [9.8, 10.2, 12.0, 10.3, 10.8],   # 第三行low > high，异常
            'close': [10.5, 11.0, 10.8, 11.2, 11.5],
            'volume': [1000000, 1200000, -800000, 1500000, 900000]  # 第三行volume < 0，异常
        }
        
        df = pd.DataFrame(data, index=dates)
        return df