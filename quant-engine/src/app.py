"""FastAPI应用实例"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .api.v1.router import api_v1_router
from .config.settings import settings
from .dao.connection_pool import connection_pool_manager
from .utils.exceptions import setup_exception_handlers
from .utils.logger import init_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")

    try:
        # 初始化连接池
        await connection_pool_manager.initialize()
        logger.info("应用启动完成")

        yield

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    finally:
        # 关闭时执行
        logger.info("正在关闭应用...")
        await connection_pool_manager.cleanup()
        logger.info("应用已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""

    # 初始化日志系统
    init_logger()

    # 创建FastAPI实例
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="量化计算引擎服务",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    # 设置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设置异常处理器
    setup_exception_handlers(app)

    # 注册路由
    app.include_router(api_v1_router, prefix="/api/v1")

    # 健康检查端点
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """健康检查"""
        try:
            # 检查连接池状态
            health_status = await connection_pool_manager.health_check()

            return {
                "status": "ok" if health_status["overall"] else "degraded",
                "service": settings.app_name,
                "version": settings.app_version,
                "health": health_status
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "error",
                "service": settings.app_name,
                "version": settings.app_version,
                "error": str(e)
            }

    # 根路径
    @app.get("/")
    async def root() -> dict[str, str]:
        """根路径"""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "description": "量化计算引擎服务",
            "docs": "/docs" if settings.debug else "文档已禁用"
        }

    logger.info(f"FastAPI应用创建完成: {settings.app_name} v{settings.app_version}")
    return app


# 创建应用实例
app = create_app()
