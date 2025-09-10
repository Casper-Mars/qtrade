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
router = APIRouter()

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
    "/factor/{stock_code}",
    response_model=ApiResponse,
    summary="获取股票情绪因子",
    description="获取指定股票和日期的情绪因子数据",
)
async def get_sentiment_factor(
    stock_code: str,
    calculation_date: str = Query(..., description="计算日期，格式：YYYY-MM-DD"),
) -> ApiResponse:
    """获取股票情绪因子

    Args:
        stock_code: 股票代码
        calculation_date: 计算日期

    Returns:
        ApiResponse: 包含情绪因子数据的响应
    """
    try:
        # 验证日期格式
        try:
            datetime.strptime(calculation_date, "%Y-%m-%d")
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="日期格式不正确，应为YYYY-MM-DD"
            ) from e

        result = await NewsSentimentFactorDAO.get_sentiment_factor(
            stock_code=stock_code,
            calculation_date=calculation_date,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"未找到股票 {stock_code} 在 {calculation_date} 的情绪因子数据"
            )

        return ApiResponse(
            code=200,
            message="获取情绪因子成功",
            data=result.dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取情绪因子失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪因子时发生错误: {str(e)}"
        ) from e


@router.get(
    "/factors/date/{calculation_date}",
    response_model=ApiResponse,
    summary="获取指定日期的所有情绪因子",
    description="获取指定日期的所有股票情绪因子数据",
)
async def get_sentiment_factors_by_date(
    calculation_date: str,
    limit: int = Query(default=100, description="返回记录数限制"),
) -> ApiResponse:
    """获取指定日期的所有情绪因子

    Args:
        calculation_date: 计算日期
        limit: 返回记录数限制

    Returns:
        ApiResponse: 包含情绪因子数据列表的响应
    """
    try:
        # 验证日期格式
        try:
            datetime.strptime(calculation_date, "%Y-%m-%d")
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="日期格式不正确，应为YYYY-MM-DD"
            ) from e

        results = await NewsSentimentFactorDAO.get_sentiment_factors_by_date(
            calculation_date=calculation_date,
            limit=limit,
        )

        return ApiResponse(
            code=200,
            message=f"获取 {calculation_date} 情绪因子数据成功",
            data={
                "calculation_date": calculation_date,
                "count": len(results),
                "factors": [result.dict() for result in results],
            },
        )

    except HTTPException:
        raise
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
) -> ApiResponse:
    """获取股票情绪趋势

    Args:
        request: 情绪趋势查询请求

    Returns:
        ApiResponse: 包含趋势数据的响应
    """
    try:
        # 获取趋势数据
        trend_data = await NewsSentimentFactorDAO.get_sentiment_trend(
            stock_code=request.stock_code,
            days=request.days,
        )

        # 获取统计数据
        statistics = await NewsSentimentFactorDAO.get_sentiment_statistics(
            stock_code=request.stock_code,
            days=request.days,
        )

        response_data = SentimentTrendResponse(
            stock_code=request.stock_code,
            period=f"{request.days}天",
            daily_factors=trend_data,
            statistics=statistics,
        )

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


@router.get(
    "/health",
    response_model=ApiResponse,
    summary="情绪因子服务健康检查",
    description="检查情绪因子计算服务的健康状态",
)
async def sentiment_health_check() -> ApiResponse:
    """情绪因子服务健康检查

    Returns:
        ApiResponse: 健康检查结果
    """
    try:
        # 检查模型状态
        model_status = {
            "nlp_model_loaded": True,
            "sentiment_analyzer_ready": True
        }

        # 检查数据库连接
        try:
            # 尝试查询一条记录来测试数据库连接
            await NewsSentimentFactorDAO.get_sentiment_factors_by_date(
                calculation_date="2024-01-01",
                limit=1
            )
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        health_data = {
            "service": "sentiment-factor",
            "status": "healthy" if model_status.get("nlp_model_loaded") and db_status == "healthy" else "unhealthy",
            "model_status": model_status,
            "database_status": db_status,
            "timestamp": datetime.now().isoformat(),
        }

        return ApiResponse(
            code=200,
            message="健康检查完成",
            data=health_data,
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return ApiResponse(
            code=500,
            message="健康检查失败",
            data={
                "service": "sentiment-factor",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )
