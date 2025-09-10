"""情绪因子API接口"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger

from ...services.sentiment_service import SentimentFactorService
from ...models.schemas import (
    ApiResponse,
    BatchSentimentFactorRequest,
    BatchSentimentFactorResponse,
    SentimentFactorRequest,
    SentimentTrendRequest,
    SentimentTrendResponse,
)
# 创建路由器
router = APIRouter(prefix="/sentiment", tags=["sentiment-factors"])

# 全局情感因子服务实例
_sentiment_service_instance: Optional[SentimentFactorService] = None


def get_sentiment_service() -> SentimentFactorService:
    """获取情感因子服务实例（单例模式）"""
    global _sentiment_service_instance
    if _sentiment_service_instance is None:
        _sentiment_service_instance = SentimentFactorService()
    return _sentiment_service_instance


@router.post(
    "/calculate",
    response_model=ApiResponse,
    summary="计算单个股票情绪因子",
    description="基于新闻数据计算指定股票的情绪因子",
)
async def calculate_sentiment_factor(
    request: SentimentFactorRequest,
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """计算单个股票情绪因子

    Args:
        request: 情绪因子计算请求

    Returns:
        ApiResponse: 包含情绪因子结果的响应

    Raises:
        HTTPException: 计算失败时抛出异常
    """
    try:
        response_data = await sentiment_service.calculate_sentiment_factor(request)
        
        return ApiResponse(
            code=200,
            message="情绪因子计算成功",
            data=response_data.dict(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        ) from e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算情绪因子失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"计算情绪因子时发生错误: {str(e)}"
        ) from e


@router.post(
    "/batch-calculate",
    response_model=ApiResponse,
    summary="批量计算情绪因子",
    description="批量计算多个股票的情绪因子",
)
async def batch_calculate_sentiment_factors(
    request: BatchSentimentFactorRequest,
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """批量计算情绪因子

    Args:
        request: 批量情绪因子计算请求

    Returns:
        ApiResponse: 包含批量计算结果的响应
    """
    try:
        response_data = await sentiment_service.batch_calculate_sentiment_factors(request)
        
        return ApiResponse(
            code=200,
            message="批量情绪因子计算完成",
            data=response_data.dict(),
        )

    except Exception as e:
        logger.error(f"批量计算情绪因子失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量计算情绪因子时发生错误: {str(e)}"
        ) from e


@router.get(
    "/factor",
    response_model=ApiResponse,
    summary="获取股票情绪因子",
    description="获取指定股票和日期的情绪因子数据",
)
async def get_sentiment_factor(
    stock_code: str = Query(..., description="股票代码"),
    calculation_date: str = Query(..., description="计算日期，格式：YYYY-MM-DD"),
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """获取股票情绪因子

    Args:
        stock_code: 股票代码
        calculation_date: 计算日期
        sentiment_service: 情绪因子服务

    Returns:
        ApiResponse: 包含情绪因子数据的响应
    """
    try:
        result = await sentiment_service.get_sentiment_factor(
            stock_code=stock_code,
            date=calculation_date,
        )

        if result is None:
            return ApiResponse(
                code=404,
                message="未找到情绪因子数据",
                data=None,
            )

        return ApiResponse(
            code=200,
            message="获取情绪因子成功",
            data=result,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"获取情绪因子失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪因子时发生错误: {str(e)}"
        ) from e


@router.get(
    "/factors/date",
    response_model=ApiResponse,
    summary="获取指定日期的所有情绪因子",
    description="获取指定日期的所有股票情绪因子数据",
)
async def get_sentiment_factors_by_date(
    calculation_date: str = Query(..., description="计算日期，格式：YYYY-MM-DD"),
    limit: int = Query(default=100, description="返回记录数限制"),
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """获取指定日期的所有情绪因子

    Args:
        calculation_date: 计算日期
        limit: 返回记录数限制
        sentiment_service: 情绪因子服务

    Returns:
        ApiResponse: 包含情绪因子数据列表的响应
    """
    try:
        results = await sentiment_service.get_sentiment_factors_by_date(
            date=calculation_date,
            limit=limit,
        )

        return ApiResponse(
            code=200,
            message=f"获取 {calculation_date} 情绪因子数据成功",
            data={
                "calculation_date": calculation_date,
                "count": len(results),
                "factors": results,
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"获取日期情绪因子失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取日期情绪因子时发生错误: {str(e)}"
        ) from e


@router.post(
    "/trend",
    response_model=ApiResponse,
    summary="获取股票情绪趋势",
    description="获取指定股票的情绪趋势数据和统计信息",
)
async def get_sentiment_trend(
    request: SentimentTrendRequest,
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """获取股票情绪趋势

    Args:
        request: 情绪趋势查询请求
        sentiment_service: 情绪因子服务

    Returns:
        ApiResponse: 包含趋势数据的响应
    """
    try:
        response_data = await sentiment_service.get_sentiment_trend(request)

        return ApiResponse(
            code=200,
            message="获取情绪趋势成功",
            data=response_data.dict(),
        )

    except Exception as e:
        logger.error(f"获取情绪趋势失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪趋势时发生错误: {str(e)}"
        ) from e


@router.post(
    "/statistics",
    response_model=ApiResponse,
    summary="获取股票情绪统计",
    description="获取指定股票的情绪统计数据",
)
async def get_sentiment_statistics(
    request: SentimentTrendRequest,
    sentiment_service: SentimentFactorService = Depends(get_sentiment_service),
) -> ApiResponse:
    """获取股票情绪统计

    Args:
        request: 情绪统计查询请求
        sentiment_service: 情绪因子服务

    Returns:
        ApiResponse: 包含统计数据的响应
    """
    try:
        # 获取统计数据
        from ...dao.base import NewsSentimentFactorDAO
        statistics = await NewsSentimentFactorDAO.get_sentiment_statistics(
            stock_code=request.stock_code,
            days=request.days,
        )

        return ApiResponse(
            code=200,
            message="获取情绪统计成功",
            data=statistics,
        )

    except Exception as e:
        logger.error(f"获取情绪统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪统计时发生错误: {str(e)}"
        ) from e
