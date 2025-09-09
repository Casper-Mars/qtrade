"""任务管理器

本模块实现了任务管理的核心功能，包括任务创建、状态查询、任务取消等操作。
"""

from loguru import logger
from datetime import datetime
from typing import Any
from uuid import uuid4

from ...utils.exceptions import DataNotFoundError, ValidationException
from ..dao.task_dao import TaskDAO
from ..models.task_models import TaskInfo, TaskRequest, TaskStatus


class TaskManager:
    """任务管理器

    负责任务的创建、查询、状态管理等核心功能。
    """

    def __init__(self) -> None:
        """初始化任务管理器"""
        self._task_dao: TaskDAO | None = None

    async def _get_task_dao(self) -> TaskDAO:
        """获取任务DAO实例

        Returns:
            TaskDAO实例
        """
        if self._task_dao is None:
            self._task_dao = TaskDAO()
        return self._task_dao

    async def create_task(self, request: TaskRequest) -> TaskInfo:
        """创建任务

        Args:
            request: 任务创建请求

        Returns:
            创建的任务信息

        Raises:
            ValidationException: 参数验证失败
        """
        try:
            logger.info(f"开始创建任务: {request.task_name}")

            # 基本参数验证
            await self._validate_task_request(request)

            # 生成任务ID和批次ID
            task_id = self._generate_task_id()
            batch_id = request.batch_id or self._generate_batch_id()

            # 创建TaskInfo对象
            task_info = TaskInfo.create_from_request(
                request=request,
                task_id=task_id,
                batch_id=batch_id
            )

            # 保存到数据库
            task_dao = await self._get_task_dao()
            await task_dao.save_task(task_info)

            logger.info(f"任务创建成功: {task_id}")
            return task_info

        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise ValidationException(f"创建任务失败: {str(e)}") from e

    async def get_task_status(self, task_id: str) -> TaskInfo:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息

        Raises:
            DataNotFoundError: 任务不存在
        """
        try:
            task_dao = await self._get_task_dao()
            db_task = await task_dao.get_by_id(task_id)

            if not db_task:
                raise DataNotFoundError(f"任务不存在: {task_id}")

            task_info = await task_dao.convert_to_task_info(db_task)
            return task_info

        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}")
            raise

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功

        Raises:
            DataNotFoundError: 任务不存在
            ValidationException: 任务状态不允许取消
        """
        try:
            task_dao = await self._get_task_dao()
            db_task = await task_dao.get_by_id(task_id)

            if not db_task:
                raise DataNotFoundError(f"任务不存在: {task_id}")

            current_status = TaskStatus(db_task.status)

            # 检查是否可以取消
            if not current_status.can_transition_to(TaskStatus.CANCELLED):
                raise ValidationException(f"任务状态 {current_status.value} 不允许取消")

            # 更新状态为已取消
            success = await task_dao.update_task_status(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
                error_message="任务已被用户取消"
            )

            if success:
                logger.info(f"任务已取消: {task_id}")
            else:
                logger.error(f"取消任务失败: {task_id}")

            return success

        except (DataNotFoundError, ValidationException):
            raise
        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}")
            raise

    async def get_tasks_by_batch(self, batch_id: str) -> list[TaskInfo]:
        """根据批次ID获取任务列表

        Args:
            batch_id: 批次ID

        Returns:
            任务信息列表
        """
        try:
            task_dao = await self._get_task_dao()
            db_tasks = await task_dao.get_tasks_by_batch(batch_id)

            task_infos = []
            for db_task in db_tasks:
                task_info = await task_dao.convert_to_task_info(db_task)
                task_infos.append(task_info)

            return task_infos

        except Exception as e:
            logger.error(f"获取批次任务失败: {str(e)}")
            raise

    async def get_task_result(self, task_id: str) -> dict[str, Any]:
        """获取任务执行结果

        Args:
            task_id: 任务ID

        Returns:
            任务结果信息

        Raises:
            DataNotFoundError: 任务不存在或结果不存在
        """
        try:
            task_info = await self.get_task_status(task_id)

            if not task_info.backtest_result_id:
                raise DataNotFoundError(f"任务 {task_id} 尚未有执行结果")

            # 构建结果信息
            result = {
                'task_id': task_info.task_id,
                'task_name': task_info.task_name,
                'status': task_info.status.value,
                'backtest_result_id': task_info.backtest_result_id,
                'created_at': task_info.created_at.isoformat() if task_info.created_at else None,
                'started_at': task_info.started_at.isoformat() if task_info.started_at else None,
                'completed_at': task_info.completed_at.isoformat() if task_info.completed_at else None,
                'duration': task_info.get_duration(),
                'error_message': task_info.error_message
            }

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取任务结果失败: {str(e)}")
            raise

    async def list_tasks(self, status: TaskStatus | None = None,
                        batch_id: str | None = None,
                        skip: int = 0, limit: int = 100) -> list[TaskInfo]:
        """列表查询任务

        Args:
            status: 任务状态过滤
            batch_id: 批次ID过滤
            skip: 跳过的记录数
            limit: 限制返回的记录数

        Returns:
            任务信息列表
        """
        try:
            task_dao = await self._get_task_dao()

            filters = {}
            if status:
                filters['status'] = status.value
            if batch_id:
                filters['batch_id'] = batch_id

            db_tasks = await task_dao.list_objects(skip=skip, limit=limit, **filters)

            task_infos = []
            for db_task in db_tasks:
                task_info = await task_dao.convert_to_task_info(db_task)
                task_infos.append(task_info)

            return task_infos

        except Exception as e:
            logger.error(f"列表查询任务失败: {str(e)}")
            raise

    async def _validate_task_request(self, request: TaskRequest) -> None:
        """验证任务请求参数

        Args:
            request: 任务请求

        Raises:
            ValidationException: 验证失败
        """
        # 验证日期格式和范围
        try:
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d')

            if end_date <= start_date:
                raise ValidationException("结束日期必须大于开始日期")

            # 检查日期不能是未来日期
            today = datetime.now().date()
            if end_date.date() > today:
                raise ValidationException("结束日期不能是未来日期")

        except ValueError as e:
            raise ValidationException(f"日期格式错误: {str(e)}") from e

        # 验证股票代码格式
        if not request.stock_code or len(request.stock_code) != 9:
            raise ValidationException("股票代码格式错误，应为6位数字.SH或.SZ")

        # 验证初始资金
        if request.initial_capital <= 0:
            raise ValidationException("初始资金必须大于0")

    def _generate_task_id(self) -> str:
        """生成任务ID

        Returns:
            任务ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        uuid_part = uuid4().hex[:8]
        return f"bt_{timestamp}_{uuid_part}"

    def _generate_batch_id(self) -> str:
        """生成批次ID

        Returns:
            批次ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        uuid_part = uuid4().hex[:8]
        return f"batch_{timestamp}_{uuid_part}"

    async def close(self) -> None:
        """关闭资源"""
        self._task_dao = None
