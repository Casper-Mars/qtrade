"""回测引擎服务层模块

包含回测引擎的核心服务组件：
- 数据回放器：历史数据回放和验证
- 因子组合管理器：因子配置管理
- 信号生成器：交易信号生成
- 收益计算器：投资组合收益计算
"""

from .data_replayer import DataReplayer, DataSnapshot
from .factor_combination_manager import (
    ConfigValidator,
    FactorCombinationManager,
)
from .return_calculator import (
    PerformanceMetrics,
    PortfolioPosition,
    ReturnCalculator,
    TransactionCost,
)
from .signal_generator import SignalGenerator

__all__ = [
    "DataReplayer",
    "DataSnapshot",
    "FactorCombinationManager",
    "ConfigValidator",
    "SignalGenerator",
    "ReturnCalculator",
    "PerformanceMetrics",
    "PortfolioPosition",
    "TransactionCost",
]
