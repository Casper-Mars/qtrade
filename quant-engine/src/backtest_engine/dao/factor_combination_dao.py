"""因子组合配置数据访问层

本模块提供因子组合配置的数据库操作功能。
"""

import json
import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ...config.connection_pool import get_db_session
from ..models.factor_combination import (
    FactorCombination,
    FactorConfig,
    FactorType,
)

logger = logging.getLogger(__name__)


class FactorCombinationDAO:
    """因子组合配置数据访问对象

    负责因子组合配置的数据库CRUD操作。
    """

    def __init__(self) -> None:
        """初始化因子组合配置DAO"""
        pass

    async def save_config(self, config: FactorCombination) -> str:
        """保存因子组合配置

        Args:
            config: 因子组合配置对象

        Returns:
            str: 配置ID

        Raises:
            ValueError: 当配置数据无效时
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                # 生成配置ID
                config_id = str(uuid4())

                # 准备因子配置数据
                factors_json = json.dumps([
                    {
                        "id": str(factor.id),
                        "name": factor.name,
                        "factor_type": factor.factor_type.value,
                        "weight": float(factor.weight),
                        "parameters": factor.parameters,
                        "is_active": factor.is_active,
                        "description": factor.description,
                        "created_at": factor.created_at.isoformat(),
                        "updated_at": factor.updated_at.isoformat()
                    }
                    for factor in config.factors
                ], ensure_ascii=False)

                # 插入数据库
                insert_sql = text("""
                    INSERT INTO factor_combinations (
                        combination_id, name, description, factors,
                        total_weight, is_active, created_by, created_at, updated_at
                    ) VALUES (
                        :combination_id, :name, :description, :factors,
                        :total_weight, :is_active, :created_by, :created_at, :updated_at
                    )
                """)

                current_time = datetime.now()
                await session.execute(insert_sql, {
                    "combination_id": config_id,
                    "name": config.name,
                    "description": config.description,
                    "factors": factors_json,
                    "total_weight": float(config.total_weight),
                    "is_active": 1,
                    "created_by": config.created_by,
                    "created_at": current_time,
                    "updated_at": current_time
                })

                await session.commit()
                logger.info(f"成功保存因子组合配置: {config_id}")
                return config_id

        except SQLAlchemyError as e:
            logger.error(f"保存配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"保存配置时发生未知错误: {e}")
            raise RuntimeError(f"保存配置失败: {e}") from e

    async def get_config(self, config_id: str) -> FactorCombination | None:
        """获取因子组合配置

        Args:
            config_id: 配置ID

        Returns:
            Optional[FactorCombination]: 因子组合配置对象，如果不存在则返回None

        Raises:
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                select_sql = text("""
                    SELECT combination_id, name, description, factors,
                           total_weight, is_active, created_by, created_at, updated_at
                    FROM factor_combinations
                    WHERE combination_id = :config_id
                """)

                result = await session.execute(select_sql, {"config_id": config_id})
                row = result.fetchone()

                if not row:
                    return None

                # 解析因子数据
                factors_data = json.loads(row.factors)

                # 构建FactorCombination对象
                factors = []
                for factor_data in factors_data:
                    factor = FactorConfig(
                        id=factor_data["id"],
                        name=factor_data["name"],
                        factor_type=FactorType(factor_data["factor_type"]),
                        weight=factor_data["weight"],
                        parameters=factor_data["parameters"],
                        is_active=factor_data["is_active"],
                        description=factor_data["description"],
                        created_at=datetime.fromisoformat(factor_data["created_at"]),
                        updated_at=datetime.fromisoformat(factor_data["updated_at"])
                    )
                    factors.append(factor)

                config = FactorCombination(
                    name=row.name,
                    description=row.description,
                    factors=factors,
                    created_by=row.created_by
                )

                return config

        except SQLAlchemyError as e:
            logger.error(f"获取配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"获取配置时发生未知错误: {e}")
            raise RuntimeError(f"获取配置失败: {e}") from e

    async def update_config(self, config_id: str, config: FactorCombination) -> bool:
        """更新因子组合配置

        Args:
            config_id: 配置ID
            config: 更新后的因子组合配置对象

        Returns:
            bool: 更新是否成功

        Raises:
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                # 准备因子配置数据
                factors_json = json.dumps([
                    {
                        "id": str(factor.id),
                        "name": factor.name,
                        "factor_type": factor.factor_type.value,
                        "weight": float(factor.weight),
                        "parameters": factor.parameters,
                        "is_active": factor.is_active,
                        "description": factor.description,
                        "created_at": factor.created_at.isoformat(),
                        "updated_at": factor.updated_at.isoformat()
                    }
                    for factor in config.factors
                ], ensure_ascii=False)

                # 更新数据库
                update_sql = text("""
                    UPDATE factor_combinations
                    SET name = :name,
                        description = :description,
                        factors = :factors,
                        total_weight = :total_weight,
                        updated_at = :updated_at
                    WHERE combination_id = :config_id
                """)

                result = await session.execute(update_sql, {
                    "config_id": config_id,
                    "name": config.name,
                    "description": config.description,
                    "factors": factors_json,
                    "total_weight": float(config.total_weight),
                    "updated_at": datetime.now()
                })

                await session.commit()

                # 检查是否有行被更新
                if result.rowcount > 0:
                    logger.info(f"成功更新因子组合配置: {config_id}")
                    return True
                else:
                    logger.warning(f"配置不存在，无法更新: {config_id}")
                    return False

        except SQLAlchemyError as e:
            logger.error(f"更新配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"更新配置时发生未知错误: {e}")
            raise RuntimeError(f"更新配置失败: {e}") from e

    async def delete_config(self, config_id: str) -> bool:
        """删除因子组合配置

        Args:
            config_id: 配置ID

        Returns:
            bool: 删除是否成功

        Raises:
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                delete_sql = text("""
                    DELETE FROM factor_combinations
                    WHERE combination_id = :config_id
                """)

                result = await session.execute(delete_sql, {"config_id": config_id})
                await session.commit()

                # 检查是否有行被删除
                if result.rowcount > 0:
                    logger.info(f"成功删除因子组合配置: {config_id}")
                    return True
                else:
                    logger.warning(f"配置不存在，无法删除: {config_id}")
                    return False

        except SQLAlchemyError as e:
            logger.error(f"删除配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"删除配置时发生未知错误: {e}")
            raise RuntimeError(f"删除配置失败: {e}") from e

    async def list_configs(self, created_by: str | None = None,
                          is_active: bool | None = None,
                          limit: int = 100,
                          offset: int = 0) -> list[FactorCombination]:
        """列出因子组合配置

        Args:
            created_by: 创建者筛选条件
            is_active: 是否激活筛选条件
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[FactorCombination]: 因子组合配置列表

        Raises:
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                # 构建查询条件
                where_conditions = []
                params: dict[str, str | int] = {"limit": limit, "offset": offset}

                if created_by is not None:
                    where_conditions.append("created_by = :created_by")
                    params["created_by"] = created_by

                if is_active is not None:
                     where_conditions.append("is_active = :is_active")
                     params["is_active"] = int(1 if is_active else 0)

                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)

                select_sql = text(f"""
                    SELECT combination_id, name, description, factors,
                           total_weight, is_active, created_by, created_at, updated_at
                    FROM factor_combinations
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)

                result = await session.execute(select_sql, params)
                rows = result.fetchall()

                configs = []
                for row in rows:
                    # 解析因子数据
                    factors_data = json.loads(row.factors)

                    # 构建FactorCombination对象
                    factors = []
                    for factor_data in factors_data:
                        factor = FactorConfig(
                            id=factor_data["id"],
                            name=factor_data["name"],
                            factor_type=FactorType(factor_data["factor_type"]),
                            weight=factor_data["weight"],
                            parameters=factor_data["parameters"],
                            is_active=factor_data["is_active"],
                            description=factor_data["description"],
                            created_at=datetime.fromisoformat(factor_data["created_at"]),
                            updated_at=datetime.fromisoformat(factor_data["updated_at"])
                        )
                        factors.append(factor)

                    config = FactorCombination(
                        name=row.name,
                        description=row.description,
                        factors=factors,
                        created_by=row.created_by
                    )
                    configs.append(config)

                return configs

        except SQLAlchemyError as e:
            logger.error(f"列出配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"列出配置时发生未知错误: {e}")
            raise RuntimeError(f"列出配置失败: {e}") from e

    async def get_config_by_name(self, name: str) -> FactorCombination | None:
        """根据名称获取因子组合配置

        Args:
            name: 配置名称

        Returns:
            Optional[FactorCombination]: 因子组合配置对象，如果不存在则返回None

        Raises:
            RuntimeError: 当数据库操作失败时
        """
        try:
            async with get_db_session() as session:
                select_sql = text("""
                    SELECT combination_id, name, description, factors,
                           total_weight, is_active, created_by, created_at, updated_at
                    FROM factor_combinations
                    WHERE name = :name
                """)

                result = await session.execute(select_sql, {"name": name})
                row = result.fetchone()

                if not row:
                    return None

                # 解析因子数据
                factors_data = json.loads(row.factors)

                # 构建FactorCombination对象
                factors = []
                for factor_data in factors_data:
                    factor = FactorConfig(
                        id=factor_data["id"],
                        name=factor_data["name"],
                        factor_type=FactorType(factor_data["factor_type"]),
                        weight=factor_data["weight"],
                        parameters=factor_data["parameters"],
                        is_active=factor_data["is_active"],
                        description=factor_data["description"],
                        created_at=datetime.fromisoformat(factor_data["created_at"]),
                        updated_at=datetime.fromisoformat(factor_data["updated_at"])
                    )
                    factors.append(factor)

                config = FactorCombination(
                    name=row.name,
                    description=row.description,
                    factors=factors,
                    created_by=row.created_by
                )

                return config

        except SQLAlchemyError as e:
            logger.error(f"根据名称获取配置时发生数据库错误: {e}")
            raise RuntimeError(f"数据库操作失败: {e}") from e
        except Exception as e:
            logger.error(f"根据名称获取配置时发生未知错误: {e}")
            raise RuntimeError(f"根据名称获取配置失败: {e}") from e
