"""BacktraderAnalyzer单元测试模块

测试BacktraderAnalyzer类的所有功能，包括：
- 分析器添加和配置
- 回测结果提取
- 性能指标计算
- 风险指标计算
- 交易统计计算
- 异常处理
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

from src.backtest_engine.services.backtrader_analyzer import BacktraderAnalyzer
from src.backtest_engine.models.backtest_models import BacktestResult
from tests.test_backtest_engine.test_utils import TestDataFactory


class TestBacktraderAnalyzer:
    """BacktraderAnalyzer测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.analyzer = BacktraderAnalyzer()
        self.mock_cerebro = Mock()
        self.test_data = TestDataFactory()
    
    def test_init(self):
        """测试初始化"""
        analyzer = BacktraderAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'add_analyzers')
        assert hasattr(analyzer, 'extract_results')
    
    def test_add_analyzers_success(self):
        """测试成功添加分析器"""
        # 准备测试数据
        mock_cerebro = Mock()
        
        # 执行测试
        self.analyzer.add_analyzers(mock_cerebro)
        
        # 验证结果
        assert mock_cerebro.addanalyzer.call_count >= 5  # 至少添加5个分析器
        
        # 验证添加的分析器类型
        call_args_list = mock_cerebro.addanalyzer.call_args_list
        analyzer_names = []
        for call in call_args_list:
            if len(call[0]) > 0:
                analyzer_names.append(call[0][0].__name__)
        
        expected_analyzers = [
            'Returns', 'SharpeRatio', 'DrawDown', 
            'TradeAnalyzer', 'SQN'
        ]
        
        for expected in expected_analyzers:
            assert any(expected in name for name in analyzer_names)
    
    def test_add_analyzers_with_exception(self):
        """测试添加分析器时发生异常"""
        # 准备测试数据
        mock_cerebro = Mock()
        mock_cerebro.addanalyzer.side_effect = Exception("添加分析器失败")
        
        # 执行测试并验证异常
        with pytest.raises(Exception) as exc_info:
            self.analyzer.add_analyzers(mock_cerebro)
        
        assert "添加分析器失败" in str(exc_info.value)
    
    def test_extract_results_success(self):
        """测试成功提取回测结果"""
        # 准备测试数据
        mock_strategy = self._create_mock_strategy_with_analyzers()
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # 执行测试
        result = self.analyzer.extract_results(mock_strategy, start_date, end_date)
        
        # 验证结果
        assert isinstance(result, BacktestResult)
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert result.total_return > 0
        assert result.annual_return > 0
        assert result.sharpe_ratio > 0
        assert result.max_drawdown < 0
        assert result.total_trades > 0
        assert result.win_rate >= 0
        assert result.profit_factor > 0
    
    def test_extract_results_with_zero_trades(self):
        """测试无交易情况下的结果提取"""
        # 准备测试数据
        mock_strategy = self._create_mock_strategy_with_no_trades()
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # 执行测试
        result = self.analyzer.extract_results(mock_strategy, start_date, end_date)
        
        # 验证结果
        assert isinstance(result, BacktestResult)
        assert result.total_trades == 0
        assert result.win_rate == 0.0
        assert result.profit_factor == 0.0
        assert result.avg_trade_return == 0.0
    
    def test_extract_results_with_missing_analyzers(self):
        """测试缺少分析器时的结果提取"""
        # 准备测试数据
        mock_strategy = Mock()
        mock_strategy.analyzers = Mock()
        # 模拟缺少某些分析器
        mock_strategy.analyzers.returns = None
        mock_strategy.analyzers.sharpe = None
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # 执行测试并验证异常
        with pytest.raises(AttributeError):
            self.analyzer.extract_results(mock_strategy, start_date, end_date)
    
    def test_extract_performance_metrics_success(self):
        """测试成功提取性能指标"""
        # 准备测试数据
        mock_analyzers = self._create_mock_analyzers()
        
        # 执行测试
        metrics = self.analyzer._extract_performance_metrics(mock_analyzers)
        
        # 验证结果
        assert 'total_return' in metrics
        assert 'annual_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert metrics['total_return'] == 0.15
        assert metrics['annual_return'] == 0.12
        assert metrics['sharpe_ratio'] == 1.5
    
    def test_extract_performance_metrics_with_none_values(self):
        """测试性能指标为None的情况"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.returns.get_analysis.return_value = {}
        mock_analyzers.sharpe.get_analysis.return_value = {'sharperatio': None}
        
        # 执行测试
        metrics = self.analyzer._extract_performance_metrics(mock_analyzers)
        
        # 验证结果
        assert metrics['total_return'] == 0.0
        assert metrics['annual_return'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0
    
    def test_extract_risk_metrics_success(self):
        """测试成功提取风险指标"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.drawdown.get_analysis.return_value = {
            'max': {'drawdown': -0.08}
        }
        
        # 执行测试
        metrics = self.analyzer._extract_risk_metrics(mock_analyzers)
        
        # 验证结果
        assert 'max_drawdown' in metrics
        assert metrics['max_drawdown'] == -0.08
    
    def test_extract_risk_metrics_with_missing_data(self):
        """测试风险指标数据缺失的情况"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.drawdown.get_analysis.return_value = {}
        
        # 执行测试
        metrics = self.analyzer._extract_risk_metrics(mock_analyzers)
        
        # 验证结果
        assert metrics['max_drawdown'] == 0.0
    
    def test_extract_trade_metrics_success(self):
        """测试成功提取交易指标"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.trades.get_analysis.return_value = {
            'total': {'total': 100},
            'won': {'total': 60},
            'lost': {'total': 40},
            'pnl': {
                'gross': {'total': 15000.0, 'average': 150.0},
                'net': {'total': 14500.0, 'average': 145.0}
            }
        }
        
        # 执行测试
        metrics = self.analyzer._extract_trade_metrics(mock_analyzers)
        
        # 验证结果
        assert metrics['total_trades'] == 100
        assert metrics['win_rate'] == 0.6
        assert metrics['profit_factor'] == 1.0  # 默认值，因为没有亏损数据
        assert metrics['avg_trade_return'] == 145.0
    
    def test_extract_trade_metrics_with_zero_trades(self):
        """测试零交易情况下的交易指标提取"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.trades.get_analysis.return_value = {
            'total': {'total': 0}
        }
        
        # 执行测试
        metrics = self.analyzer._extract_trade_metrics(mock_analyzers)
        
        # 验证结果
        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0
        assert metrics['profit_factor'] == 0.0
        assert metrics['avg_trade_return'] == 0.0
    
    def test_extract_trade_metrics_with_profit_factor_calculation(self):
        """测试盈亏比计算"""
        # 准备测试数据
        mock_analyzers = Mock()
        mock_analyzers.trades.get_analysis.return_value = {
            'total': {'total': 100},
            'won': {'total': 60, 'pnl': {'total': 12000.0}},
            'lost': {'total': 40, 'pnl': {'total': -8000.0}},
            'pnl': {
                'gross': {'total': 4000.0, 'average': 40.0},
                'net': {'total': 3500.0, 'average': 35.0}
            }
        }
        
        # 执行测试
        metrics = self.analyzer._extract_trade_metrics(mock_analyzers)
        
        # 验证结果
        assert metrics['total_trades'] == 100
        assert metrics['win_rate'] == 0.6
        assert metrics['profit_factor'] == 1.5  # 12000 / 8000
        assert metrics['avg_trade_return'] == 35.0
    
    def test_extract_results_with_invalid_dates(self):
        """测试无效日期参数"""
        # 准备测试数据
        mock_strategy = self._create_mock_strategy_with_analyzers()
        
        # 测试开始日期晚于结束日期
        start_date = date(2023, 12, 31)
        end_date = date(2023, 1, 1)
        
        # 执行测试并验证异常
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.extract_results(mock_strategy, start_date, end_date)
        
        assert "开始日期不能晚于结束日期" in str(exc_info.value)
    
    def test_extract_results_with_none_strategy(self):
        """测试策略为None的情况"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        # 执行测试并验证异常
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.extract_results(None, start_date, end_date)
        
        assert "策略对象不能为空" in str(exc_info.value)
    
    def _create_mock_strategy_with_analyzers(self):
        """创建带有分析器的模拟策略"""
        mock_strategy = Mock()
        mock_strategy.analyzers = self._create_mock_analyzers()
        return mock_strategy
    
    def _create_mock_strategy_with_no_trades(self):
        """创建无交易的模拟策略"""
        mock_strategy = Mock()
        mock_analyzers = Mock()
        
        # 模拟无交易的分析器结果
        mock_analyzers.returns.get_analysis.return_value = {
            'rtot': 0.0, 'rnorm': 0.0
        }
        mock_analyzers.sharpe.get_analysis.return_value = {
            'sharperatio': 0.0
        }
        mock_analyzers.drawdown.get_analysis.return_value = {
            'max': {'drawdown': 0.0}
        }
        mock_analyzers.trades.get_analysis.return_value = {
            'total': {'total': 0}
        }
        mock_analyzers.sqn.get_analysis.return_value = {
            'sqn': 0.0
        }
        
        mock_strategy.analyzers = mock_analyzers
        return mock_strategy
    
    def _create_mock_analyzers(self):
        """创建模拟分析器"""
        mock_analyzers = Mock()
        
        # 模拟收益率分析器
        mock_analyzers.returns.get_analysis.return_value = {
            'rtot': 0.15,  # 总收益率15%
            'rnorm': 0.12  # 年化收益率12%
        }
        
        # 模拟夏普比率分析器
        mock_analyzers.sharpe.get_analysis.return_value = {
            'sharperatio': 1.5
        }
        
        # 模拟回撤分析器
        mock_analyzers.drawdown.get_analysis.return_value = {
            'max': {'drawdown': -0.08}  # 最大回撤8%
        }
        
        # 模拟交易分析器
        mock_analyzers.trades.get_analysis.return_value = {
            'total': {'total': 100},
            'won': {'total': 60, 'pnl': {'total': 12000.0}},
            'lost': {'total': 40, 'pnl': {'total': -8000.0}},
            'pnl': {
                'gross': {'total': 4000.0, 'average': 40.0},
                'net': {'total': 3500.0, 'average': 35.0}
            }
        }
        
        # 模拟SQN分析器
        mock_analyzers.sqn.get_analysis.return_value = {
            'sqn': 2.5
        }
        
        return mock_analyzers
    
    def test_edge_cases_and_boundary_conditions(self):
        """测试边界条件和特殊情况"""
        # 测试极小的收益率
        mock_analyzers = Mock()
        mock_analyzers.returns.get_analysis.return_value = {
            'rtot': 0.0001,  # 极小收益率
            'rnorm': 0.0001
        }
        
        metrics = self.analyzer._extract_performance_metrics(mock_analyzers)
        assert metrics['total_return'] == 0.0001
        assert metrics['annual_return'] == 0.0001
        
        # 测试负收益率
        mock_analyzers.returns.get_analysis.return_value = {
            'rtot': -0.05,  # 负收益率
            'rnorm': -0.03
        }
        
        metrics = self.analyzer._extract_performance_metrics(mock_analyzers)
        assert metrics['total_return'] == -0.05
        assert metrics['annual_return'] == -0.03
    
    def test_analyzer_error_handling(self):
        """测试分析器错误处理"""
        # 测试分析器方法调用异常
        mock_analyzers = Mock()
        mock_analyzers.returns.get_analysis.side_effect = Exception("分析器错误")
        
        with pytest.raises(Exception) as exc_info:
            self.analyzer._extract_performance_metrics(mock_analyzers)
        
        assert "分析器错误" in str(exc_info.value)