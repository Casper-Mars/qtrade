"""回测引擎模块

本模块提供量化交易回测功能，包括：
- 因子组合管理
- 回测策略执行
- 性能指标计算
- 风险控制管理
"""

from . import api, dao, models, services

__version__ = "1.0.0"

__all__ = [
    "api",
    "dao",
    "models",
    "services",
]
