"""BacktestEngine回测引擎核心模块单元测试

本模块测试基于Backtrader框架的回测引擎核心功能，包括：
- BacktestEngine 初始化测试
- 回测配置验证测试
- Cerebro引擎配置测试
- 数据源配置测试
- 策略配置测试
- 分析器配置测试
- 回测执行流程测试
- 结果处理测试
"""

import logging
from decimal import Decimal
from unittest.mock import Mock, patch

import backtrader as bt  # type: ignore
import pytest
from pydantic import ValidationError

from src.backtest_engine.models.backtest_models import (
    BacktestConfig,
    BacktestFactorConfig,
    BacktestMode,
    BacktestResult,
    FactorItem,
)
from src.backtest_engine.services.backtest_engine import BacktestEngine
from src.clients.tushare_client import TushareClient
from src.factor_engine.services.factor_service import FactorService
from src.utils.exceptions import ValidationException


class TestBacktestEngine:
    """BacktestEngine测试类"""

    def setup_method(self) -> None:
        """测试前置设置"""
        # 创建模拟对象
        self.mock_factor_service = Mock(spec=FactorService)
        self.mock_data_client = Mock(spec=TushareClient)

        # 创建BacktestEngine实例
        self.backtest_engine = BacktestEngine(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client
        )

        # 创建测试用的因子配置
        self.factor_config = BacktestFactorConfig(
            combination_id="test_combination_001",
            description="测试因子组合",
            factors=[
                FactorItem(
                    factor_name="PE",
                    factor_type="fundamental",
                    weight=0.4
                ),
                FactorItem(
                    factor_name="RSI",
                    factor_type="technical",
                    weight=0.3
                ),
                FactorItem(
                    factor_name="MA",
                    factor_type="technical",
                    weight=0.3
                )
            ]
        )

        # 创建测试用的回测配置
        self.backtest_config = BacktestConfig(
            name="测试回测配置",
            stock_code="000001.SZ",
            start_date="2023-01-01",
            end_date="2023-12-31",
            factor_combination=self.factor_config,
            initial_capital=Decimal('100000'),
            transaction_cost=0.001,
            slippage=0.0001,
            buy_threshold=0.6,
            sell_threshold=0.4,
            backtest_mode=BacktestMode.HISTORICAL_SIMULATION,
            optimization_result_id="test_optimization_001"
        )

    def test_initialization(self) -> None:
        """测试BacktestEngine初始化"""
        # 验证初始化参数
        assert self.backtest_engine.factor_service == self.mock_factor_service
        assert self.backtest_engine.data_client == self.mock_data_client

        # 验证Cerebro引擎已创建
        assert isinstance(self.backtest_engine.cerebro, bt.Cerebro)

        # 验证运行时状态初始化
        assert self.backtest_engine._current_config is None
        assert self.backtest_engine._results == []

    def test_get_cerebro_info_not_initialized(self) -> None:
        """测试获取未初始化的Cerebro信息"""
        # 创建新的引擎实例，不设置cerebro
        engine = BacktestEngine(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client
        )
        engine.cerebro = None

        info = engine.get_cerebro_info()
        assert info["status"] == "not_initialized"

    def test_get_cerebro_info_initialized(self) -> None:
        """测试获取已初始化的Cerebro信息"""
        info = self.backtest_engine.get_cerebro_info()

        assert info["status"] == "initialized"
        assert "cash" in info
        assert "value" in info
        assert "data_feeds" in info
        assert "strategies" in info
        assert "analyzers" in info
        assert isinstance(info["cash"], float)
        assert isinstance(info["value"], float)
        assert isinstance(info["data_feeds"], int)
        assert isinstance(info["strategies"], int)
        assert isinstance(info["analyzers"], int)

    def test_validate_config_success(self) -> None:
        """测试配置验证成功"""
        # 正常配置应该通过验证
        try:
            self.backtest_engine._validate_config(self.backtest_config)
        except ValidationException:
            pytest.fail("正常配置验证失败")

    def test_validate_config_invalid_date_range(self) -> None:
        """测试无效日期范围验证"""
        # 创建开始日期晚于结束日期的配置
        invalid_config = self.backtest_config.model_copy()
        invalid_config.start_date = "2023-12-31"
        invalid_config.end_date = "2023-01-01"

        with pytest.raises(ValidationException, match="开始日期必须早于结束日期"):
            self.backtest_engine._validate_config(invalid_config)

    def test_validate_config_empty_factors(self) -> None:
        """测试空因子组合验证"""
        # 创建空因子组合的配置
        empty_factor_config = BacktestFactorConfig(
            combination_id="empty_test",
            description="空因子组合测试",
            factors=[]
        )

        # 由于Pydantic验证，这应该在模型创建时就失败
        with pytest.raises(ValidationError):
            BacktestConfig(
                name="测试配置",
                stock_code="000001.SZ",
                start_date="2023-01-01",
                end_date="2023-12-31",
                factor_combination=empty_factor_config,
                optimization_result_id="test_optimization_002"
            )

    def test_validate_config_invalid_weight_sum(self) -> None:
        """测试无效权重总和验证"""
        # 创建权重总和不为1的因子配置
        invalid_factor_config = BacktestFactorConfig(
            combination_id="invalid_weight_test",
            description="无效权重测试",
            factors=[
                FactorItem(factor_name="PE", factor_type="fundamental", weight=0.3),
                FactorItem(factor_name="RSI", factor_type="technical", weight=0.3)
                # 总权重为0.6，不等于1.0
            ]
        )

        # 由于Pydantic验证，这应该在模型创建时就失败
        with pytest.raises(ValidationError):
            BacktestConfig(
                name="测试配置",
                stock_code="000001.SZ",
                start_date="2023-01-01",
                end_date="2023-12-31",
                factor_combination=invalid_factor_config,
                optimization_result_id="test_optimization_003"
            )

    def test_validate_config_invalid_capital(self) -> None:
        """测试无效初始资金验证"""
        invalid_config = self.backtest_config.model_copy()
        invalid_config.initial_capital = Decimal('0')

        with pytest.raises(ValidationException, match="初始资金必须大于0"):
            self.backtest_engine._validate_config(invalid_config)

    def test_validate_config_invalid_slippage(self) -> None:
        """测试无效滑点验证"""
        invalid_config = self.backtest_config.model_copy()
        invalid_config.slippage = -0.001

        with pytest.raises(ValidationException, match="滑点不能为负数"):
            self.backtest_engine._validate_config(invalid_config)

    def test_validate_config_invalid_thresholds(self) -> None:
        """测试无效阈值验证"""
        # 测试买入阈值超出范围
        invalid_config = self.backtest_config.model_copy()
        invalid_config.buy_threshold = 1.5

        with pytest.raises(ValidationException, match="买入阈值必须在0-1之间"):
            self.backtest_engine._validate_config(invalid_config)

        # 测试卖出阈值超出范围
        invalid_config = self.backtest_config.model_copy()
        invalid_config.sell_threshold = -0.1

        with pytest.raises(ValidationException, match="卖出阈值必须在0-1之间"):
            self.backtest_engine._validate_config(invalid_config)

    def test_initialize_cerebro(self) -> None:
        """测试Cerebro引擎初始化"""
        # 执行初始化
        self.backtest_engine._initialize_cerebro(self.backtest_config)

        # 验证初始资金设置
        assert self.backtest_engine.cerebro.broker.getcash() == float(self.backtest_config.initial_capital)

        # 验证佣金设置
        # 注意：Backtrader的佣金设置可能需要通过其他方式验证

        # 验证Cerebro实例已重置
        assert isinstance(self.backtest_engine.cerebro, bt.Cerebro)

    @patch('src.backtest_engine.services.backtest_engine.FactorDataFeed')
    def test_setup_data_feeds(self, mock_data_feed_class: Mock) -> None:
        """测试数据源配置"""
        mock_data_feed = Mock()
        mock_data_feed_class.return_value = mock_data_feed

        # 执行数据源配置
        self.backtest_engine._setup_data_feeds(self.backtest_config)

        # 验证FactorDataFeed被正确创建
        mock_data_feed_class.assert_called_once_with(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client,
            stock_code=self.backtest_config.stock_code,
            start_date=self.backtest_config.start_date,
            end_date=self.backtest_config.end_date,
            factor_combination=self.backtest_config.factor_combination
        )

        # 验证数据源被添加到Cerebro
        assert len(self.backtest_engine.cerebro.datas) == 1

    @patch('src.backtest_engine.services.backtest_engine.FactorStrategy')
    def test_setup_strategy(self, mock_strategy_class: Mock) -> None:
        """测试策略配置"""
        # 执行策略配置
        self.backtest_engine._setup_strategy(self.backtest_config)

        # 验证策略被添加到Cerebro
        assert len(self.backtest_engine.cerebro.strats) == 1

    def test_setup_analyzers(self) -> None:
        """测试分析器配置"""
        # 执行分析器配置
        self.backtest_engine._setup_analyzers(self.backtest_config)

        # 验证分析器被添加到Cerebro
        assert len(self.backtest_engine.cerebro.analyzers) > 0

        # 验证包含必要的分析器
        analyzer_names = [analyzer._name for analyzer in self.backtest_engine.cerebro.analyzers]
        expected_analyzers = ['returns', 'sharpe', 'drawdown', 'trades', 'sqn', 'performance']

        for expected in expected_analyzers:
            assert expected in analyzer_names

    def test_process_results_empty_results(self) -> None:
        """测试处理空回测结果"""
        with pytest.raises(Exception, match="回测结果为空"):
            self.backtest_engine._process_results([], self.backtest_config, 10.0)

    def test_process_results_success(self) -> None:
        """测试成功处理回测结果"""
        # 创建模拟的策略结果
        mock_strategy = Mock()

        # 模拟分析器结果
        mock_strategy.analyzers.returns.get_analysis.return_value = {
            'rtot': 0.15,  # 总收益率15%
            'rnorm': 0.12  # 年化收益率12%
        }

        mock_strategy.analyzers.sharpe.get_analysis.return_value = {
            'sharperatio': 1.2
        }

        mock_strategy.analyzers.drawdown.get_analysis.return_value = {
            'max': {'drawdown': 8.5}  # 最大回撤8.5%
        }

        mock_strategy.analyzers.trades.get_analysis.return_value = {
            'total': {'total': 10},
            'won': {
                'total': 6,
                'pnl': {'average': 1500.0, 'max': 3000.0}
            },
            'lost': {
                'pnl': {'average': -800.0, 'max': -1200.0}
            }
        }

        mock_strategy.analyzers.sqn.get_analysis.return_value = {
            'sqn': 1.8
        }

        mock_strategy.analyzers.performance.get_analysis.return_value = {
            'sortino_ratio': 1.5,
            'calmar_ratio': 1.1,
            'profit_loss_ratio': 1.875,
            'volatility': 0.18,
            'var_95': -0.025,
            'beta': 1.1,
            'gross_leverage': 0.95,
            'portfolio_values': [100000, 101000, 102000],
            'benchmark_values': [100000, 100500, 101000],
            'dates': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'data_points': 252
        }

        results = [mock_strategy]
        execution_time = 15.5

        # 执行结果处理
        result = self.backtest_engine._process_results(results, self.backtest_config, execution_time)

        # 验证结果
        assert isinstance(result, BacktestResult)
        assert result.config_id == self.backtest_config.id
        assert result.total_return == 0.15
        assert result.annual_return == 0.12
        assert result.max_drawdown == 0.085
        assert result.sharpe_ratio == 1.2
        assert result.trade_count == 10
        assert result.win_rate == 0.6
        assert result.execution_time == execution_time
        assert result.stock_code == self.backtest_config.stock_code
        assert result.start_date == self.backtest_config.start_date
        assert result.end_date == self.backtest_config.end_date

    @patch('src.backtest_engine.services.backtest_engine.FactorDataFeed')
    @patch('src.backtest_engine.services.backtest_engine.FactorStrategy')
    def test_run_backtest_success(self, mock_strategy_class: Mock, mock_data_feed_class: Mock) -> None:
        """测试成功执行回测"""
        # 设置模拟对象
        mock_data_feed = Mock()
        mock_data_feed_class.return_value = mock_data_feed

        # 创建模拟的Cerebro运行结果
        mock_strategy = Mock()
        mock_strategy.analyzers.returns.get_analysis.return_value = {'rtot': 0.1, 'rnorm': 0.08}
        mock_strategy.analyzers.sharpe.get_analysis.return_value = {'sharperatio': 1.0}
        mock_strategy.analyzers.drawdown.get_analysis.return_value = {'max': {'drawdown': 5.0}}
        mock_strategy.analyzers.trades.get_analysis.return_value = {
            'total': {'total': 5},
            'won': {'total': 3, 'pnl': {'average': 1000.0, 'max': 2000.0}},
            'lost': {'pnl': {'average': -500.0, 'max': -800.0}}
        }
        mock_strategy.analyzers.sqn.get_analysis.return_value = {'sqn': 1.5}
        mock_strategy.analyzers.performance.get_analysis.return_value = {
            'sortino_ratio': 1.2,
            'calmar_ratio': 1.0,
            'profit_loss_ratio': 2.0,
            'volatility': 0.15,
            'var_95': -0.02,
            'beta': 1.0,
            'gross_leverage': 0.9,
            'portfolio_values': [100000, 110000],
            'benchmark_values': [100000, 105000],
            'dates': ['2023-01-01', '2023-12-31'],
            'data_points': 252
        }

        # 模拟Cerebro.run()返回结果
        with patch.object(self.backtest_engine.cerebro, 'run', return_value=[mock_strategy]):
            result = self.backtest_engine.run_backtest(self.backtest_config)

        # 验证结果
        assert isinstance(result, BacktestResult)
        assert result.total_return == 0.1
        assert result.sharpe_ratio == 1.0
        assert result.trade_count == 5
        assert result.win_rate == 0.6

        # 验证配置被正确设置和清理
        assert self.backtest_engine._current_config is None

    def test_run_backtest_validation_error(self) -> None:
        """测试回测配置验证错误"""
        # 创建无效配置
        invalid_config = self.backtest_config.model_copy()
        invalid_config.initial_capital = Decimal('0')

        with pytest.raises(ValidationException):
            self.backtest_engine.run_backtest(invalid_config)

    @patch('src.backtest_engine.services.backtest_engine.FactorDataFeed')
    @patch('src.backtest_engine.services.backtest_engine.FactorStrategy')
    def test_run_backtest_execution_error(self, mock_strategy_class: Mock, mock_data_feed_class: Mock) -> None:
        """测试回测执行错误"""
        # 设置模拟对象
        mock_data_feed = Mock()
        mock_data_feed_class.return_value = mock_data_feed

        # 模拟Cerebro.run()抛出异常
        with patch.object(self.backtest_engine.cerebro, 'run', side_effect=Exception("回测执行失败")):
            with pytest.raises(Exception, match="回测执行失败"):
                self.backtest_engine.run_backtest(self.backtest_config)

        # 验证配置被正确清理
        assert self.backtest_engine._current_config is None

    def test_run_backtest_cleanup_on_exception(self) -> None:
        """测试异常情况下的资源清理"""
        # 模拟验证失败
        invalid_config = self.backtest_config.model_copy()
        invalid_config.initial_capital = Decimal('-1000')

        try:
            self.backtest_engine.run_backtest(invalid_config)
        except ValidationException:
            pass

        # 验证配置被正确清理
        assert self.backtest_engine._current_config is None

    def test_logging_integration(self, caplog: pytest.LogCaptureFixture) -> None:
        """测试日志集成"""
        with caplog.at_level(logging.INFO):
            # 测试配置验证日志
            try:
                self.backtest_engine._validate_config(self.backtest_config)
            except Exception:
                pass

            # 测试Cerebro初始化日志
            self.backtest_engine._initialize_cerebro(self.backtest_config)

            # 验证日志记录
            assert "Cerebro引擎初始化完成" in caplog.text

    def test_multiple_backtest_runs(self) -> None:
        """测试多次回测运行"""
        # 验证可以多次运行回测
        for i in range(3):
            config = self.backtest_config.model_copy()
            config.name = f"测试配置_{i}"

            # 验证每次运行前状态正确
            assert self.backtest_engine._current_config is None

            # 验证Cerebro引擎可以重复初始化
            self.backtest_engine._initialize_cerebro(config)
            assert isinstance(self.backtest_engine.cerebro, bt.Cerebro)

    def test_memory_management(self) -> None:
        """测试内存管理"""
        # 验证Cerebro实例在多次初始化后不会累积
        initial_cerebro = self.backtest_engine.cerebro

        self.backtest_engine._initialize_cerebro(self.backtest_config)
        new_cerebro = self.backtest_engine.cerebro

        # 验证Cerebro实例被重新创建
        assert new_cerebro is not initial_cerebro
        assert isinstance(new_cerebro, bt.Cerebro)


class TestBacktestEngineIntegration:
    """BacktestEngine集成测试类"""

    def setup_method(self) -> None:
        """测试前置设置"""
        self.mock_factor_service = Mock(spec=FactorService)
        self.mock_data_client = Mock(spec=TushareClient)
        self.backtest_engine = BacktestEngine(
            factor_service=self.mock_factor_service,
            data_client=self.mock_data_client
        )

    def test_end_to_end_configuration_flow(self) -> None:
        """测试端到端配置流程"""
        # 创建完整的回测配置
        factor_config = BacktestFactorConfig(
            combination_id="integration_test",
            description="集成测试因子组合",
            factors=[
                FactorItem(factor_name="PE", factor_type="fundamental", weight=0.5),
                FactorItem(factor_name="RSI", factor_type="technical", weight=0.5)
            ]
        )

        config = BacktestConfig(
            name="集成测试配置",
            stock_code="000001.SZ",
            start_date="2023-01-01",
            end_date="2023-06-30",
            factor_combination=factor_config,
            initial_capital=Decimal('50000'),
            transaction_cost=0.002,
            slippage=0.0002,
            buy_threshold=0.7,
            sell_threshold=0.3,
            optimization_result_id="integration_test_001"
        )

        # 执行配置流程
        self.backtest_engine._validate_config(config)
        self.backtest_engine._initialize_cerebro(config)

        # 验证配置结果
        assert self.backtest_engine.cerebro.broker.getcash() == 50000.0

        # 验证可以获取引擎信息
        info = self.backtest_engine.get_cerebro_info()
        assert info["status"] == "initialized"
        assert info["cash"] == 50000.0
