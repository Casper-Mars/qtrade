"""任务数据访问层

本模块实现了任务管理的数据访问功能，包括任务的CRUD操作和查询功能。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select, update

from ...config.connection_pool import get_db_session
from ..models.database import BacktestTaskTable
from ..models.task_models import TaskInfo, TaskStatus
from .base import BaseDAO


class TaskDAO(BaseDAO[BacktestTaskTable]):
    """任务数据访问对象

    提供任务的数据库操作功能，包括创建、查询、更新和删除任务。
    """

    def __init__(self) -> None:
        """初始化任务数据访问对象"""
        pass

    async def create(self, obj: BacktestTaskTable) -> BacktestTaskTable:
        """创建任务

        Args:
            obj: 任务对象

        Returns:
            创建的任务对象
        """
        async with get_db_session() as session:
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def get_by_id(self, task_id: str | UUID) -> BacktestTaskTable | None:
        """根据任务ID获取任务

        Args:
            task_id: 任务ID（字符串或UUID）

        Returns:
            任务对象，如果不存在则返回None
        """
        # 如果是字符串，转换为UUID
        if isinstance(task_id, str):
            try:
                task_id = UUID(task_id)
            except ValueError:
                return None

        async with get_db_session() as session:
            stmt = select(BacktestTaskTable).where(BacktestTaskTable.id == task_id)
            result = await session.execute(stmt)
            task: BacktestTaskTable | None = result.scalar_one_or_none()
            return task

    async def update(self, obj: BacktestTaskTable) -> BacktestTaskTable:
        """更新任务

        Args:
            obj: 任务对象

        Returns:
            更新后的任务对象
        """
        async with get_db_session() as session:
            # 将对象合并到当前会话
            merged_obj: BacktestTaskTable = await session.merge(obj)
            await session.commit()
            await session.refresh(merged_obj)
            return merged_obj

    async def delete(self, task_id: str | UUID) -> bool:
        """删除任务

        Args:
            task_id: 任务ID（字符串或UUID）

        Returns:
            是否删除成功
        """
        # 如果是字符串，转换为UUID
        if isinstance(task_id, str):
            try:
                task_id = UUID(task_id)
            except ValueError:
                return False

        task = await self.get_by_id(task_id)
        if task:
            async with get_db_session() as session:
                # 重新获取对象以确保在当前会话中
                stmt = select(BacktestTaskTable).where(BacktestTaskTable.id == task_id)
                result = await session.execute(stmt)
                task_to_delete = result.scalar_one_or_none()
                if task_to_delete:
                    await session.delete(task_to_delete)
                    await session.commit()
                    return True
        return False

    async def list_objects(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[BacktestTaskTable]:
        """列表查询任务

        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            **filters: 过滤条件

        Returns:
            任务列表
        """
        async with get_db_session() as session:
            stmt = select(BacktestTaskTable)

            # 应用过滤条件
            if 'status' in filters:
                stmt = stmt.where(BacktestTaskTable.status == filters['status'])
            if 'batch_id' in filters:
                stmt = stmt.where(BacktestTaskTable.batch_id == filters['batch_id'])

            stmt = stmt.order_by(desc(BacktestTaskTable.created_at))
            stmt = stmt.offset(skip).limit(limit)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """计数查询

        Args:
            **filters: 过滤条件

        Returns:
            符合条件的记录数
        """
        async with get_db_session() as session:
            stmt = select(BacktestTaskTable)

            # 应用过滤条件
            if 'status' in filters:
                stmt = stmt.where(BacktestTaskTable.status == filters['status'])
            if 'batch_id' in filters:
                stmt = stmt.where(BacktestTaskTable.batch_id == filters['batch_id'])

            result = await session.execute(stmt)
            return len(list(result.scalars().all()))

    async def save_task(self, task_info: TaskInfo) -> BacktestTaskTable:
        """保存任务信息

        Args:
            task_info: 任务信息对象

        Returns:
            保存的数据库任务对象
        """
        # 转换TaskInfo为数据库模型
        db_task = BacktestTaskTable(
            id=task_info.task_id,
            batch_id=task_info.batch_id,
            name=task_info.task_name,
            description=f"股票{task_info.stock_code}的回测任务",
            status=task_info.status.value,
            config={
                'stock_code': task_info.stock_code,
                'start_date': task_info.start_date,
                'end_date': task_info.end_date,
                'initial_capital': task_info.initial_capital,
                'factor_combination_id': task_info.factor_combination_id,
                **task_info.config
            },
            result_id=task_info.backtest_result_id,
            error_message=task_info.error_message,
            progress=task_info.progress,
            created_at=task_info.created_at,
            updated_at=task_info.updated_at,
            started_at=task_info.started_at,
            completed_at=task_info.completed_at
        )

        return await self.create(db_task)

    async def update_task_status(self, task_id: str, status: TaskStatus,
                                error_message: str | None = None,
                                result_id: str | None = None,
                                progress: float | None = None) -> bool:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            result_id: 结果ID
            progress: 进度

        Returns:
            是否更新成功
        """
        task = await self.get_by_id(task_id)
        if not task:
            return False

        # 更新状态
        task.status = status.value
        task.updated_at = datetime.utcnow()  # type: ignore[assignment]

        if error_message is not None:
            task.error_message = error_message

        if result_id is not None:
            task.result_id = result_id

        if progress is not None:
            task.progress = progress

        # 根据状态更新时间字段
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.utcnow()  # type: ignore[assignment]
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.utcnow()  # type: ignore[assignment]

        await self.update(task)
        return True

    async def get_tasks_by_batch(self, batch_id: str) -> list[BacktestTaskTable]:
        """根据批次ID获取任务列表

        Args:
            batch_id: 批次ID

        Returns:
            任务列表
        """
        return await self.list_objects(batch_id=batch_id)

    async def get_pending_tasks(self, limit: int = 10) -> list[BacktestTaskTable]:
        """获取待执行的任务

        Args:
            limit: 限制返回的任务数

        Returns:
            待执行任务列表
        """
        return await self.list_objects(status=TaskStatus.PENDING.value, limit=limit)

    async def batch_create_tasks(self, tasks: list[BacktestTaskTable]) -> list[BacktestTaskTable]:
        """批量创建任务

        Args:
            tasks: 任务对象列表

        Returns:
            创建的任务对象列表
        """
        async with get_db_session() as session:
            session.add_all(tasks)
            await session.commit()
            for task in tasks:
                await session.refresh(task)
            return tasks

    async def batch_update_status(self, task_ids: list[str], status: TaskStatus) -> int:
        """批量更新任务状态

        Args:
            task_ids: 任务ID列表
            status: 新状态

        Returns:
            更新的任务数量
        """
        # 转换字符串ID为UUID
        uuid_ids = []
        for task_id in task_ids:
            try:
                uuid_ids.append(UUID(task_id))
            except ValueError:
                # 跳过无效的UUID
                pass

        if not uuid_ids:
            return 0

        async with get_db_session() as session:
            stmt = (
                update(BacktestTaskTable)
                .where(BacktestTaskTable.id.in_(uuid_ids))
                .values(status=status.value, updated_at=datetime.utcnow())
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount or 0

    async def batch_save_tasks(self, task_infos: list[TaskInfo]) -> list[BacktestTaskTable]:
        """批量保存任务信息

        Args:
            task_infos: 任务信息对象列表

        Returns:
            保存的数据库任务对象列表
        """
        db_tasks = []
        for task_info in task_infos:
            db_task = BacktestTaskTable(
                id=task_info.task_id,
                batch_id=task_info.batch_id,
                name=task_info.task_name,
                description=f"股票{task_info.stock_code}的回测任务",
                status=task_info.status.value,
                config={
                    'stock_code': task_info.stock_code,
                    'start_date': task_info.start_date,
                    'end_date': task_info.end_date,
                    'initial_capital': task_info.initial_capital,
                    'factor_combination_id': task_info.factor_combination_id,
                    **task_info.config
                },
                result_id=task_info.backtest_result_id,
                error_message=task_info.error_message,
                progress=task_info.progress,
                created_at=task_info.created_at,
                updated_at=task_info.updated_at,
                started_at=task_info.started_at,
                completed_at=task_info.completed_at
            )
            db_tasks.append(db_task)

        return await self.batch_create_tasks(db_tasks)

    async def execute_in_transaction(self, operations: list) -> bool:
        """在事务中执行多个操作

        Args:
            operations: 操作列表，每个操作是一个可调用对象

        Returns:
            是否执行成功
        """
        async with get_db_session() as session:
            try:
                # 开始事务
                for operation in operations:
                    await operation()

                # 提交事务
                await session.commit()
                return True
            except Exception:
                # 回滚事务
                await session.rollback()
                return False

    async def get_task_statistics(self, batch_id: str | None = None) -> dict[str, int]:
        """获取任务统计信息

        Args:
            batch_id: 批次ID，如果为None则统计所有任务

        Returns:
            任务统计信息字典
        """
        from sqlalchemy import func

        stmt = select(
            BacktestTaskTable.status,
            func.count(BacktestTaskTable.id).label('count')
        )

        if batch_id:
            stmt = stmt.where(BacktestTaskTable.batch_id == batch_id)

        stmt = stmt.group_by(BacktestTaskTable.status)

        async with get_db_session() as session:
            result = await session.execute(stmt)
            statistics: dict[str, int] = {}

            for row in result:
                statistics[str(row.status)] = int(row[1])  # row[1] is the count column

            return statistics

    async def convert_to_task_info(self, db_task: BacktestTaskTable) -> TaskInfo:
        """将数据库任务对象转换为TaskInfo

        Args:
            db_task: 数据库任务对象

        Returns:
            TaskInfo对象
        """
        config = db_task.config or {}

        return TaskInfo(
            task_id=str(db_task.id),
            batch_id=str(db_task.batch_id) if db_task.batch_id else None,
            task_name=str(db_task.name),
            stock_code=config.get('stock_code', ''),
            start_date=config.get('start_date', ''),
            end_date=config.get('end_date', ''),
            initial_capital=config.get('initial_capital', 1000000.0),
            factor_combination_id=config.get('factor_combination_id'),
            config={k: v for k, v in config.items() if k not in [
                'stock_code', 'start_date', 'end_date', 'initial_capital', 'factor_combination_id'
            ]},
            status=TaskStatus(db_task.status),
            progress=float(db_task.progress or 0),
            error_message=db_task.error_message,
            backtest_result_id=db_task.result_id,
            created_at=db_task.created_at.replace(tzinfo=None) if db_task.created_at else datetime.now(),
            started_at=db_task.started_at.replace(tzinfo=None) if db_task.started_at else None,
            completed_at=db_task.completed_at.replace(tzinfo=None) if db_task.completed_at else None,
            updated_at=db_task.updated_at.replace(tzinfo=None) if db_task.updated_at else datetime.now()
        )
