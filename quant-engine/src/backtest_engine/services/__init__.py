"""回测引擎服务层模块

包含基于Backtrader框架的回测引擎核心服务组件：
- BacktestEngine：回测引擎核心
- FactorDataFeed：因子数据源
- FactorStrategy：因子策略
- BacktraderAnalyzer：回测结果分析器
"""

from .backtest_engine import BacktestEngine
from .backtrader_analyzer import BacktraderAnalyzer
from .factor_data_feed import FactorDataFeed
from .factor_strategy import FactorStrategy

__all__ = [
    "BacktestEngine",
    "FactorDataFeed",
    "FactorStrategy",
    "BacktraderAnalyzer",
]
