"""健康检查API端点"""

from typing import Any

from fastapi import APIRouter
from loguru import logger

from src.config.connection_pool import connection_pool_manager, get_connection_stats

from ....clients.data_collector_client import get_data_collector_client
from ....config.settings import settings

router = APIRouter()


@router.get("/", summary="基础健康检查")
async def basic_health_check() -> dict[str, Any]:
    """基础健康检查"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/detailed", summary="详细健康检查")
async def detailed_health_check() -> dict[str, Any]:
    """详细健康检查，包括数据库和外部服务"""
    try:
        # 检查连接池状态
        health_status = await connection_pool_manager.health_check()

        # 检查data-collector服务
        data_collector_status = False
        try:
            async with await get_data_collector_client() as client:
                data_collector_status = await client.health_check()
        except Exception as e:
            logger.warning(f"data-collector服务检查失败: {e}")

        # 获取连接池统计
        connection_stats = await get_connection_stats()

        overall_status = health_status["overall"] and data_collector_status

        return {
            "status": "ok" if overall_status else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "components": {
                "mysql": health_status["mysql"],
                "redis": health_status["redis"],
                "data_collector": data_collector_status,
            },
            "connection_stats": connection_stats,
            "overall": overall_status,
        }

    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        return {
            "status": "error",
            "service": settings.app_name,
            "version": settings.app_version,
            "error": str(e),
        }


@router.get("/readiness", summary="就绪检查")
async def readiness_check() -> dict[str, Any]:
    """就绪检查，用于Kubernetes等容器编排"""
    try:
        # 检查关键组件是否就绪
        is_ready = connection_pool_manager.is_initialized

        if is_ready:
            # 进一步检查连接池健康状态
            health_status = await connection_pool_manager.health_check()
            is_ready = health_status["mysql"] and health_status["redis"]

        return {
            "status": "ready" if is_ready else "not_ready",
            "service": settings.app_name,
            "ready": is_ready,
        }

    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        return {
            "status": "error",
            "service": settings.app_name,
            "ready": False,
            "error": str(e),
        }


@router.get("/liveness", summary="存活检查")
async def liveness_check() -> dict[str, Any]:
    """存活检查，用于Kubernetes等容器编排"""
    return {"status": "alive", "service": settings.app_name, "alive": True}
