"""Redis缓存配置和策略

本模块定义了因子数据的Redis缓存策略，提供高性能的数据访问。
"""

import json
import pickle
from datetime import date, datetime
from typing import Any

from redis import Redis


class FactorCacheManager:
    """因子数据缓存管理器"""

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

        # 缓存TTL配置（秒）
        self.ttl_config = {
            "hot_factors": 3600,  # 热点因子数据: 1小时
            "calculation_result": 1800,  # 计算中间结果: 30分钟
            "stock_basic": 86400,  # 股票基础数据: 24小时
            "factor_list": 7200,  # 因子列表: 2小时
            "batch_task": 600,  # 批量任务状态: 10分钟
        }

        # 缓存Key前缀
        self.key_prefix = {
            "technical": "factor:technical",
            "fundamental": "factor:fundamental",
            "market": "factor:market",
            "news_sentiment": "factor:sentiment",
            "calculation": "calc:result",
            "stock_basic": "stock:basic",
            "factor_list": "factor:list",
            "batch_task": "task:batch",
        }

    def _build_key(self, prefix: str, *args: Any) -> str:
        """构建缓存Key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据"""
        if isinstance(data, dict | list | str | int | float | bool):
            return json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        else:
            return pickle.dumps(data)

    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化数据"""
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(data)

    # ==================== 技术因子缓存 ====================

    def cache_technical_factor(
        self, stock_code: str, factor_name: str, trade_date: date, factor_value: float
    ) -> bool:
        """缓存技术因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["technical"],
                stock_code,
                factor_name,
                trade_date.isoformat(),
            )

            data = {
                "stock_code": stock_code,
                "factor_name": factor_name,
                "factor_value": factor_value,
                "trade_date": trade_date.isoformat(),
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存技术因子数据失败: {e}")
            return False

    def get_technical_factor(
        self, stock_code: str, factor_name: str, trade_date: date
    ) -> Any:
        """获取技术因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["technical"],
                stock_code,
                factor_name,
                trade_date.isoformat(),
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取技术因子缓存失败: {e}")
            return None

    def cache_technical_factors_batch(
        self, stock_code: str, trade_date: date, factors: dict[str, float]
    ) -> bool:
        """批量缓存技术因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["technical"],
                "batch",
                stock_code,
                trade_date.isoformat(),
            )

            data = {
                "stock_code": stock_code,
                "trade_date": trade_date.isoformat(),
                "factors": factors,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"批量缓存技术因子数据失败: {e}")
            return False

    def get_technical_factors_batch(self, stock_code: str, trade_date: date) -> Any:
        """批量获取技术因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["technical"],
                "batch",
                stock_code,
                trade_date.isoformat(),
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"批量获取技术因子缓存失败: {e}")
            return None

    # ==================== 基本面因子缓存 ====================

    def cache_fundamental_factor(
        self, stock_code: str, factor_name: str, report_period: str, factor_value: float
    ) -> bool:
        """缓存基本面因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["fundamental"], stock_code, factor_name, report_period
            )

            data = {
                "stock_code": stock_code,
                "factor_name": factor_name,
                "factor_value": factor_value,
                "report_period": report_period,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存基本面因子数据失败: {e}")
            return False

    def get_fundamental_factor(
        self, stock_code: str, factor_name: str, report_period: str
    ) -> Any:
        """获取基本面因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["fundamental"], stock_code, factor_name, report_period
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取基本面因子缓存失败: {e}")
            return None

    def cache_fundamental_factors(
        self,
        stock_code: str,
        period: str,
        factors: dict[str, float],
        growth_rates: dict[str, float],
    ) -> bool:
        """批量缓存基本面因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["fundamental"], "batch", stock_code, period
            )

            data = {
                "stock_code": stock_code,
                "period": period,
                "factors": factors,
                "growth_rates": growth_rates,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"批量缓存基本面因子数据失败: {e}")
            return False

    def get_fundamental_factors(self, stock_code: str, period: str) -> Any:
        """批量获取基本面因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["fundamental"], "batch", stock_code, period
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"批量获取基本面因子缓存失败: {e}")
            return None

    # ==================== 市场因子缓存 ====================

    def cache_market_factor(
        self, stock_code: str, factor_name: str, trade_date: date, factor_value: float
    ) -> bool:
        """缓存市场因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["market"],
                stock_code,
                factor_name,
                trade_date.isoformat(),
            )

            data = {
                "stock_code": stock_code,
                "factor_name": factor_name,
                "factor_value": factor_value,
                "trade_date": trade_date.isoformat(),
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存市场因子数据失败: {e}")
            return False

    def get_market_factor(
        self, stock_code: str, factor_name: str, trade_date: date
    ) -> Any:
        """获取市场因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["market"],
                stock_code,
                factor_name,
                trade_date.isoformat(),
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取市场因子缓存失败: {e}")
            return None

    def cache_market_factors_batch(
        self, stock_code: str, trade_date: date, factors: dict[str, float]
    ) -> bool:
        """批量缓存市场因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["market"],
                "batch",
                stock_code,
                trade_date.isoformat(),
            )

            data = {
                "stock_code": stock_code,
                "trade_date": trade_date.isoformat(),
                "factors": factors,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"批量缓存市场因子数据失败: {e}")
            return False

    def get_market_factors_batch(self, stock_code: str, trade_date: date) -> Any:
        """批量获取市场因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["market"],
                "batch",
                stock_code,
                trade_date.isoformat(),
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"批量获取市场因子缓存失败: {e}")
            return None

    # ==================== 新闻情绪因子缓存 ====================

    def cache_sentiment_factor(
        self,
        stock_code: str,
        calculation_date: date,
        factor_value: float,
        news_count: int,
    ) -> bool:
        """缓存新闻情绪因子数据"""
        try:
            key = self._build_key(
                self.key_prefix["news_sentiment"],
                stock_code,
                calculation_date.isoformat(),
            )

            data = {
                "stock_code": stock_code,
                "factor_value": factor_value,
                "calculation_date": calculation_date.isoformat(),
                "news_count": news_count,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["hot_factors"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存新闻情绪因子数据失败: {e}")
            return False

    def get_sentiment_factor(self, stock_code: str, calculation_date: date) -> Any:
        """获取新闻情绪因子缓存数据"""
        try:
            key = self._build_key(
                self.key_prefix["news_sentiment"],
                stock_code,
                calculation_date.isoformat(),
            )

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取新闻情绪因子缓存失败: {e}")
            return None

    # ==================== 计算结果缓存 ====================

    def cache_calculation_result(self, task_id: str, result: dict) -> bool:
        """缓存计算结果"""
        try:
            key = self._build_key(self.key_prefix["calculation"], task_id)

            data = {
                "task_id": task_id,
                "result": result,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            cache_result = self.redis_client.setex(
                key, self.ttl_config["calculation_result"], serialized_data
            )
            return bool(cache_result)
        except Exception as e:
            print(f"缓存计算结果失败: {e}")
            return False

    def get_calculation_result(self, task_id: str) -> Any:
        """获取计算结果缓存"""
        try:
            key = self._build_key(self.key_prefix["calculation"], task_id)

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取计算结果缓存失败: {e}")
            return None

    # ==================== 股票基础数据缓存 ====================

    def cache_stock_basic_info(self, stock_code: str, basic_info: dict) -> bool:
        """缓存股票基础信息"""
        try:
            key = self._build_key(self.key_prefix["stock_basic"], stock_code)

            data = {
                "stock_code": stock_code,
                "basic_info": basic_info,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["stock_basic"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存股票基础信息失败: {e}")
            return False

    def get_stock_basic_info(self, stock_code: str) -> Any:
        """获取股票基础信息缓存"""
        try:
            key = self._build_key(self.key_prefix["stock_basic"], stock_code)

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取股票基础信息缓存失败: {e}")
            return None

    # ==================== 批量任务状态缓存 ====================

    def cache_batch_task_status(self, task_id: str, status: dict) -> bool:
        """缓存批量任务状态"""
        try:
            key = self._build_key(self.key_prefix["batch_task"], task_id)

            data = {
                "task_id": task_id,
                "status": status,
                "cached_at": datetime.now().isoformat(),
            }

            serialized_data = self._serialize_data(data)
            result = self.redis_client.setex(
                key, self.ttl_config["batch_task"], serialized_data
            )
            return bool(result)
        except Exception as e:
            print(f"缓存批量任务状态失败: {e}")
            return False

    def get_batch_task_status(self, task_id: str) -> Any:
        """获取批量任务状态缓存"""
        try:
            key = self._build_key(self.key_prefix["batch_task"], task_id)

            cached_data = self.redis_client.get(key)
            if cached_data:
                return self._deserialize_data(cached_data)
            return None
        except Exception as e:
            print(f"获取批量任务状态缓存失败: {e}")
            return None

    # ==================== 缓存管理 ====================

    def delete_cache(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                result = self.redis_client.delete(*keys)
                return int(result)
            return 0
        except Exception as e:
            print(f"删除缓存失败: {e}")
            return 0

    def clear_expired_cache(self) -> dict[str, int]:
        """清理过期缓存"""
        result = {}

        for cache_type, prefix in self.key_prefix.items():
            try:
                pattern = f"{prefix}:*"
                deleted_count = self.delete_cache(pattern)
                result[cache_type] = deleted_count
            except Exception as e:
                print(f"清理{cache_type}缓存失败: {e}")
                result[cache_type] = 0

        return result

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / max(
                        info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                    )
                )
                * 100,
            }
        except Exception as e:
            print(f"获取缓存统计信息失败: {e}")
            return {}


def create_cache_manager(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    redis_password: str | None = None,
) -> FactorCacheManager:
    """创建缓存管理器实例"""
    redis_client = Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=False,  # 保持二进制模式以支持pickle
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    return FactorCacheManager(redis_client)
