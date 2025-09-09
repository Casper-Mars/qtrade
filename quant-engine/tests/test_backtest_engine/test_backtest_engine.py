"""BacktestEngine单元测试

测试回测引擎的核心功能：
- 初始化和配置
- 配置验证
- 回测执行流程
- 结果处理
- 异常处理
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from src.backtest_engine.models.backtest_models import (
    BacktestConfig,
    BacktestFactorConfig,
    BacktestMode,
    BacktestResult,
)
from src.backtest_engine.models.factor_combination import FactorConfig
from src.backtest_engine.services.backtest_engine import BacktestEngine
from src.utils.exceptions import ValidationException
from .test_utils import (
    MockTushareClient,
    MockFactorService,
    TestDataFactory,
    create_mock_cerebro,
    MockBacktraderStrategy,
)


class TestBacktestEngine:
    """BacktestEngine测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.mock_factor_service = MockFactorService()
        self.mock_data_client = MockTushareClient()
        self.engine = BacktestEngine(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client
        )
        self.valid_config = TestDataFactory.create_backtest_config()

    def test_init_success(self):
        """测试正常初始化"""
        engine = BacktestEngine(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client
        )
        
        assert engine.factor_service == self.mock_factor_service
        assert engine.data_client == self.mock_data_client
        assert engine.cerebro is not None
        assert engine._current_config is None
        assert engine._results == []

    def test_init_with_none_services(self):
        """测试使用None服务初始化"""
        # 应该能够初始化，但在运行时会出错
        engine = BacktestEngine(
            factor_service=None,
            data_client=None
        )
        
        assert engine.factor_service is None
        assert engine.data_client is None

    def test_validate_config_success(self):
        """测试配置验证成功"""
        # 不应该抛出异常
        self.engine._validate_config(self.valid_config)

    def test_validate_config_invalid_date_range(self):
        """测试无效日期范围"""
        config = TestDataFactory.create_backtest_config(
            start_date="2023-12-31",
            end_date="2023-01-01"
        )
        
        with pytest.raises(ValidationException, match="开始日期必须早于结束日期"):
            self.engine._validate_config(config)

    def test_validate_config_same_dates(self):
        """测试相同的开始和结束日期"""
        config = TestDataFactory.create_backtest_config(
            start_date="2023-06-01",
            end_date="2023-06-01"
        )
        
        with pytest.raises(ValidationException, match="开始日期必须早于结束日期"):
            self.engine._validate_config(config)

    def test_validate_config_empty_factors(self):
        """测试空因子组合"""
        config = TestDataFactory.create_backtest_config()
        config.factor_combination.factors = []
        
        with pytest.raises(ValidationException, match="因子组合不能为空"):
            self.engine._validate_config(config)

    def test_validate_config_none_factor_combination(self):
        """测试None因子组合"""
        config = TestDataFactory.create_backtest_config()
        config.factor_combination = None
        
        with pytest.raises(ValidationException, match="因子组合不能为空"):
            self.engine._validate_config(config)

    def test_validate_config_invalid_weights_sum(self):
        """测试权重总和不为1"""
        factors = [
            FactorConfig(name="momentum", factor_type="technical", weight=Decimal('0.6')),
            FactorConfig(name="value", factor_type="fundamental", weight=Decimal('0.6')),  # 总和1.2
        ]
        config = TestDataFactory.create_backtest_config()
        config.factor_combination.factors = factors
        
        with pytest.raises(ValidationException, match="因子权重总和必须为1.0"):
            self.engine._validate_config(config)

    def test_validate_config_zero_initial_capital(self):
        """测试零初始资金"""
        config = TestDataFactory.create_backtest_config(initial_capital=0)
        
        with pytest.raises(ValidationException, match="初始资金必须大于0"):
            self.engine._validate_config(config)

    def test_validate_config_negative_initial_capital(self):
        """测试负初始资金"""
        config = TestDataFactory.create_backtest_config(initial_capital=-1000)
        
        with pytest.raises(ValidationException, match="初始资金必须大于0"):
            self.engine._validate_config(config)

    def test_validate_config_negative_slippage(self):
        """测试负滑点"""
        config = TestDataFactory.create_backtest_config(slippage=-0.001)
        
        with pytest.raises(ValidationException, match="滑点不能为负数"):
            self.engine._validate_config(config)

    def test_validate_config_invalid_buy_threshold(self):
        """测试无效买入阈值"""
        config = TestDataFactory.create_backtest_config(buy_threshold=1.5)
        
        with pytest.raises(ValidationException, match="买入阈值必须在0-1之间"):
            self.engine._validate_config(config)

    def test_validate_config_invalid_sell_threshold(self):
        """测试无效卖出阈值"""
        config = TestDataFactory.create_backtest_config(sell_threshold=-0.1)
        
        with pytest.raises(ValidationException, match="卖出阈值必须在0-1之间"):
            self.engine._validate_config(config)

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_initialize_cerebro(self, mock_cerebro_class):
        """测试Cerebro初始化"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        
        self.engine._initialize_cerebro(self.valid_config)
        
        # 验证Cerebro配置
        mock_cerebro.broker.setcash.assert_called_once_with(self.valid_config.initial_capital)
        mock_cerebro.broker.setcommission.assert_called_once_with(commission=self.valid_config.transaction_cost)
        mock_cerebro.addsizer.assert_called_once()

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_initialize_cerebro_with_slippage(self, mock_cerebro_class):
        """测试带滑点的Cerebro初始化"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        
        config = TestDataFactory.create_backtest_config(slippage=0.002)
        self.engine._initialize_cerebro(config)
        
        mock_cerebro.broker.set_slippage_perc.assert_called_once_with(0.002)

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_initialize_cerebro_zero_slippage(self, mock_cerebro_class):
        """测试零滑点的Cerebro初始化"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        
        config = TestDataFactory.create_backtest_config(slippage=0.0)
        self.engine._initialize_cerebro(config)
        
        # 零滑点时不应该调用set_slippage_perc
        mock_cerebro.broker.set_slippage_perc.assert_not_called()

    @patch('src.backtest_engine.services.backtest_engine.FactorDataFeed')
    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_setup_data_feeds(self, mock_cerebro_class, mock_data_feed_class):
        """测试数据源配置"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        mock_data_feed = Mock()
        mock_data_feed_class.return_value = mock_data_feed
        
        self.engine._setup_data_feeds(self.valid_config)
        
        # 验证数据源创建
        mock_data_feed_class.assert_called_once_with(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client,
            stock_code=self.valid_config.stock_code,
            start_date=self.valid_config.start_date,
            end_date=self.valid_config.end_date,
            factor_combination=self.valid_config.factor_combination
        )
        
        # 验证数据源添加到Cerebro
        mock_cerebro.adddata.assert_called_once_with(mock_data_feed)

    @patch('src.backtest_engine.services.backtest_engine.FactorStrategy')
    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_setup_strategy(self, mock_cerebro_class, mock_strategy_class):
        """测试策略配置"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        
        self.engine._setup_strategy(self.valid_config)
        
        # 验证策略添加
        mock_cerebro.addstrategy.assert_called_once_with(
            mock_strategy_class,
            factor_combination=self.valid_config.factor_combination,
            buy_threshold=self.valid_config.buy_threshold,
            sell_threshold=self.valid_config.sell_threshold,
            backtest_mode=self.valid_config.backtest_mode
        )

    @patch('src.backtest_engine.services.backtest_engine.BacktraderAnalyzer')
    @patch('src.backtest_engine.services.backtest_engine.bt')
    def test_setup_analyzers(self, mock_bt, mock_analyzer_class):
        """测试分析器配置"""
        mock_cerebro = create_mock_cerebro()
        self.engine.cerebro = mock_cerebro
        
        self.engine._setup_analyzers(self.valid_config)
        
        # 验证内置分析器添加
        expected_calls = 6  # 5个内置分析器 + 1个自定义分析器
        assert mock_cerebro.addanalyzer.call_count == expected_calls

    def test_process_results_success(self):
        """测试结果处理成功"""
        mock_strategy = MockBacktraderStrategy()
        results = [mock_strategy]
        
        result = self.engine._process_results(results, self.valid_config, 5.2)
        
        # 验证结果基本信息
        assert result.config_id == self.valid_config.id
        assert result.stock_code == self.valid_config.stock_code
        assert result.start_date == self.valid_config.start_date
        assert result.end_date == self.valid_config.end_date
        assert result.execution_time == 5.2
        
        # 验证绩效指标
        assert result.total_return == 0.15
        assert result.sharpe_ratio == 1.2
        assert result.max_drawdown == 0.05  # 转换为小数
        
        # 验证交易统计
        assert result.trade_count == 50
        assert result.win_rate == 0.6  # 30/50

    def test_process_results_empty_results(self):
        """测试空结果处理"""
        with pytest.raises(Exception, match="回测结果为空"):
            self.engine._process_results([], self.valid_config, 5.2)

    def test_process_results_none_sharpe_ratio(self):
        """测试None夏普比率处理"""
        mock_strategy = MockBacktraderStrategy()
        mock_strategy.analyzers.sharpe.get_analysis = lambda: {'sharperatio': None}
        results = [mock_strategy]
        
        result = self.engine._process_results(results, self.valid_config, 5.2)
        
        # None夏普比率应该转换为0.0
        assert result.sharpe_ratio == 0.0

    def test_get_cerebro_info_initialized(self):
        """测试获取已初始化Cerebro信息"""
        info = self.engine.get_cerebro_info()
        
        assert info['status'] == 'initialized'
        assert 'cash' in info
        assert 'value' in info
        assert 'data_feeds' in info
        assert 'strategies' in info
        assert 'analyzers' in info

    def test_get_cerebro_info_not_initialized(self):
        """测试获取未初始化Cerebro信息"""
        self.engine.cerebro = None
        
        info = self.engine.get_cerebro_info()
        
        assert info == {'status': 'not_initialized'}

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    @patch('src.backtest_engine.services.backtest_engine.FactorDataFeed')
    @patch('src.backtest_engine.services.backtest_engine.FactorStrategy')
    @patch('src.backtest_engine.services.backtest_engine.BacktraderAnalyzer')
    def test_run_backtest_success(self, mock_analyzer, mock_strategy, mock_data_feed, mock_cerebro_class):
        """测试完整回测流程成功"""
        # 设置Mock
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        mock_cerebro.run.return_value = [MockBacktraderStrategy()]
        
        # 执行回测
        result = self.engine.run_backtest(self.valid_config)
        
        # 验证结果
        assert isinstance(result, type(TestDataFactory.create_backtest_result()))
        assert result.config_id == self.valid_config.id
        assert result.execution_time > 0
        
        # 验证流程调用
        mock_cerebro.run.assert_called_once()

    def test_run_backtest_validation_error(self):
        """测试回测配置验证失败"""
        invalid_config = TestDataFactory.create_backtest_config(initial_capital=0)
        
        with pytest.raises(ValidationException):
            self.engine.run_backtest(invalid_config)

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_run_backtest_execution_error(self, mock_cerebro_class):
        """测试回测执行失败"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        mock_cerebro.run.side_effect = Exception("执行失败")
        
        with pytest.raises(Exception, match="执行失败"):
            self.engine.run_backtest(self.valid_config)

    @patch('src.backtest_engine.services.backtest_engine.bt.Cerebro')
    def test_run_backtest_state_cleanup(self, mock_cerebro_class):
        """测试回测状态清理"""
        mock_cerebro = create_mock_cerebro()
        mock_cerebro_class.return_value = mock_cerebro
        mock_cerebro.run.side_effect = Exception("执行失败")
        
        # 设置初始状态
        self.engine._current_config = self.valid_config
        
        try:
            self.engine.run_backtest(self.valid_config)
        except Exception:
            pass
        
        # 验证状态清理
        assert self.engine._current_config is None

    def test_edge_case_minimal_config(self):
        """测试边界情况：最小配置"""
        factors = [FactorConfig(name="momentum", factor_type="technical", weight=Decimal('1.0'))]
        factor_combination = BacktestFactorConfig(
            combination_id="minimal",
            factors=factors,
            description="最小配置"
        )
        
        config = BacktestConfig(
            id=uuid4(),
            stock_code="000001.SZ",
            start_date="2023-01-01",
            end_date="2023-01-02",  # 最小日期范围
            initial_capital=1.0,  # 最小资金
            factor_combination=factor_combination,
            buy_threshold=0.0,  # 边界值
            sell_threshold=1.0,  # 边界值
            transaction_cost=0.0,
            slippage=0.0,
            backtest_mode=BacktestMode.HISTORICAL_SIMULATION
        )
        
        # 应该通过验证
        self.engine._validate_config(config)

    def test_edge_case_maximum_thresholds(self):
        """测试边界情况：最大阈值"""
        config = TestDataFactory.create_backtest_config(
            buy_threshold=1.0,
            sell_threshold=0.0
        )
        
        # 应该通过验证
        self.engine._validate_config(config)

    def test_concurrent_backtest_isolation(self):
        """测试并发回测的隔离性"""
        # 创建两个引擎实例
        engine1 = BacktestEngine(self.mock_factor_service, self.mock_data_client)
        engine2 = BacktestEngine(self.mock_factor_service, self.mock_data_client)
        
        config1 = TestDataFactory.create_backtest_config(stock_code="000001.SZ")
        config2 = TestDataFactory.create_backtest_config(stock_code="000002.SZ")
        
        # 设置不同的当前配置
        engine1._current_config = config1
        engine2._current_config = config2
        
        # 验证隔离性
        assert engine1._current_config.stock_code == "000001.SZ"
        assert engine2._current_config.stock_code == "000002.SZ"
        assert engine1.cerebro is not engine2.cerebro