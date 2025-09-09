"""Backtrader分析器模块单元测试

测试BacktraderAnalyzer类及其相关分析器的功能
"""

from datetime import date, datetime
from unittest.mock import Mock, patch
from uuid import UUID

import backtrader as bt
import pytest

from src.backtest_engine.models.backtest_models import (
    BacktestFactorConfig,
    BacktestMode,
    BacktestResult,
)
from src.backtest_engine.services.backtrader_analyzer import (
    BacktraderAnalyzer,
    CalmarRatioAnalyzer,
    PortfolioValueAnalyzer,
)


class TestBacktraderAnalyzer:
    """BacktraderAnalyzer类测试"""

    def setup_method(self) -> None:
        """测试前置设置"""
        self.analyzer = BacktraderAnalyzer()

    def test_init(self) -> None:
        """测试初始化"""
        assert isinstance(self.analyzer.analyzers, dict)
        assert isinstance(self.analyzer.custom_data, dict)
        assert len(self.analyzer.analyzers) == 0
        assert len(self.analyzer.custom_data) == 0

    def test_add_analyzers(self) -> None:
        """测试添加分析器"""
        # 创建mock cerebro
        mock_cerebro = Mock(spec=bt.Cerebro)

        # 执行添加分析器
        self.analyzer.add_analyzers(mock_cerebro)

        # 验证addanalyzer被调用了正确的次数
        assert mock_cerebro.addanalyzer.call_count == 12

        # 验证添加了正确的分析器
        calls = mock_cerebro.addanalyzer.call_args_list
        analyzer_names = [call[1]['_name'] for call in calls]

        expected_names = [
            'returns', 'sharpe', 'drawdown', 'trades',
            'annual_return', 'time_return', 'vwr', 'sqn',
            'transactions', 'positions', 'calmar', 'portfolio_value'
        ]

        for name in expected_names:
            assert name in analyzer_names

    def test_add_analyzers_exception(self) -> None:
        """测试添加分析器异常处理"""
        mock_cerebro = Mock(spec=bt.Cerebro)
        mock_cerebro.addanalyzer.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            self.analyzer.add_analyzers(mock_cerebro)

    def test_extract_results_empty_strategy(self) -> None:
        """测试提取空策略结果"""
        with pytest.raises(ValueError, match="策略结果为空"):
            self.analyzer.extract_results([])

    def test_extract_results_success(self) -> None:
        """测试成功提取回测结果"""
        # 创建mock策略和分析器
        mock_strategy = self._create_mock_strategy()

        # 执行提取结果
        result = self.analyzer.extract_results([mock_strategy])

        # 验证结果类型
        assert isinstance(result, BacktestResult)

        # 验证基础字段
        assert isinstance(result.config_id, UUID)
        assert isinstance(result.factor_combination, BacktestFactorConfig)
        assert result.backtest_mode == BacktestMode.HISTORICAL_SIMULATION

        # 验证绩效指标
        assert result.total_return == 0.15
        assert result.annual_return == 0.10  # 取最后一年（2024）的收益率
        assert result.sharpe_ratio == 1.5
        assert result.max_drawdown == 0.08

        # 验证交易统计
        assert result.trade_count == 10
        assert result.win_rate == 0.6  # 胜率为小数格式（6/10 = 0.6）

        # 验证时间戳
        assert isinstance(result.completed_at, datetime)

    def test_extract_performance_metrics(self) -> None:
        """测试提取绩效指标"""
        mock_analyzers = self._create_mock_analyzers()

        metrics = self.analyzer._extract_performance_metrics(mock_analyzers)

        assert metrics['total_return'] == 0.15
        assert metrics['annual_return'] == 0.10  # 取最后一年（2024）的收益率
        assert metrics['sharpe_ratio'] == 1.5

    def test_extract_risk_metrics(self) -> None:
        """测试提取风险指标"""
        mock_analyzers = self._create_mock_analyzers()

        metrics = self.analyzer._extract_risk_metrics(mock_analyzers)

        assert metrics['max_drawdown'] == 0.08
        assert 'volatility' in metrics
        assert metrics['beta'] == 1.0  # 默认值
        assert metrics['alpha'] == 0.0  # 默认值

    def test_extract_trade_statistics(self) -> None:
        """测试提取交易统计"""
        mock_analyzers = self._create_mock_analyzers()

        stats = self.analyzer._extract_trade_statistics(mock_analyzers)

        assert stats['trade_count'] == 10
        assert stats['win_rate'] == 0.6  # 胜率为小数格式
        assert 'avg_win' in stats
        assert 'avg_loss' in stats
        assert 'profit_factor' in stats

    def test_extract_backtrader_metrics(self) -> None:
        """测试提取Backtrader指标"""
        mock_analyzers = self._create_mock_analyzers()

        metrics = self.analyzer._extract_backtrader_metrics(mock_analyzers)

        assert metrics['calmar_ratio'] == 2.0
        assert metrics['sqn'] == 1.8
        assert metrics['largest_win'] == 5000.0
        assert metrics['largest_loss'] == 2000.0
        assert metrics['gross_leverage'] == 1.0

    def test_extract_portfolio_data(self) -> None:
        """测试提取资金曲线数据"""
        mock_analyzers = self._create_mock_analyzers()

        data = self.analyzer._extract_portfolio_data(mock_analyzers)

        assert 'portfolio_value' in data
        assert 'benchmark_value' in data
        assert 'dates' in data
        assert len(data['dates']) == 3
        assert len(data['portfolio_value']) == 3
        assert len(data['benchmark_value']) == 3

    def _create_mock_strategy(self) -> Mock:
        """创建mock策略对象"""
        mock_strategy = Mock(spec=bt.Strategy)
        mock_strategy.analyzers = self._create_mock_analyzers()
        return mock_strategy

    def _create_mock_analyzers(self) -> Mock:
        """创建mock分析器对象"""
        mock_analyzers = Mock()

        # Returns分析器
        mock_returns = Mock()
        mock_returns.get_analysis.return_value = {'rtot': 0.15}
        mock_analyzers.returns = mock_returns

        # Annual return分析器
        mock_annual = Mock()
        mock_annual.get_analysis.return_value = {2023: 0.12, 2024: 0.10}
        mock_analyzers.annual_return = mock_annual

        # Sharpe分析器
        mock_sharpe = Mock()
        mock_sharpe.get_analysis.return_value = {'sharperatio': 1.5}
        mock_analyzers.sharpe = mock_sharpe

        # Drawdown分析器
        mock_drawdown = Mock()
        mock_drawdown.get_analysis.return_value = {
            'max': {'drawdown': -0.08}
        }
        mock_analyzers.drawdown = mock_drawdown

        # Time return分析器
        mock_time_return = Mock()
        mock_time_return.get_analysis.return_value = {
            date(2023, 1, 1): 0.01,
            date(2023, 1, 2): -0.005,
            date(2023, 1, 3): 0.015
        }
        mock_analyzers.time_return = mock_time_return

        # VWR分析器
        mock_vwr = Mock()
        mock_vwr.get_analysis.return_value = {'vwr': 0.25}
        mock_analyzers.vwr = mock_vwr

        # Trades分析器
        mock_trades = Mock()
        mock_trades.get_analysis.return_value = {
            'total': {'total': 10},
            'won': {
                'total': 6,
                'pnl': {'total': 15000.0, 'average': 2500.0, 'max': 5000.0}
            },
            'lost': {
                'total': 4,
                'pnl': {'total': -8000.0, 'average': -2000.0, 'max': -2000.0}
            }
        }
        mock_analyzers.trades = mock_trades

        # Calmar分析器
        mock_calmar = Mock()
        mock_calmar.get_analysis.return_value = {'calmar_ratio': 2.0}
        mock_analyzers.calmar = mock_calmar

        # SQN分析器
        mock_sqn = Mock()
        mock_sqn.get_analysis.return_value = {'sqn': 1.8}
        mock_analyzers.sqn = mock_sqn

        # Portfolio value分析器
        mock_portfolio = Mock()
        mock_portfolio.get_analysis.return_value = {
            date(2023, 1, 1): 100000.0,
            date(2023, 1, 2): 101000.0,
            date(2023, 1, 3): 102500.0
        }
        mock_analyzers.portfolio_value = mock_portfolio

        return mock_analyzers


class TestCalmarRatioAnalyzer:
    """CalmarRatioAnalyzer类测试"""

    def setup_method(self) -> None:
        """测试前置设置"""
        self.analyzer = CalmarRatioAnalyzer()

        # 创建mock策略
        self.mock_strategy = Mock()
        self.mock_broker = Mock()
        self.mock_datetime = Mock()
        self.mock_strategy.broker = self.mock_broker
        self.mock_strategy.datetime = self.mock_datetime
        self.mock_datetime.date.return_value = date(2023, 1, 1)

        # 手动调用__init__来设置strategy属性
        self.analyzer.strategy = self.mock_strategy

    def test_init(self) -> None:
        """测试初始化"""
        assert isinstance(self.analyzer.returns, list)
        assert len(self.analyzer.returns) == 0
        assert self.analyzer.peak == 0
        assert self.analyzer.max_dd == 0

    def test_next_first_call(self) -> None:
        """测试第一次调用next"""
        self.mock_broker.getvalue.return_value = 100000.0

        self.analyzer.next()

        assert len(self.analyzer.returns) == 1
        assert self.analyzer.returns[0] == 0.0
        assert self.analyzer.peak == 100000.0

    def test_next_subsequent_calls(self) -> None:
        """测试后续调用next"""
        # 第一次调用
        self.mock_broker.getvalue.return_value = 100000.0
        self.analyzer.next()

        # 第二次调用 - 上涨
        self.mock_broker.getvalue.return_value = 105000.0
        self.analyzer.next()

        assert len(self.analyzer.returns) == 2
        assert self.analyzer.returns[1] == 0.05  # 5%收益
        assert self.analyzer.peak == 105000.0

        # 第三次调用 - 下跌
        self.mock_broker.getvalue.return_value = 95000.0
        self.analyzer.next()

        assert len(self.analyzer.returns) == 3
        assert abs(self.analyzer.returns[2] - (-0.095238)) < 0.001  # 约-9.52%
        assert self.analyzer.max_dd > 0  # 应该有回撤

    def test_get_analysis_empty_returns(self) -> None:
        """测试空收益率的分析结果"""
        result = self.analyzer.get_analysis()
        assert result['calmar_ratio'] == 0.0

    def test_get_analysis_zero_drawdown(self) -> None:
        """测试零回撤的分析结果"""
        self.analyzer.returns = [0.01, 0.02, 0.015]
        self.analyzer.max_dd = 0.0

        result = self.analyzer.get_analysis()
        assert result['calmar_ratio'] == 0.0

    def test_get_analysis_normal_case(self) -> None:
        """测试正常情况的分析结果"""
        self.analyzer.returns = [0.01, 0.02, -0.005, 0.015]  # 4天数据
        self.analyzer.max_dd = 0.1  # 10%最大回撤

        result = self.analyzer.get_analysis()

        # 验证Calmar比率计算
        total_return = sum(self.analyzer.returns)  # 0.04
        annual_return = total_return * (252 / 4)  # 年化
        expected_calmar = annual_return / 0.1

        assert abs(result['calmar_ratio'] - expected_calmar) < 0.001


class TestPortfolioValueAnalyzer:
    """PortfolioValueAnalyzer类测试"""

    def setup_method(self) -> None:
        """测试前置设置"""
        self.analyzer = PortfolioValueAnalyzer()

        # 创建mock策略
        self.mock_strategy = Mock()
        self.mock_broker = Mock()
        self.mock_datetime = Mock()

        self.mock_strategy.broker = self.mock_broker
        self.mock_strategy.datetime = self.mock_datetime

        self.analyzer.strategy = self.mock_strategy

    def test_init(self) -> None:
        """测试初始化"""
        assert isinstance(self.analyzer.portfolio_values, dict)
        assert len(self.analyzer.portfolio_values) == 0

    def test_next(self) -> None:
        """测试next方法"""
        # 设置mock返回值
        test_date = date(2023, 1, 1)
        test_value = 105000.0

        self.mock_datetime.date.return_value = test_date
        self.mock_broker.getvalue.return_value = test_value

        # 执行next
        self.analyzer.next()

        # 验证结果
        assert len(self.analyzer.portfolio_values) == 1
        assert self.analyzer.portfolio_values[test_date] == test_value

    def test_next_multiple_days(self) -> None:
        """测试多天数据记录"""
        test_data = [
            (date(2023, 1, 1), 100000.0),
            (date(2023, 1, 2), 101000.0),
            (date(2023, 1, 3), 99500.0)
        ]

        for test_date, test_value in test_data:
            self.mock_datetime.date.return_value = test_date
            self.mock_broker.getvalue.return_value = test_value
            self.analyzer.next()

        # 验证结果
        assert len(self.analyzer.portfolio_values) == 3
        for test_date, test_value in test_data:
            assert self.analyzer.portfolio_values[test_date] == test_value

    def test_get_analysis(self) -> None:
        """测试get_analysis方法"""
        # 添加测试数据
        test_data = {
            date(2023, 1, 1): 100000.0,
            date(2023, 1, 2): 101000.0
        }
        self.analyzer.portfolio_values = test_data

        # 获取分析结果
        result = self.analyzer.get_analysis()

        # 验证结果
        assert result == test_data
        assert len(result) == 2
        assert result[date(2023, 1, 1)] == 100000.0
        assert result[date(2023, 1, 2)] == 101000.0


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self) -> None:
        """测试完整工作流程"""
        # 创建分析器
        analyzer = BacktraderAnalyzer()

        # 创建mock cerebro和策略
        mock_cerebro = Mock(spec=bt.Cerebro)
        mock_strategy = Mock(spec=bt.Strategy)
        mock_strategy.analyzers = Mock()

        # 设置基本的分析器返回值
        mock_strategy.analyzers.returns = Mock()
        mock_strategy.analyzers.returns.get_analysis.return_value = {'rtot': 0.1}

        mock_strategy.analyzers.sharpe = Mock()
        mock_strategy.analyzers.sharpe.get_analysis.return_value = {'sharperatio': 1.2}

        mock_strategy.analyzers.drawdown = Mock()
        mock_strategy.analyzers.drawdown.get_analysis.return_value = {
            'max': {'drawdown': -0.05}
        }

        mock_strategy.analyzers.trades = Mock()
        mock_strategy.analyzers.trades.get_analysis.return_value = {
            'total': {'total': 5},
            'won': {'total': 3, 'pnl': {'total': 10000.0, 'average': 3333.33}},
            'lost': {'total': 2, 'pnl': {'total': -4000.0, 'average': -2000.0}}
        }

        # 执行完整流程
        analyzer.add_analyzers(mock_cerebro)
        result = analyzer.extract_results([mock_strategy])

        # 验证结果
        assert isinstance(result, BacktestResult)
        assert result.total_return == 0.1
        assert result.sharpe_ratio == 1.2
        assert result.max_drawdown == 0.05
        assert result.trade_count == 5
        assert result.win_rate == 60.0

    @patch('src.backtest_engine.services.backtrader_analyzer.logger')
    def test_error_handling(self, mock_logger: Mock) -> None:
        """测试错误处理"""
        analyzer = BacktraderAnalyzer()

        # 测试extract_results异常处理
        mock_strategy = Mock()
        mock_strategy.analyzers = Mock()
        mock_strategy.analyzers.returns = Mock()
        mock_strategy.analyzers.returns.get_analysis.side_effect = Exception("Test error")

        # 应该不会抛出异常，而是记录日志并返回默认值
        result = analyzer.extract_results([mock_strategy])

        # 验证日志被调用
        assert mock_logger.error.called

        # 验证返回了有效的结果对象
        assert isinstance(result, BacktestResult)
