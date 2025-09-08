"""因子组合配置API接口模块

提供因子组合配置管理的RESTful API接口，包括：
- 创建因子组合配置
- 获取因子组合配置
- 更新因子组合配置
- 删除因子组合配置
- 查询配置列表
- 按股票代码查询配置
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from ...dao.factor_combination_dao import FactorCombinationDAO
from ...models.factor_combination import (
    FactorCombinationCreateRequest,
    FactorCombinationDeleteRequest,
    FactorCombinationGetByStockRequest,
    FactorCombinationListRequest,
    FactorCombinationListResponse,
    FactorCombinationResponse,
    FactorCombinationUpdateRequest,
    FactorConfigGetRequest,
)
from ...services.factor_combination_manager import FactorCombinationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/factor-config", tags=["factor-config"])


async def get_factor_combination_manager() -> FactorCombinationManager:
    """获取因子组合管理器实例"""
    factor_dao = FactorCombinationDAO()
    return FactorCombinationManager(dao=factor_dao)


@router.post("/create", response_model=FactorCombinationResponse)
async def create_factor_config(
    request: FactorCombinationCreateRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> FactorCombinationResponse:
    """创建因子组合配置

    Args:
        request: 创建请求参数
        manager: 因子组合管理器

    Returns:
        创建的因子组合配置信息

    Raises:
        HTTPException: 当创建失败时抛出异常
    """
    try:
        logger.info(f"创建因子组合配置: {request.stock_code}")

        # 转换字段类型
        technical_factors = request.technical_factors if isinstance(request.technical_factors, list) else []
        fundamental_factors = request.fundamental_factors if isinstance(request.fundamental_factors, list) else []
        sentiment_factors = request.sentiment_factors if isinstance(request.sentiment_factors, list) else []
        factor_weights = request.factor_weights if isinstance(request.factor_weights, dict) else {}

        # 创建因子组合配置
        combination = await manager.create_combination(
            stock_code=request.stock_code,
            description=request.description,
            technical_factors=technical_factors,
            fundamental_factors=fundamental_factors,
            sentiment_factors=sentiment_factors,
            factor_weights=factor_weights,
        )

        logger.info(f"因子组合配置创建成功: {combination.config_id}")
        return FactorCombinationResponse(
            code=200,
            message="配置创建成功",
            data=combination,
        )

    except ValueError as e:
        logger.error(f"创建因子组合配置失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"创建因子组合配置异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e




@router.post("/get", response_model=FactorCombinationResponse)
async def get_factor_config(
    request: FactorConfigGetRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> FactorCombinationResponse:
    """获取因子组合配置

    Args:
        request: 获取请求参数
        manager: 因子组合管理器

    Returns:
        因子组合配置信息

    Raises:
        HTTPException: 当配置不存在时抛出异常
    """
    try:
        logger.info(f"获取因子组合配置: {request.config_id}")

        combination = await manager.get_combination(request.config_id)
        if not combination:
            raise HTTPException(status_code=404, detail="配置不存在")

        return FactorCombinationResponse(
            code=200,
            message="查询成功",
            data=combination,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取因子组合配置异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/update", response_model=FactorCombinationResponse)
async def update_factor_config(
    request: FactorCombinationUpdateRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> FactorCombinationResponse:
    """更新因子组合配置

    Args:
        request: 更新请求参数
        manager: 因子组合管理器

    Returns:
        更新后的因子组合配置信息

    Raises:
        HTTPException: 当更新失败时抛出异常
    """
    try:
        logger.info(f"更新因子组合配置: {request.config_id}")

        # 构建更新数据
        update_data: dict[str, str | list[str] | dict[str, float]] = {}
        if request.description is not None:
            update_data["description"] = request.description
        if request.technical_factors is not None:
            update_data["technical_factors"] = list(request.technical_factors)
        if request.fundamental_factors is not None:
            update_data["fundamental_factors"] = list(request.fundamental_factors)
        if request.sentiment_factors is not None:
            update_data["sentiment_factors"] = list(request.sentiment_factors)
        if request.factor_weights is not None:
            update_data["factor_weights"] = dict(request.factor_weights)

        combination = await manager.update_combination(
            request.config_id, update_data
        )

        if not combination:
            raise HTTPException(status_code=404, detail="配置不存在")

        logger.info(f"因子组合配置更新成功: {combination.config_id}")
        return FactorCombinationResponse(
            code=200,
            message="配置更新成功",
            data=combination,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"更新因子组合配置失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"更新因子组合配置异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/delete")
async def delete_factor_config(
    request: FactorCombinationDeleteRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> dict:
    """删除因子组合配置

    Args:
        request: 删除请求参数
        manager: 因子组合管理器

    Returns:
        删除结果

    Raises:
        HTTPException: 当删除失败时抛出异常
    """
    try:
        logger.info(f"删除因子组合配置: {request.config_id}")

        success = await manager.delete_combination(request.config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")

        logger.info(f"因子组合配置删除成功: {request.config_id}")
        return {
            "code": 200,
            "message": "配置删除成功",
            "data": {
                "config_id": request.config_id,
                "deleted_at": None,  # 实际项目中可以添加删除时间
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除因子组合配置异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/list", response_model=FactorCombinationListResponse)
async def list_factor_configs(
    request: FactorCombinationListRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> FactorCombinationListResponse:
    """获取配置列表

    Args:
        request: 列表查询请求参数
        manager: 因子组合管理器

    Returns:
        配置列表信息

    Raises:
        HTTPException: 当查询失败时抛出异常
    """
    try:
        logger.info(f"查询因子组合配置列表: page={request.page}, size={request.size}")

        # 这里简化实现，实际项目中需要在DAO层实现分页查询
        # 模拟返回数据
        from ...models.factor_combination import FactorCombinationListData

        mock_data = FactorCombinationListData(
            configs=[],
            total=0,
            page=request.page,
            size=request.size,
        )

        return FactorCombinationListResponse(
            code=200,
            message="查询成功",
            data=mock_data,
        )

    except Exception as e:
        logger.error(f"查询因子组合配置列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e


@router.post("/get-by-stock", response_model=FactorCombinationResponse)
async def get_factor_config_by_stock(
    request: FactorCombinationGetByStockRequest,
    manager: FactorCombinationManager = Depends(get_factor_combination_manager),
) -> FactorCombinationResponse:
    """按股票代码查询配置

    Args:
        request: 按股票查询请求参数
        manager: 因子组合管理器

    Returns:
        因子组合配置信息

    Raises:
        HTTPException: 当配置不存在时抛出异常
    """
    try:
        logger.info(f"按股票代码查询因子组合配置: {request.stock_code}")

        # 这里简化实现，实际项目中需要在DAO层实现按股票代码查询
        # 目前返回404作为示例
        raise HTTPException(
            status_code=404, detail="该股票暂无因子组合配置"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"按股票代码查询因子组合配置异常: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误") from e
