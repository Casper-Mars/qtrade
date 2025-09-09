"""回测引擎测试工具模块

提供测试所需的Mock对象、测试数据和辅助方法
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pandas as pd
import pytest

from src.backtest_engine.models.backtest_models import (
    BacktestConfig,
    BacktestFactorConfig,
    BacktestMode,
    BacktestResult,
    Factor,
    FactorItem,
)
from src.backtest_engine.models.factor_combination import FactorConfig, FactorType
from decimal import Decimal


class MockTushareClient:
    """Mock Tushare客户端"""

    def __init__(self) -> None:
        self.daily_data = self._create_mock_daily_data()

    async def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """模拟获取日线数据"""
        return self.daily_data.copy()

    def _create_mock_daily_data(self) -> pd.DataFrame:
        """创建模拟日线数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        # 过滤工作日
        dates = dates[dates.weekday < 5]
        
        data = {
            'trade_date': dates.strftime('%Y%m%d'),
            'ts_code': ['000001.SZ'] * len(dates),
            'open': 10.0 + (dates.dayofyear % 50) * 0.1,
            'high': 10.5 + (dates.dayofyear % 50) * 0.1,
            'low': 9.5 + (dates.dayofyear % 50) * 0.1,
            'close': 10.0 + (dates.dayofyear % 50) * 0.1,
            'vol': 1000000 + (dates.dayofyear % 100) * 10000,
            'amount': 100000000 + (dates.dayofyear % 100) * 1000000,
        }
        
        return pd.DataFrame(data)


class MockFactorService:
    """Mock因子服务"""

    def __init__(self) -> None:
        self.factor_data = self._create_mock_factor_data()

    def get_factor_data(self, stock_code: str, start_date: str, end_date: str, 
                       factor_names: List[str]) -> Dict[str, Any]:
        """模拟获取因子数据"""
        return self.factor_data.copy()

    def _create_mock_factor_data(self) -> Dict[str, Any]:
        """创建模拟因子数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        dates = dates[dates.weekday < 5]
        
        return {
            'momentum': [0.1 + (i % 10) * 0.05 for i in range(len(dates))],
            'value': [0.2 + (i % 8) * 0.04 for i in range(len(dates))],
            'quality': [0.3 + (i % 6) * 0.03 for i in range(len(dates))],
            'dates': dates.strftime('%Y-%m-%d').tolist()
        }


class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    def create_backtest_config(
        stock_code: str = "000001.SZ",
        start_date: str = "2023-01-01",
        end_date: str = "2023-12-31",
        initial_capital: float = 1000000.0,
        **kwargs: Any
    ) -> BacktestConfig:
        """创建回测配置"""
        factor_combination = TestDataFactory.create_factor_combination()
        
        return BacktestConfig(
            id=uuid4(),
            name=kwargs.get('name', 'test_backtest'),
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal(str(initial_capital)),
            factor_combination=factor_combination,
            optimization_result_id=kwargs.get('optimization_result_id'),
            buy_threshold=kwargs.get('buy_threshold', 0.6),
            sell_threshold=kwargs.get('sell_threshold', 0.4),
            transaction_cost=kwargs.get('transaction_cost', 0.001),
            slippage=kwargs.get('slippage', 0.001),
            backtest_mode=kwargs.get('backtest_mode', BacktestMode.HISTORICAL_SIMULATION)
        )

    @staticmethod
    def create_factor_combination() -> BacktestFactorConfig:
        """创建因子组合配置"""
        factors = [
            FactorItem(factor_name="momentum", factor_type="technical", weight=0.4),
            FactorItem(factor_name="value", factor_type="fundamental", weight=0.3),
            FactorItem(factor_name="quality", factor_type="fundamental", weight=0.3)
        ]
        
        return BacktestFactorConfig(
            combination_id="test_combination",
            factors=factors,
            description="测试因子组合"
        )

    @staticmethod
    def create_backtest_result(**kwargs: Any) -> BacktestResult:
        """创建回测结果"""
        config = TestDataFactory.create_backtest_config()
        
        return BacktestResult(
            config_id=config.id,
            factor_combination=config.factor_combination,
            start_date=config.start_date,
            end_date=config.end_date,
            stock_code=config.stock_code,
            backtest_mode=config.backtest_mode,
            
            # 核心绩效指标
            total_return=kwargs.get('total_return', 0.15),
            annual_return=kwargs.get('annual_return', 0.15),
            max_drawdown=kwargs.get('max_drawdown', -0.05),
            sharpe_ratio=kwargs.get('sharpe_ratio', 1.2),
            sortino_ratio=kwargs.get('sortino_ratio', 1.5),
            calmar_ratio=kwargs.get('calmar_ratio', 3.0),
            
            # 交易统计
            trade_count=kwargs.get('trade_count', 50),
            win_rate=kwargs.get('win_rate', 0.6),
            avg_profit=kwargs.get('avg_profit', 1000.0),
            avg_loss=kwargs.get('avg_loss', -500.0),
            profit_loss_ratio=kwargs.get('profit_loss_ratio', 2.0),
            largest_win=kwargs.get('largest_win', 5000.0),
            largest_loss=kwargs.get('largest_loss', -2000.0),
            
            # 风险指标
            volatility=kwargs.get('volatility', 0.12),
            var_95=kwargs.get('var_95', -0.02),
            beta=kwargs.get('beta', 1.1),
            
            # Backtrader特有指标
            sqn=kwargs.get('sqn', 1.8),
            gross_leverage=kwargs.get('gross_leverage', 1.0),
            
            # 资金曲线数据
            portfolio_value=kwargs.get('portfolio_value', [1000000, 1050000, 1100000]),
            benchmark_value=kwargs.get('benchmark_value', [1000000, 1030000, 1060000]),
            dates=kwargs.get('dates', ['2023-01-01', '2023-06-01', '2023-12-31']),
            
            # 执行信息
            execution_time=kwargs.get('execution_time', 5.2),
            data_points=kwargs.get('data_points', 250),
            completed_at=kwargs.get('completed_at', datetime.now())
        )


class MockBacktraderStrategy:
    """Mock Backtrader策略"""
    
    def __init__(self) -> None:
        self.analyzers = MockAnalyzers()


class MockAnalyzers:
    """Mock分析器集合"""
    
    def __init__(self) -> None:
        self.returns = MockReturnsAnalyzer()
        self.sharpe = MockSharpeAnalyzer()
        self.drawdown = MockDrawdownAnalyzer()
        self.trades = MockTradesAnalyzer()
        self.sqn = MockSQNAnalyzer()
        self.performance = MockPerformanceAnalyzer()


class MockReturnsAnalyzer:
    """Mock收益率分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'rtot': 0.15,  # 总收益率
            'rnorm': 0.15,  # 年化收益率
        }


class MockSharpeAnalyzer:
    """Mock夏普比率分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'sharperatio': 1.2
        }


class MockDrawdownAnalyzer:
    """Mock回撤分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'max': {
                'drawdown': 5.0  # 百分比形式
            }
        }


class MockTradesAnalyzer:
    """Mock交易分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'total': {'total': 50},
            'won': {
                'total': 30,
                'pnl': {
                    'average': 1000.0,
                    'max': 5000.0
                }
            },
            'lost': {
                'total': 20,
                'pnl': {
                    'average': -500.0,
                    'max': -2000.0
                }
            }
        }


class MockSQNAnalyzer:
    """Mock SQN分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'sqn': 1.8
        }


class MockPerformanceAnalyzer:
    """Mock性能分析器"""
    
    def get_analysis(self) -> Dict[str, Any]:
        return {
            'sortino_ratio': 1.5,
            'calmar_ratio': 3.0,
            'profit_loss_ratio': 2.0,
            'volatility': 0.12,
            'var_95': -0.02,
            'beta': 1.1,
            'gross_leverage': 1.0,
            'portfolio_values': [1000000, 1050000, 1100000],
            'benchmark_values': [1000000, 1030000, 1060000],
            'dates': ['2023-01-01', '2023-06-01', '2023-12-31'],
            'data_points': 250
        }


class AsyncTestCase:
    """异步测试基类"""
    
    @staticmethod
    def run_async(coro: Any) -> Any:
        """运行异步协程"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


# 常用的测试装饰器和工具函数
def async_test(func: Callable) -> Callable:
    """异步测试装饰器"""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return AsyncTestCase.run_async(func(*args, **kwargs))
    return wrapper


def create_mock_cerebro() -> Mock:
    """创建Mock Cerebro对象"""
    cerebro = Mock()
    cerebro.broker = Mock()
    cerebro.broker.setcash = Mock()
    cerebro.broker.setcommission = Mock()
    cerebro.broker.set_slippage_perc = Mock()
    cerebro.broker.getcash = Mock(return_value=1000000.0)
    cerebro.broker.getvalue = Mock(return_value=1150000.0)
    cerebro.adddata = Mock()
    cerebro.addstrategy = Mock()
    cerebro.addanalyzer = Mock()
    cerebro.addsizer = Mock()
    cerebro.run = Mock(return_value=[MockBacktraderStrategy()])
    cerebro.datas = []
    cerebro.strats = []
    cerebro.analyzers = []
    return cerebro