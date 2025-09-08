"""API v1 路由模块"""

from fastapi import APIRouter
from loguru import logger

from ...backtest_engine.api.v1 import factor_config
from ...factor_engine.api.v1 import fundamental, market, sentiment, technical
from .endpoints import health, system

# 创建API v1路由器
api_v1_router = APIRouter()

# 注册子路由
api_v1_router.include_router(health.router, prefix="/health", tags=["健康检查"])

api_v1_router.include_router(system.router, prefix="/system", tags=["系统信息"])

api_v1_router.include_router(technical.router, tags=["技术因子"])

api_v1_router.include_router(
    fundamental.router, tags=["基本面因子"]
)

api_v1_router.include_router(
    sentiment.router, tags=["情绪因子"]
)

api_v1_router.include_router(
    market.router, tags=["市场因子"]
)

api_v1_router.include_router(
    factor_config.router, tags=["因子组合配置"]
)

logger.info("API v1路由注册完成")
