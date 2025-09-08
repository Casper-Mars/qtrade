"""回测引擎缓存管理模块

本模块提供回测引擎的缓存功能，包括：
- Redis缓存操作
- 回测结果缓存
- 因子组合缓存
- 性能指标缓存
"""

import json
from datetime import timedelta
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = timedelta(hours=24)  # 默认24小时过期

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """设置缓存"""
        try:
            serialized_value = json.dumps(value, default=str)
            expire_time = ttl or self.default_ttl
            await self.redis.setex(key, expire_time, serialized_value)
            return True
        except Exception:
            return False

    async def get(self, key: str) -> Any | None:
        """获取缓存"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception:
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception:
            return 0


class BacktestCache:
    """回测缓存管理"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = "backtest"

    def _make_key(self, suffix: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}:{suffix}"

    async def cache_backtest_result(self, backtest_id: UUID, result: dict, ttl: timedelta | None = None) -> bool:
        """缓存回测结果"""
        key = self._make_key(f"result:{backtest_id}")
        return await self.cache.set(key, result, ttl)

    async def get_backtest_result(self, backtest_id: UUID) -> dict | None:
        """获取回测结果缓存"""
        key = self._make_key(f"result:{backtest_id}")
        return await self.cache.get(key)

    async def cache_performance_metrics(self, backtest_id: UUID, metrics: dict, ttl: timedelta | None = None) -> bool:
        """缓存性能指标"""
        key = self._make_key(f"metrics:{backtest_id}")
        return await self.cache.set(key, metrics, ttl)

    async def get_performance_metrics(self, backtest_id: UUID) -> dict | None:
        """获取性能指标缓存"""
        key = self._make_key(f"metrics:{backtest_id}")
        return await self.cache.get(key)

    async def clear_backtest_cache(self, backtest_id: UUID) -> int:
        """清除指定回测的所有缓存"""
        pattern = self._make_key(f"*:{backtest_id}")
        return await self.cache.clear_pattern(pattern)


class FactorCombinationCache:
    """因子组合缓存管理"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.prefix = "factor_combination"

    def _make_key(self, suffix: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}:{suffix}"

    async def cache_combination(self, combination_id: UUID, combination: dict, ttl: timedelta | None = None) -> bool:
        """缓存因子组合"""
        key = self._make_key(f"config:{combination_id}")
        return await self.cache.set(key, combination, ttl)

    async def get_combination(self, combination_id: UUID) -> dict | None:
        """获取因子组合缓存"""
        key = self._make_key(f"config:{combination_id}")
        return await self.cache.get(key)

    async def cache_combination_list(self, user_id: str, combinations: list, ttl: timedelta | None = None) -> bool:
        """缓存用户的因子组合列表"""
        key = self._make_key(f"list:{user_id}")
        return await self.cache.set(key, combinations, ttl)

    async def get_combination_list(self, user_id: str) -> list | None:
        """获取用户的因子组合列表缓存"""
        key = self._make_key(f"list:{user_id}")
        return await self.cache.get(key)

    async def clear_user_cache(self, user_id: str) -> int:
        """清除用户相关的所有缓存"""
        pattern = self._make_key(f"*:{user_id}")
        return await self.cache.clear_pattern(pattern)
