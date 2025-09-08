"""回测引擎服务层模块

本模块提供回测引擎的业务服务功能，包括：
- 回测任务服务
- 因子组合管理服务
- 性能分析服务
- 策略执行服务
"""

from .factor_combination_manager import (
    ConfigValidator,
    FactorCombinationManager,
)

__all__ = [
    "FactorCombinationManager",
    "ConfigValidator",
]
