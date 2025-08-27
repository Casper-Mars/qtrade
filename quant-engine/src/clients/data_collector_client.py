"""data-collector服务HTTP客户端"""

from typing import Any

import httpx
from loguru import logger

from ..config.settings import settings


class DataCollectorClient:
    """data-collector服务客户端"""

    def __init__(self) -> None:
        self.base_url = settings.data_collector_base_url
        self.timeout = settings.data_collector_timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "DataCollectorClient":
        """异步上下文管理器入口"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{settings.app_name}/{settings.app_version}"
            }
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器退出"""
        if self._client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None
    ) -> Any:
        """通用请求方法"""
        if not self._client:
            raise RuntimeError("客户端未初始化，请使用async with语句")

        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP请求失败: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"请求异常: {e}")
            raise
        except Exception as e:
            logger.error(f"未知异常: {e}")
            raise

    async def get_stock_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> Any:
        """获取股票数据"""
        params: dict[str, Any] = {"symbol": symbol}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        result = await self._request("GET", "/api/v1/stock/data", params=params)
        return result.get("data", [])

    async def get_financial_data(
        self,
        symbol: str,
        report_type: str = "annual"
    ) -> Any:
        """获取财务数据"""
        params: dict[str, Any] = {
            "symbol": symbol,
            "report_type": report_type
        }

        result = await self._request("GET", "/api/v1/financial/data", params=params)
        return result.get("data", [])

    async def get_market_data(
        self,
        market: str = "A",
        data_type: str = "index"
    ) -> Any:
        """获取市场数据"""
        params: dict[str, Any] = {
            "market": market,
            "data_type": data_type
        }

        result = await self._request("GET", "/api/v1/market/data", params=params)
        return result.get("data", [])

    async def get_news_data(
        self,
        symbol: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100
    ) -> Any:
        """获取新闻数据"""
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if category:
            params["category"] = category
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        result = await self._request("GET", "/api/v1/news/data", params=params)
        return result.get("data", [])

    async def get_policy_data(
        self,
        policy_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> Any:
        """获取政策数据"""
        params: dict[str, Any] = {}
        if policy_type:
            params["policy_type"] = policy_type
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        result = await self._request("GET", "/api/v1/policy/data", params=params)
        return result.get("data", [])

    async def health_check(self) -> Any:
        """健康检查"""
        try:
            result = await self._request("GET", "/health")
            return result.get("status") == "ok"
        except Exception as e:
            logger.error(f"data-collector服务健康检查失败: {e}")
            return False


# 全局客户端实例工厂
async def get_data_collector_client() -> DataCollectorClient:
    """获取data-collector客户端实例"""
    return DataCollectorClient()
