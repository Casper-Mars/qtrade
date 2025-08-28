"""API v1 路由注册

本模块负责注册所有v1版本的API路由。
"""

from fastapi import APIRouter

from .fundamental import router as fundamental_router
from .market import router as market_router
from .sentiment import router as sentiment_router
from .technical import router as technical_router

# 创建v1版本的主路由
api_v1_router = APIRouter(prefix="/api/v1")

# 注册各个因子模块的路由
api_v1_router.include_router(
    technical_router,
    prefix="/technical",
    tags=["技术因子"]
)

api_v1_router.include_router(
    sentiment_router,
    prefix="/sentiment",
    tags=["情绪因子"]
)

api_v1_router.include_router(
    fundamental_router,
    prefix="/fundamental",
    tags=["基本面因子"]
)

api_v1_router.include_router(
    market_router,
    prefix="/market",
    tags=["市场因子"]
)

__all__ = ["api_v1_router"]
