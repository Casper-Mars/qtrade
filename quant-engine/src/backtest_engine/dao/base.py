"""回测引擎基础DAO类

本模块定义了回测引擎数据访问层的基础类和通用方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)


class BaseDAO(ABC, Generic[T]):
    """基础DAO抽象类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def create(self, obj: T) -> T:
        """创建对象"""
        pass

    @abstractmethod
    async def get_by_id(self, obj_id: UUID | str) -> T | None:
        """根据ID获取对象"""
        pass

    @abstractmethod
    async def update(self, obj: T) -> T:
        """更新对象"""
        pass

    @abstractmethod
    async def delete(self, obj_id: UUID | str) -> bool:
        """删除对象"""
        pass

    @abstractmethod
    async def list_objects(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[T]:
        """列表查询"""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """计数查询"""
        pass


class CRUDMixin:
    """CRUD操作混入类"""
    session: AsyncSession

    async def create_obj(self, model_class: type[T], **kwargs: Any) -> T:
        """创建对象的通用方法"""
        obj = model_class(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_obj_by_id(self, model_class: type[T], obj_id: UUID) -> T | None:
        """根据ID获取对象的通用方法"""
        result = await self.session.get(model_class, obj_id)
        return result

    async def update_obj(self, obj: T, **kwargs: Any) -> T:
        """更新对象的通用方法"""
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_obj(self, obj: T) -> bool:
        """删除对象的通用方法"""
        try:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False
