"""Redis配置模块

提供Redis客户端配置和依赖注入功能
"""

import redis
from loguru import logger

from .settings import settings

# Redis客户端配置
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)


def get_redis_client() -> redis.Redis:
    """获取Redis客户端的依赖注入函数"""
    try:
        # 测试连接
        redis_client.ping()
        return redis_client
    except redis.ConnectionError as e:
        logger.error(f"Redis连接失败: {e}")
        raise
    except Exception as e:
        logger.error(f"Redis客户端获取失败: {e}")
        raise


def close_redis_client() -> None:
    """关闭Redis客户端连接"""
    try:
        redis_client.close()
        logger.info("Redis客户端连接已关闭")
    except Exception as e:
        logger.warning(f"关闭Redis客户端时出错: {e}")


logger.info("Redis配置初始化完成")
