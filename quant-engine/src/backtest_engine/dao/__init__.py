"""回测引擎数据访问层模块

本模块提供回测引擎的数据访问功能，包括：
- 基础DAO类
- 回测任务数据访问
- 因子组合数据访问
- 回测结果数据访问
- 缓存管理
"""

from . import base, cache
from .backtest_dao import BacktestDAO
from .factor_combination_dao import FactorCombinationDAO

__all__ = [
    "base",
    "cache",
    "BacktestDAO",
    "FactorCombinationDAO",
]
