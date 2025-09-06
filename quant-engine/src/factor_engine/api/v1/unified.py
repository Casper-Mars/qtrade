"""统一因子计算API接口模块

提供统一因子计算的RESTful API接口，包括：
- 计算所有类型因子
- 批量计算所有类型因子
- 查询统一因子历史数据
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from sqlalchemy.orm import Session

from src.utils.exceptions import DataNotFoundError, FactorCalculationException

from ....clients.tushare_client import TushareClient
from ....config.database import get_db_session
from ....config.redis import get_redis_client
from ...dao.factor_dao import FactorDAO
from ...models.schemas import (
    BatchUnifiedFactorRequest,
    BatchUnifiedFactorResponse,
    UnifiedFactorHistoryResponse,
    UnifiedFactorRequest,
    UnifiedFactorResponse,
)
from ...services.factor_service import FactorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified", tags=["unified-factors"])


async def get_factor_service(
    db_session: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis_client),
) -> FactorService:
    """获取因子服务实例"""
    factor_dao = FactorDAO(db_session, redis_client)
    data_client = TushareClient()
    await data_client.initialize()  # 确保TushareClient被正确初始化
    return FactorService(factor_dao, data_client)


@router.post("/calculate", response_model=UnifiedFactorResponse)
async def calculate_all_factors(
    request: UnifiedFactorRequest,
    factor_service: FactorService = Depends(get_factor_service),
) -> UnifiedFactorResponse:
    """
    计算所有类型的因子

    Args:
        request: 统一因子计算请求
        factor_service: 因子服务实例

    Returns:
        统一因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(
            f"开始计算统一因子: stock_code={request.stock_code}, "
            f"factor_types={request.factor_types}"
        )

        # 调用因子服务计算所有因子
        result = await factor_service.calculate_all_factors(request)

        logger.info(f"统一因子计算完成: stock_code={request.stock_code}")
        return result

    except DataNotFoundError as e:
        logger.error(f"数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FactorCalculationException as e:
        logger.error(f"统一因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"统一因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/batch-calculate", response_model=BatchUnifiedFactorResponse)
async def batch_calculate_all_factors(
    request: BatchUnifiedFactorRequest,
    factor_service: FactorService = Depends(get_factor_service),
) -> BatchUnifiedFactorResponse:
    """
    批量计算所有类型的因子

    Args:
        request: 批量统一因子计算请求
        factor_service: 因子服务实例

    Returns:
        批量统一因子计算结果

    Raises:
        HTTPException: 当计算失败时抛出异常
    """
    try:
        logger.info(
            f"开始批量计算统一因子: stock_codes={len(request.stock_codes)}, "
            f"factor_types={request.factor_types}"
        )

        # 调用因子服务批量计算所有因子
        result = await factor_service.batch_calculate_all_factors(request)

        logger.info(
            f"批量统一因子计算完成: 处理股票数={len(request.stock_codes)}, "
            f"成功={result.successful_stocks}, 失败={result.failed_stocks}"
        )
        return result

    except DataNotFoundError as e:
        logger.error(f"数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FactorCalculationException as e:
        logger.error(f"批量统一因子计算失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"批量统一因子计算异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.get("/history", response_model=UnifiedFactorHistoryResponse)
async def get_all_factors_history(
    stock_code: str = Query(..., description="股票代码"),
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD"),
    technical_factors: str = Query(None, description="技术因子列表，逗号分隔"),
    fundamental_factors: str = Query(None, description="基本面因子列表，逗号分隔"),
    market_factors: str = Query(None, description="市场因子列表，逗号分隔"),
    factor_service: FactorService = Depends(get_factor_service),
) -> UnifiedFactorHistoryResponse:
    """
    查询所有类型因子的历史数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        technical_factors: 技术因子列表（可选）
        fundamental_factors: 基本面因子列表（可选）
        market_factors: 市场因子列表（可选）
        factor_service: 因子服务实例

    Returns:
        统一因子历史数据

    Raises:
        HTTPException: 当查询失败时抛出异常
    """
    try:
        logger.info(
            f"查询统一因子历史数据: stock_code={stock_code}, "
            f"start_date={start_date}, end_date={end_date}"
        )

        # 解析因子列表参数
        tech_factors_list = technical_factors.split(",") if technical_factors else None
        fund_factors_list = fundamental_factors.split(",") if fundamental_factors else None
        market_factors_list = market_factors.split(",") if market_factors else None

        # 调用因子服务查询历史数据
        result = await factor_service.get_all_factors_history(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            technical_factors=tech_factors_list,
            fundamental_factors=fund_factors_list,
            market_factors=market_factors_list,
        )

        logger.info(
            f"统一因子历史数据查询完成: stock_code={stock_code}, "
            f"技术因子记录数={result.data_summary['technical_count']}, "
            f"基本面因子记录数={result.data_summary['fundamental_count']}, "
            f"市场因子记录数={result.data_summary['market_count']}"
        )
        return result

    except DataNotFoundError as e:
        logger.error(f"历史数据未找到: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"统一因子历史数据查询异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e
