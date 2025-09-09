"""回测任务管理API端点"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from ...models.task_models import TaskRequest, TaskStatus
from ...services.task_manager import TaskManager
from ....utils.exceptions import DataNotFoundError, ValidationException

router = APIRouter(prefix="/backtest-task", tags=["backtest-task"])


class TaskCreateRequest(BaseModel):
    """任务创建请求模型"""
    task_name: str = Field(..., description="任务名称")
    stock_code: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(default=1000000.0, description="初始资金")
    factor_combination_id: str | None = Field(default=None, description="因子组合ID")
    batch_id: str | None = Field(default=None, description="批次ID")
    config: dict[str, Any] = Field(default_factory=dict, description="任务配置")


class TaskCreateResponse(BaseModel):
    """任务创建响应模型"""
    task_id: str = Field(..., description="任务ID")
    batch_id: str | None = Field(..., description="批次ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    batch_id: str | None = Field(..., description="批次ID")
    stock_code: str = Field(..., description="股票代码")
    created_at: str | None = Field(default=None, description="创建时间")
    started_at: str | None = Field(default=None, description="开始时间")
    completed_at: str | None = Field(default=None, description="完成时间")
    error_message: str | None = Field(default=None, description="错误信息")
    backtest_result_id: str | None = Field(default=None, description="回测结果ID")


class TaskResultResponse(BaseModel):
    """任务结果响应模型"""
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    backtest_result_id: str = Field(..., description="回测结果ID")
    created_at: str | None = Field(default=None, description="创建时间")
    started_at: str | None = Field(default=None, description="开始时间")
    completed_at: str | None = Field(default=None, description="完成时间")
    duration: float | None = Field(default=None, description="执行时长(秒)")
    error_message: str | None = Field(default=None, description="错误信息")


class BatchTasksResponse(BaseModel):
    """批次任务响应模型"""
    batch_id: str = Field(..., description="批次ID")
    tasks: list[TaskStatusResponse] = Field(..., description="任务列表")
    total_count: int = Field(..., description="任务总数")


class TaskCancelResponse(BaseModel):
    """任务取消响应模型"""
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否取消成功")
    message: str = Field(..., description="响应消息")


@router.post("/createTask", response_model=TaskCreateResponse, summary="创建回测任务")
async def create_task(request: TaskCreateRequest) -> TaskCreateResponse:
    """创建回测任务

    Args:
        request: 任务创建请求

    Returns:
        任务创建结果

    Raises:
        HTTPException: 参数验证失败或创建失败
    """
    try:
        logger.info(f"收到任务创建请求: {request.task_name}")

        # 转换为TaskRequest
        task_request = TaskRequest(
            task_name=request.task_name,
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            factor_combination_id=request.factor_combination_id,
            batch_id=request.batch_id,
            config=request.config
        )

        # 创建任务
        task_manager = TaskManager()
        task_info = await task_manager.create_task(task_request)

        return TaskCreateResponse(
            task_id=task_info.task_id,
            batch_id=task_info.batch_id,
            status=task_info.status.value,
            message="任务创建成功"
        )

    except ValidationException as e:
        logger.error(f"任务创建参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"任务创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}") from e


@router.get("/getTaskStatus", response_model=TaskStatusResponse, summary="查询任务状态")
async def get_task_status(task_id: str = Query(..., description="任务ID")) -> TaskStatusResponse:
    """查询任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息

    Raises:
        HTTPException: 任务不存在或查询失败
    """
    try:
        logger.info(f"查询任务状态: {task_id}")

        task_manager = TaskManager()
        task_info = await task_manager.get_task_status(task_id)

        return TaskStatusResponse(
            task_id=task_info.task_id,
            task_name=task_info.task_name,
            status=task_info.status.value,
            batch_id=task_info.batch_id,
            stock_code=task_info.stock_code,
            created_at=task_info.created_at.isoformat() if task_info.created_at else None,
            started_at=task_info.started_at.isoformat() if task_info.started_at else None,
            completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
            error_message=task_info.error_message,
            backtest_result_id=task_info.backtest_result_id
        )

    except DataNotFoundError as e:
        logger.error(f"任务不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}") from e


@router.get("/getTasksByBatch", response_model=BatchTasksResponse, summary="按批次查询任务")
async def get_tasks_by_batch(batch_id: str = Query(..., description="批次ID")) -> BatchTasksResponse:
    """按批次查询任务列表

    Args:
        batch_id: 批次ID

    Returns:
        批次任务列表

    Raises:
        HTTPException: 查询失败
    """
    try:
        logger.info(f"查询批次任务: {batch_id}")

        task_manager = TaskManager()
        task_infos = await task_manager.get_tasks_by_batch(batch_id)

        tasks = []
        for task_info in task_infos:
            tasks.append(TaskStatusResponse(
                task_id=task_info.task_id,
                task_name=task_info.task_name,
                status=task_info.status.value,
                batch_id=task_info.batch_id,
                stock_code=task_info.stock_code,
                created_at=task_info.created_at.isoformat() if task_info.created_at else None,
                started_at=task_info.started_at.isoformat() if task_info.started_at else None,
                completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
                error_message=task_info.error_message,
                backtest_result_id=task_info.backtest_result_id
            ))

        return BatchTasksResponse(
            batch_id=batch_id,
            tasks=tasks,
            total_count=len(tasks)
        )

    except Exception as e:
        logger.error(f"查询批次任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询批次任务失败: {str(e)}") from e


@router.post("/cancelTask", response_model=TaskCancelResponse, summary="取消任务")
async def cancel_task(task_id: str = Query(..., description="任务ID")) -> TaskCancelResponse:
    """取消任务

    Args:
        task_id: 任务ID

    Returns:
        任务取消结果

    Raises:
        HTTPException: 任务不存在或取消失败
    """
    try:
        logger.info(f"取消任务: {task_id}")

        task_manager = TaskManager()
        success = await task_manager.cancel_task(task_id)

        return TaskCancelResponse(
            task_id=task_id,
            success=success,
            message="任务取消成功" if success else "任务取消失败"
        )

    except DataNotFoundError as e:
        logger.error(f"任务不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValidationException as e:
        logger.error(f"任务取消验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}") from e


@router.get("/getTaskResult", response_model=TaskResultResponse, summary="查询任务结果")
async def get_task_result(task_id: str = Query(..., description="任务ID")) -> TaskResultResponse:
    """查询任务执行结果

    Args:
        task_id: 任务ID

    Returns:
        任务执行结果

    Raises:
        HTTPException: 任务不存在或结果不存在
    """
    try:
        logger.info(f"查询任务结果: {task_id}")

        task_manager = TaskManager()
        result = await task_manager.get_task_result(task_id)

        return TaskResultResponse(
            task_id=result['task_id'],
            task_name=result['task_name'],
            status=result['status'],
            backtest_result_id=result['backtest_result_id'],
            created_at=result['created_at'],
            started_at=result['started_at'],
            completed_at=result['completed_at'],
            duration=result['duration'],
            error_message=result['error_message']
        )

    except DataNotFoundError as e:
        logger.error(f"任务结果不存在: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"查询任务结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务结果失败: {str(e)}") from e


@router.get("/listTasks", response_model=list[TaskStatusResponse], summary="列表查询任务")
async def list_tasks(
    status: str | None = Query(default=None, description="任务状态过滤"),
    batch_id: str | None = Query(default=None, description="批次ID过滤"),
    skip: int = Query(default=0, ge=0, description="跳过的记录数"),
    limit: int = Query(default=100, ge=1, le=1000, description="限制返回的记录数")
) -> list[TaskStatusResponse]:
    """列表查询任务

    Args:
        status: 任务状态过滤
        batch_id: 批次ID过滤
        skip: 跳过的记录数
        limit: 限制返回的记录数

    Returns:
        任务列表

    Raises:
        HTTPException: 查询失败
    """
    try:
        logger.info(f"列表查询任务: status={status}, batch_id={batch_id}, skip={skip}, limit={limit}")

        # 转换状态参数
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}") from None

        task_manager = TaskManager()
        task_infos = await task_manager.list_tasks(
            status=task_status,
            batch_id=batch_id,
            skip=skip,
            limit=limit
        )

        tasks = []
        for task_info in task_infos:
            tasks.append(TaskStatusResponse(
                task_id=task_info.task_id,
                task_name=task_info.task_name,
                status=task_info.status.value,
                batch_id=task_info.batch_id,
                stock_code=task_info.stock_code,
                created_at=task_info.created_at.isoformat() if task_info.created_at else None,
                started_at=task_info.started_at.isoformat() if task_info.started_at else None,
                completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
                error_message=task_info.error_message,
                backtest_result_id=task_info.backtest_result_id
            ))

        return tasks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列表查询任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列表查询任务失败: {str(e)}") from e
