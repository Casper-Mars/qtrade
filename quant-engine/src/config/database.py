"""数据库基础配置模块"""

from collections.abc import AsyncGenerator, Generator

from loguru import logger
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .settings import settings

# SQLAlchemy基础配置
Base = declarative_base()
metadata = MetaData()

# 同步数据库引擎（用于初始化和迁移）
sync_engine = create_engine(
    settings.mysql_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
)

# 异步数据库引擎
async_mysql_url = settings.mysql_url.replace("mysql+pymysql://", "mysql+aiomysql://")
async_engine = create_async_engine(
    async_mysql_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
)

# 会话工厂
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

logger.info("数据库基础配置初始化完成")


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话的依赖注入函数"""
    async with AsyncSessionLocal() as session:
        yield session
