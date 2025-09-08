"""连接池管理模块"""

from contextlib import asynccontextmanager
from typing import Any

import redis
from loguru import logger
from sqlalchemy import text

from ..config.database import AsyncSessionLocal, async_engine
from ..config.redis import get_redis_client


class ConnectionPoolManager:
    """连接池管理器"""

    def __init__(self) -> None:
        self._mysql_initialized = False
        self._redis_initialized = False
        self._redis_client: redis.Redis | None = None

    async def initialize(self) -> None:
        """初始化所有连接池"""
        try:
            logger.info("开始初始化连接池...")

            # 初始化MySQL连接池
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            self._mysql_initialized = True
            logger.info("MySQL连接池初始化完成")

            # 初始化Redis连接池
            try:
                self._redis_client = get_redis_client()
                # 测试Redis连接
                self._redis_client.ping()
                self._redis_initialized = True
                logger.info("Redis连接池初始化完成")
            except Exception as e:
                logger.error(f"Redis连接池初始化失败: {e}")
                raise

            logger.info("所有连接池初始化完成")

        except Exception as e:
            logger.error(f"连接池初始化失败: {e}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """清理所有连接池"""
        try:
            logger.info("开始清理连接池...")

            if self._mysql_initialized:
                await async_engine.dispose()
                logger.info("MySQL连接池已关闭")

            if self._redis_initialized and self._redis_client:
                try:
                    self._redis_client.close()
                    logger.info("Redis连接池已关闭")
                except Exception as e:
                    logger.warning(f"关闭Redis连接池时出错: {e}")

            self._mysql_initialized = False
            self._redis_initialized = False
            self._redis_client = None

            logger.info("连接池清理完成")

        except Exception as e:
            logger.error(f"连接池清理异常: {e}")

    @property
    def is_initialized(self) -> bool:
        """检查连接池是否已初始化"""
        return self._mysql_initialized and self._redis_initialized

    async def health_check(self) -> dict:
        """连接池健康检查"""
        health_status = {"mysql": False, "redis": False, "overall": False}

        # 检查MySQL连接
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            health_status["mysql"] = True
            logger.debug("MySQL连接健康")
        except Exception as e:
            logger.error(f"MySQL连接异常: {e}")

        # 检查Redis连接
        try:
            if self._redis_client:
                self._redis_client.ping()
                health_status["redis"] = True
                logger.debug("Redis连接健康")
            else:
                health_status["redis"] = False
                logger.warning("Redis客户端未初始化")
        except Exception as e:
            health_status["redis"] = False
            logger.error(f"Redis连接异常: {e}")

        health_status["overall"] = health_status["mysql"] and health_status["redis"]
        return health_status


# 全局连接池管理器实例
connection_pool_manager = ConnectionPoolManager()


@asynccontextmanager
async def get_db_session() -> Any:
    """获取数据库会话的上下文管理器"""
    if not connection_pool_manager.is_initialized:
        raise RuntimeError("连接池未初始化")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_redis_connection() -> Any:
    """获取Redis连接的上下文管理器"""
    if not connection_pool_manager.is_initialized:
        raise RuntimeError("连接池未初始化")

    if not connection_pool_manager._redis_client:
        raise RuntimeError("Redis客户端未初始化")

    try:
        yield connection_pool_manager._redis_client
    except Exception as e:
        logger.error(f"Redis连接异常: {e}")
        raise


async def get_connection_stats() -> dict[str, Any]:
    """获取连接池统计信息"""
    try:
        # 获取连接池基本信息
        pool = async_engine.pool
        mysql_stats = {
            "engine_url": str(async_engine.url),
            "pool_class": pool.__class__.__name__,
            "engine_name": async_engine.name or "default",
        }

        # 尝试获取可用的池统计信息
        if hasattr(pool, "_pool"):
            mysql_stats["pool_available"] = getattr(pool._pool, "qsize", lambda: 0)()

    except Exception as e:
        mysql_stats = {"error": str(e)}

    # Redis统计信息
    try:
        if connection_pool_manager._redis_client:
            redis_info = connection_pool_manager._redis_client.info()
            redis_stats = {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory", 0),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
                "redis_version": redis_info.get("redis_version", "unknown"),
            }
        else:
            redis_stats = {"error": "Redis客户端未初始化"}
    except Exception as e:
        redis_stats = {"error": str(e)}

    stats = {"mysql": mysql_stats, "redis": redis_stats}

    return stats
