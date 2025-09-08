"""基本面因子API接口模块

提供基本面因子计算的RESTful API接口，包括：
- 计算单个基本面因子
- 查询基本面因子历史数据
- 批量计算基本面因子
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from redis import Redis
from sqlalchemy.orm import Session

from src.clients.tushare_client import TushareClient
from src.config.database import get_db_session
from src.config.redis import get_redis_client
from src.factor_engine.dao.factor_dao import FactorDAO
from src.factor_engine.models.schemas import (
    BatchFundamentalFactorRequest,
    BatchFundamentalFactorResponse,
    FundamentalFactorRequest,
    FundamentalFactorResponse,
)
from src.factor_engine.services.factor_service import FactorService
from src.utils.exceptions import DataNotFoundError, FactorCalculationException

router = APIRouter(prefix="/fundamental", tags=["fundamental-factors"])


@router.post("/calculate", response_model=FundamentalFactorResponse)
async def calculate_fundamental_factors(
    request: FundamentalFactorRequest,
    db_session: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> FundamentalFactorResponse:
    """
    计算基本面因子

    Args:
        request: 基本面因子计算请求
        db_session: 数据库会话
        redis_client: Redis客户端

    Returns:
        基本面因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(
            f"开始计算基本面因子: stock_code={request.stock_code}, period={request.period}"
        )

        # 使用async with确保TushareClient在整个请求生命周期内保持活跃
        async with TushareClient() as data_client:
            factor_dao = FactorDAO(db_session, redis_client)
            factor_service = FactorService(factor_dao, data_client)

            # 调用因子服务计算基本面因子
            result = await factor_service.calculate_fundamental_factors(request)

        logger.info(f"基本面因子计算完成: stock_code={request.stock_code}")
        return result

    except DataNotFoundError as e:
        logger.error(f"数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FactorCalculationException as e:
        logger.error(f"基本面因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"基本面因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.get("/history")
async def get_fundamental_factor_history(
    stock_code: str = Query(..., description="股票代码"),
    factor_name: str = Query(..., description="因子名称"),
    start_period: str = Query(..., description="开始期间，格式：YYYY-Q[1-4] 或 YYYY"),
    end_period: str = Query(..., description="结束期间，格式：YYYY-Q[1-4] 或 YYYY"),
    db_session: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> list[dict]:
    """
    查询基本面因子历史数据

    Args:
        stock_code: 股票代码
        factor_name: 因子名称
        start_period: 开始期间
        end_period: 结束期间
        db_session: 数据库会话
        redis_client: Redis客户端

    Returns:
        基本面因子历史数据

    Raises:
        HTTPException: 当查询失败时抛出异常
    """
    try:
        logger.info(
            f"查询基本面因子历史数据: stock_code={stock_code}, factor={factor_name}"
        )

        # 使用async with确保TushareClient在整个请求生命周期内保持活跃
        async with TushareClient() as data_client:
            factor_dao = FactorDAO(db_session, redis_client)
            factor_service = FactorService(factor_dao, data_client)

            result = await factor_service.get_fundamental_factor_history(
                stock_code=stock_code,
                factor_name=factor_name,
                start_period=start_period,
                end_period=end_period,
            )

        logger.info(
            f"基本面因子历史数据查询完成: stock_code={stock_code}, 记录数={len(result)}"
        )
        return result

    except DataNotFoundError as e:
        logger.error(f"历史数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"基本面因子历史数据查询异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/batch-calculate", response_model=BatchFundamentalFactorResponse)
async def batch_calculate_fundamental_factors(
    request: BatchFundamentalFactorRequest,
    db_session: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> BatchFundamentalFactorResponse:
    """
    批量计算基本面因子

    Args:
        request: 批量基本面因子计算请求
        db_session: 数据库会话
        redis_client: Redis客户端

    Returns:
        批量基本面因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(
            f"开始批量计算基本面因子: stock_codes={len(request.stock_codes)}, period={request.period}"
        )

        # 使用async with确保TushareClient在整个请求生命周期内保持活跃
        async with TushareClient() as data_client:
            factor_dao = FactorDAO(db_session, redis_client)
            factor_service = FactorService(factor_dao, data_client)

            # 调用因子服务批量计算基本面因子
            result = await factor_service.batch_calculate_fundamental_factors(request)

        logger.info(f"批量基本面因子计算完成: 处理股票数={len(request.stock_codes)}")
        return result

    except FactorCalculationException as e:
        logger.error(f"批量因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"批量基本面因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e
