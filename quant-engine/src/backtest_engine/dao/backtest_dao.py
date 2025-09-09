"""回测数据访问层

本模块实现回测结果、任务和批次的数据访问功能。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.database import (
    BacktestBatchTable,
    BacktestResultTable,
    BacktestTaskTable,
)
from .base import BaseDAO, CRUDMixin


class BacktestDAO(BaseDAO[BacktestResultTable], CRUDMixin):
    """回测数据访问对象

    提供回测结果、任务和批次的完整CRUD操作。
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.model = BacktestResultTable

    # 实现BaseDAO抽象方法
    async def create(self, obj: BacktestResultTable) -> BacktestResultTable:
        """创建对象"""
        return await self.create_result(obj)

    async def get_by_id(self, obj_id: UUID | str) -> BacktestResultTable | None:
        """根据ID获取对象"""
        return await self.get_result_by_id(obj_id)

    async def update(self, obj: BacktestResultTable) -> BacktestResultTable:
        """更新对象"""
        return await self.update_result(obj)

    async def delete(self, obj_id: UUID | str) -> bool:
        """删除对象"""
        obj = await self.get_result_by_id(obj_id)
        if obj:
            return await self.delete_obj(obj)
        return False

    async def list_objects(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[BacktestResultTable]:
        """列表查询"""
        query = select(BacktestResultTable)

        # 应用过滤条件
        if 'stock_code' in filters:
            query = query.where(BacktestResultTable.stock_code == filters['stock_code'])
        if 'start_date' in filters:
            query = query.where(BacktestResultTable.start_date >= filters['start_date'])
        if 'end_date' in filters:
            query = query.where(BacktestResultTable.end_date <= filters['end_date'])
        if 'backtest_mode' in filters:
            query = query.where(BacktestResultTable.backtest_mode == filters['backtest_mode'])
        if 'task_id' in filters:
            query = query.where(BacktestResultTable.task_id == filters['task_id'])
        if 'batch_id' in filters:
            query = query.where(BacktestResultTable.batch_id == filters['batch_id'])

        # 排序和分页
        query = query.order_by(desc(BacktestResultTable.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """计数查询"""
        query = select(func.count(BacktestResultTable.id))

        # 应用过滤条件
        if 'stock_code' in filters:
            query = query.where(BacktestResultTable.stock_code == filters['stock_code'])
        if 'start_date' in filters:
            query = query.where(BacktestResultTable.start_date >= filters['start_date'])
        if 'end_date' in filters:
            query = query.where(BacktestResultTable.end_date <= filters['end_date'])
        if 'backtest_mode' in filters:
            query = query.where(BacktestResultTable.backtest_mode == filters['backtest_mode'])
        if 'task_id' in filters:
            query = query.where(BacktestResultTable.task_id == filters['task_id'])
        if 'batch_id' in filters:
            query = query.where(BacktestResultTable.batch_id == filters['batch_id'])

        result = await self.session.execute(query)
        return result.scalar() or 0

    # BacktestResult CRUD操作
    async def create_result(self, obj: BacktestResultTable) -> BacktestResultTable:
        """创建回测结果"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_result_by_id(self, obj_id: UUID | str) -> BacktestResultTable | None:
        """根据ID获取回测结果"""
        # 如果是字符串，转换为UUID
        if isinstance(obj_id, str):
            try:
                obj_id = UUID(obj_id)
            except ValueError:
                return None

        query = select(BacktestResultTable).where(BacktestResultTable.id == obj_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_result(self, obj: BacktestResultTable) -> BacktestResultTable:
        """更新回测结果"""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_result(self, obj_id: UUID | str) -> bool:
        """删除回测结果"""
        # 如果是字符串，转换为UUID
        if isinstance(obj_id, str):
            try:
                obj_id = UUID(obj_id)
            except ValueError:
                return False

        obj = await self.get_result_by_id(obj_id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False





    # BacktestTask CRUD操作
    async def create_task(self, obj: BacktestTaskTable) -> BacktestTaskTable:
        """创建回测任务"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_task_by_id(self, obj_id: UUID) -> BacktestTaskTable | None:
        """根据ID获取回测任务"""
        query = select(BacktestTaskTable).where(BacktestTaskTable.id == obj_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_task(self, obj: BacktestTaskTable) -> BacktestTaskTable:
        """更新回测任务"""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_task(self, obj_id: UUID) -> bool:
        """删除回测任务"""
        obj = await self.get_task_by_id(obj_id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> list[BacktestTaskTable]:
        """列表查询回测任务"""
        query = select(BacktestTaskTable)

        # 应用过滤条件
        if 'batch_id' in filters:
            query = query.where(BacktestTaskTable.batch_id == filters['batch_id'])
        if 'status' in filters:
            query = query.where(BacktestTaskTable.status == filters['status'])

        # 排序和分页
        query = query.order_by(desc(BacktestTaskTable.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # BacktestBatch CRUD操作
    async def create_batch(self, obj: BacktestBatchTable) -> BacktestBatchTable:
        """创建回测批次"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_batch_by_id(self, obj_id: UUID) -> BacktestBatchTable | None:
        """根据ID获取回测批次"""
        query = select(BacktestBatchTable).where(BacktestBatchTable.id == obj_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_batch(self, obj: BacktestBatchTable) -> BacktestBatchTable:
        """更新回测批次"""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_batch(self, obj_id: UUID) -> bool:
        """删除回测批次"""
        obj = await self.get_batch_by_id(obj_id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

    # 批量操作
    async def batch_create_results(self, results: list[BacktestResultTable]) -> list[BacktestResultTable]:
        """批量创建回测结果"""
        self.session.add_all(results)
        await self.session.commit()
        for result in results:
            await self.session.refresh(result)
        return results

    async def bulk_create_results(
        self, results: list[BacktestResultTable]
    ) -> list[BacktestResultTable]:
        """批量创建回测结果"""
        self.session.add_all(results)
        await self.session.flush()
        return results

    async def bulk_update_results(
        self, updates: list[dict[str, Any]]
    ) -> int:
        """批量更新回测结果"""
        if not updates:
            return 0

        updated_count = 0
        for update_data in updates:
            result_id = update_data.get("id")
            if not result_id:
                continue

            # 构建更新语句
            stmt = (
                select(BacktestResultTable)
                .where(BacktestResultTable.id == result_id)
            )
            result = await self.session.execute(stmt)
            backtest_result = result.scalar_one_or_none()

            if backtest_result:
                # 更新字段
                for key, value in update_data.items():
                    if key != "id" and hasattr(backtest_result, key):
                        setattr(backtest_result, key, value)
                updated_count += 1

        return updated_count

    async def batch_update_task_status(
        self,
        task_ids: list[UUID],
        status: str
    ) -> int:
        """批量更新任务状态"""

        stmt = (
            update(BacktestTaskTable)
            .where(BacktestTaskTable.id.in_(task_ids))
            .values(status=status, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount or 0

    # 查询优化方法
    async def get_results_with_tasks(
        self,
        batch_id: UUID
    ) -> list[BacktestResultTable]:
        """获取包含任务信息的回测结果"""
        query = (
            select(BacktestResultTable)
            .options(selectinload(BacktestResultTable.task))
            .where(BacktestResultTable.batch_id == batch_id)
            .order_by(desc(BacktestResultTable.created_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_results(
        self, stock_code: str, limit: int = 10
    ) -> list[BacktestResultTable]:
        """获取指定股票的最新回测结果"""
        stmt = (
            select(BacktestResultTable)
            .where(BacktestResultTable.stock_code == stock_code)
            .order_by(desc(BacktestResultTable.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_performance_summary(
        self, stock_code: str | None = None
    ) -> dict[str, Any]:
        """获取绩效汇总统计"""
        # 构建统计查询
        stats_query = select(
            func.count(BacktestResultTable.id).label("total_count"),
            func.avg(BacktestResultTable.total_return).label("avg_return"),
            func.avg(BacktestResultTable.sharpe_ratio).label("avg_sharpe"),
            func.avg(BacktestResultTable.max_drawdown).label("avg_drawdown"),
            func.max(BacktestResultTable.total_return).label("best_return"),
            func.min(BacktestResultTable.total_return).label("worst_return"),
        )
        if stock_code:
            stats_query = stats_query.where(BacktestResultTable.stock_code == stock_code)

        result = await self.session.execute(stats_query)
        stats = result.first()

        if stats is None:
            return {
                "total_count": 0,
                "avg_return": 0.0,
                "avg_sharpe": 0.0,
                "avg_drawdown": 0.0,
                "best_return": 0.0,
                "worst_return": 0.0,
            }

        return {
            "total_count": int(stats.total_count or 0),
            "avg_return": float(stats.avg_return or 0),
            "avg_sharpe": float(stats.avg_sharpe or 0),
            "avg_drawdown": float(stats.avg_drawdown or 0),
            "best_return": float(stats.best_return or 0),
            "worst_return": float(stats.worst_return or 0),
        }
