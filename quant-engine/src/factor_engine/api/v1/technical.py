"""技术因子API接口模块

提供技术因子计算的RESTful API接口，包括：
- 计算单个技术因子
- 查询技术因子历史数据
- 批量计算技术因子
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from src.utils.exceptions import DataNotFoundError, FactorCalculationException

from ....config.database import get_db_session
from ....config.redis import get_redis_client
from ...dao.factor_dao import FactorDAO
from ...models.schemas import (
    BatchTechnicalFactorRequest,
    BatchTechnicalFactorResponse,
    TechnicalFactorHistoryResponse,
    TechnicalFactorRequest,
    TechnicalFactorResponse,
)
from ...services.factor_service import FactorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/technical", tags=["technical-factors"])


def get_factor_service(
    db_session: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client)
) -> FactorService:
    """获取因子服务实例"""
    factor_dao = FactorDAO(db_session, redis_client)
    return FactorService(factor_dao)


@router.post("/calculate", response_model=TechnicalFactorResponse)
async def calculate_technical_factors(
    request: TechnicalFactorRequest,
    factor_service: FactorService = Depends(get_factor_service)
) -> TechnicalFactorResponse:
    """
    计算技术因子

    Args:
        request: 技术因子计算请求
        factor_service: 因子服务实例

    Returns:
        技术因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(f"开始计算技术因子: stock_code={request.stock_code}, factors={request.factors}")
# 调用因子服务计算技术因子
        result = await factor_service.calculate_technical_factors(request)

        logger.info(f"技术因子计算完成: stock_code={request.stock_code}")
        return result

    except DataNotFoundError as e:
        logger.error(f"数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FactorCalculationException as e:
        logger.error(f"技术因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"技术因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e



@router.get("/history", response_model=TechnicalFactorHistoryResponse)
async def get_technical_factor_history(
    stock_code: str = Query(..., description="股票代码"),
    factor_name: str = Query(..., description="因子名称"),
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD"),
    factor_service: FactorService = Depends(get_factor_service)
) -> TechnicalFactorHistoryResponse:
    """
    查询技术因子历史数据

    Args:
        stock_code: 股票代码
        factor_name: 因子名称
        start_date: 开始日期
        end_date: 结束日期
        factor_service: 因子服务实例

    Returns:
        技术因子历史数据

    Raises:
        HTTPException: 当查询失败时抛出异常
    """
    try:
        logger.info(f"查询技术因子历史数据: stock_code={stock_code}, factor={factor_name}")

        result = await factor_service.get_technical_factor_history(
            stock_code=stock_code,
            factor_name=factor_name,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"技术因子历史数据查询完成: stock_code={stock_code}, 记录数={len(result.data)}")
        return result

    except DataNotFoundError as e:
        logger.error(f"历史数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"技术因子历史数据查询异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/batch-calculate", response_model=BatchTechnicalFactorResponse)
async def batch_calculate_technical_factors(
    request: BatchTechnicalFactorRequest,
    factor_service: FactorService = Depends(get_factor_service)
) -> BatchTechnicalFactorResponse:
    """
    批量计算技术因子

    Args:
        request: 批量技术因子计算请求
        factor_service: 因子服务实例

    Returns:
        批量技术因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(f"开始批量计算技术因子: stock_codes={len(request.stock_codes)}, factors={request.factors}")
# 调用因子服务批量计算技术因子
        result = await factor_service.batch_calculate_technical_factors(request)

        logger.info(f"批量技术因子计算完成: 处理股票数={len(request.stock_codes)}")
        return result

    except FactorCalculationException as e:
        logger.error(f"批量因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"批量技术因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e
