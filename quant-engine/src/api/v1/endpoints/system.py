"""系统信息API端点"""

import platform
from datetime import datetime
from typing import Any

import psutil
from fastapi import APIRouter
from loguru import logger

from src.config.connection_pool import get_connection_stats

from ....config.settings import settings

router = APIRouter()


@router.get("/info", summary="系统信息")
async def system_info() -> dict[str, Any]:
    """获取系统基本信息"""
    try:
        return {
            "service": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug,
                "host": settings.host,
                "port": settings.port,
            },
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "hostname": platform.node(),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/stats", summary="系统统计信息")
async def system_stats() -> dict[str, Any]:
    """获取系统统计信息"""
    try:
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # 内存信息
        memory = psutil.virtual_memory()

        # 磁盘信息
        disk = psutil.disk_usage("/")

        # 连接池统计
        connection_stats = await get_connection_stats()

        return {
            "cpu": {"usage_percent": cpu_percent, "count": cpu_count},
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "usage_percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": (disk.used / disk.total) * 100,
            },
            "connections": connection_stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/config", summary="配置信息")
async def config_info() -> dict[str, Any]:
    """获取配置信息（敏感信息已脱敏）"""
    try:
        return {
            "app": {
                "name": settings.app_name,
                "version": settings.app_version,
                "debug": settings.debug,
                "host": settings.host,
                "port": settings.port,
            },
            "database": {
                "mysql_host": settings.mysql_host,
                "mysql_port": settings.mysql_port,
                "mysql_database": settings.mysql_database,
                "mysql_charset": settings.mysql_charset,
            },
            "redis": {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
            },
            "external_services": {
                "data_collector_base_url": settings.data_collector_base_url,
                "data_collector_timeout": settings.data_collector_timeout,
            },
            "logging": {"level": settings.log_level, "file": settings.log_file},
            "cache": {"ttl": settings.cache_ttl},
            "nlp": {
                "finbert_model_name": settings.finbert_model_name,
                "model_cache_dir": settings.model_cache_dir,
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"获取配置信息失败: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}
