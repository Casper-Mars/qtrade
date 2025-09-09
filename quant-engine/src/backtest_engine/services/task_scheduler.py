"""任务调度器

本模块实现了任务调度的核心功能，包括任务队列管理、调度逻辑和定时任务管理。
"""

import asyncio
import logging
from typing import Any

from ..dao.task_dao import TaskDAO
from ..models.task_models import TaskInfo, TaskStatus
from .backtest_engine import BacktestEngine
from .factor_combination_manager import FactorCombinationManager

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器

    负责任务的调度执行、队列管理和定时任务处理。
    采用FIFO队列调度策略，支持任务重试和错误处理。
    """

    def __init__(self, retry_max_attempts: int = 3, db_session: Any = None) -> None:
        """初始化任务调度器

        Args:
            retry_max_attempts: 最大重试次数
            db_session: 数据库会话
        """
        self.retry_max_attempts = retry_max_attempts
        self.db_session = db_session
        self._task_dao: TaskDAO | None = None
        self._is_running = False
        self._scheduler_task: asyncio.Task[Any] | None = None
        self._backtest_engine: BacktestEngine | None = None
        self._factor_combination_manager: FactorCombinationManager | None = None



    async def _get_task_dao(self) -> TaskDAO:
        """获取TaskDAO实例（单例模式）

        Returns:
            TaskDAO实例
        """
        if self._task_dao is None:
            self._task_dao = TaskDAO()
        return self._task_dao

    async def _get_backtest_engine(self) -> BacktestEngine:
        """获取BacktestEngine实例（单例模式）

        Returns:
            BacktestEngine实例
        """
        if self._backtest_engine is None:
            from redis import Redis

            from ...clients.tushare_client import TushareClient

            # 创建必要的依赖实例
            from ...factor_engine.dao.factor_dao import FactorDAO
            from ...factor_engine.services.factor_service import FactorService

            data_client = TushareClient()
            redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)
            factor_dao = FactorDAO(db_session=self.db_session, redis_client=redis_client)
            factor_service = FactorService(factor_dao=factor_dao, data_client=data_client)

            self._backtest_engine = BacktestEngine(
                factor_service=factor_service,
                data_client=data_client,
                db_session=self.db_session
            )
        return self._backtest_engine

    async def _get_factor_combination_manager(self) -> FactorCombinationManager:
        """获取FactorCombinationManager实例（单例模式）

        Returns:
            FactorCombinationManager实例
        """
        if self._factor_combination_manager is None:
            self._factor_combination_manager = FactorCombinationManager()
        return self._factor_combination_manager

    async def start(self) -> None:
        """启动任务调度器"""
        if self._is_running:
            logger.warning("任务调度器已在运行中")
            return

        self._is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("任务调度器已启动")

    async def stop(self) -> None:
        """停止任务调度器"""
        if not self._is_running:
            return

        self._is_running = False

        # 取消调度器主循环
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        logger.info("任务调度器已停止")

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        try:
            # 更新数据库中的任务状态
            task_dao = await self._get_task_dao()
            await task_dao.update_task_status(task_id, TaskStatus.CANCELLED)
            logger.info(f"已取消任务: {task_id}")
            return True

        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}")
            return False

    async def _scheduler_loop(self) -> None:
        """调度器主循环

        每30秒检查一次数据库中的pending任务，逐个处理
        """
        logger.info("调度器主循环已启动")

        while self._is_running:
            try:
                # 从数据库查询pending任务并逐个处理
                await self._process_pending_tasks()

                # 等待30秒后进行下一轮检查
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"调度器循环出错: {str(e)}")
                await asyncio.sleep(30)

        logger.info("调度器主循环已退出")





    async def _process_pending_tasks(self) -> None:
        """处理数据库中的pending任务

        查询数据库中状态为pending的任务，按创建时间顺序逐个处理
        """
        try:
            task_dao = await self._get_task_dao()
            pending_tasks = await task_dao.get_pending_tasks(limit=50)

            if not pending_tasks:
                logger.debug("数据库中没有待执行任务")
                return

            logger.info(f"发现 {len(pending_tasks)} 个待执行任务")

            # 按创建时间顺序处理任务（FIFO）
            for db_task in pending_tasks:
                try:
                    # 转换为任务信息
                    task_info = await task_dao.convert_to_task_info(db_task)

                    # 更新任务状态为运行中
                    await task_dao.update_task_status(task_info.task_id, TaskStatus.RUNNING)

                    # 执行任务（集成BacktestEngine）
                    logger.info(f"开始执行任务: {task_info.task_id}")

                    # 在事务中执行回测任务和状态更新
                    backtest_result_id = await self._execute_backtest_task_with_transaction(task_info)

                    logger.info(f"任务执行完成: {task_info.task_id}, 回测结果ID: {backtest_result_id}")

                except Exception as task_error:
                    logger.error(f"处理任务失败: {task_info.task_id if 'task_info' in locals() else 'unknown'}, 错误: {str(task_error)}")

                    # 更新任务状态为失败
                    if 'task_info' in locals():
                        try:
                            await task_dao.update_task_status(task_info.task_id, TaskStatus.FAILED)
                        except Exception:
                            logger.error(f"更新任务失败状态时出错: {task_info.task_id}")

        except Exception as e:
            logger.error(f"处理pending任务失败: {str(e)}")

    async def _execute_backtest_task_with_transaction(self, task_info: 'TaskInfo') -> str:
        """在事务中执行回测任务

        确保任务状态更新与回测结果保存的事务一致性

        Args:
            task_info: 任务信息

        Returns:
            回测结果ID

        Raises:
            Exception: 回测执行失败时抛出异常
        """
        from ...config.connection_pool import get_db_session

        async with get_db_session() as session:
            try:
                # 在事务中执行回测任务
                backtest_result_id = await self._execute_backtest_task(task_info)

                # 在同一事务中更新任务状态为已完成
                task_dao = await self._get_task_dao()
                await task_dao.update_task_status(
                    task_info.task_id,
                    TaskStatus.COMPLETED,
                    result_id=backtest_result_id
                )

                # 提交事务
                await session.commit()
                logger.info(f"事务提交成功: 任务 {task_info.task_id} 状态已更新")

                return backtest_result_id

            except Exception as e:
                # 回滚事务
                await session.rollback()
                logger.error(f"事务回滚: 任务 {task_info.task_id} 执行失败, 错误: {str(e)}")

                # 更新任务状态为失败（在新的事务中）
                try:
                    task_dao = await self._get_task_dao()
                    await task_dao.update_task_status(
                        task_info.task_id,
                        TaskStatus.FAILED,
                        error_message=str(e)
                    )
                except Exception as update_error:
                    logger.error(f"更新任务失败状态时出错: {task_info.task_id}, 错误: {str(update_error)}")

                raise

    async def _execute_backtest_task(self, task_info: 'TaskInfo') -> str:
        """执行回测任务

        Args:
            task_info: 任务信息

        Returns:
            回测结果ID

        Raises:
            Exception: 回测执行失败时抛出异常
        """
        try:
            # 获取服务实例
            backtest_engine = await self._get_backtest_engine()
            factor_manager = await self._get_factor_combination_manager()
            task_dao = await self._get_task_dao()

            # 获取因子组合配置
            factor_combination = None
            if task_info.factor_combination_id:
                factor_combination = await factor_manager.get_combination(
                    task_info.factor_combination_id
                )
                logger.info(f"获取因子组合配置: {task_info.factor_combination_id}")

            # 构建回测配置
            from decimal import Decimal

            from ..models.backtest_models import (
                BacktestConfig,
                BacktestFactorConfig,
                FactorItem,
            )

            # 构建BacktestFactorConfig
            if factor_combination and hasattr(factor_combination, 'factors'):
                factor_items = [
                    FactorItem(
                        factor_name=getattr(factor, 'name', 'MA'),
                        factor_type=getattr(factor, 'type', 'technical'),
                        weight=getattr(factor, 'weight', 1.0)
                    )
                    for factor in factor_combination.factors
                ]
                backtest_factor_config = BacktestFactorConfig(
                    combination_id=getattr(factor_combination, 'id', 'default'),
                    factors=factor_items,
                    description="Auto-generated from task"
                )
            else:
                # 默认因子配置
                backtest_factor_config = BacktestFactorConfig(
                    combination_id='default',
                    factors=[FactorItem(factor_name='MA', factor_type='technical', weight=1.0)],
                    description="Default factor configuration"
                )

            backtest_config = BacktestConfig(
                name=f"Task_{task_info.task_id}",
                stock_code=task_info.stock_code,
                start_date=task_info.start_date,
                end_date=task_info.end_date,
                initial_capital=Decimal(str(task_info.initial_capital)),
                factor_combination=backtest_factor_config,
                optimization_result_id=None
            )

            logger.info(f"开始执行回测: {task_info.task_id}")

            # 执行回测
            backtest_result = await backtest_engine.run_backtest(backtest_config)

            # 保存回测结果并获取结果ID
            result_id = getattr(backtest_result, 'result_id', None)
            if not result_id:
                raise ValueError("回测引擎未返回有效的结果ID")

            logger.info(f"回测任务执行成功: {task_info.task_id}, 结果ID: {result_id}")
            return str(result_id)

        except Exception as e:
            logger.error(f"回测任务执行失败: {task_info.task_id}, 错误: {str(e)}")
            # 更新任务错误信息
            await task_dao.update_task_error(task_info.task_id, str(e))
            raise

    async def get_scheduler_status(self) -> dict[str, Any]:
        """获取调度器状态信息

        Returns:
            调度器状态字典
        """
        return {
            'is_running': self._is_running,
            'retry_max_attempts': self.retry_max_attempts
        }
