"""因子数据访问层基础类

本模块定义了因子数据访问的基础类和接口，提供统一的异步数据访问模式。
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, ClassVar

from loguru import logger
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    FundamentalFactor,
    MarketFactor,
    SentimentFactor,
    TechnicalFactor,
)
from ..models.schemas import SentimentFactorResponse
from ...config.connection_pool import get_db_session


class BaseFactorDAO(ABC):
    """因子数据访问基础类"""
    
    # 子类需要定义的模型类
    model_class: ClassVar[type] = None

    @classmethod
    @abstractmethod
    async def create(cls, **kwargs: Any) -> Any:
        """创建因子数据"""
        pass

    @classmethod
    @abstractmethod
    async def get_by_id(cls, factor_id: int) -> Any | None:
        """根据ID获取因子数据"""
        pass

    @classmethod
    @abstractmethod
    async def get_by_stock_and_date(cls, stock_code: str, trade_date: date) -> list[Any]:
        """根据股票代码和日期获取因子数据"""
        pass

    @classmethod
    @abstractmethod
    async def update(cls, factor_id: int, **kwargs: Any) -> bool:
        """更新因子数据"""
        pass

    @classmethod
    @abstractmethod
    async def delete(cls, factor_id: int) -> bool:
        """删除因子数据"""
        pass

    @classmethod
    async def batch_create(cls, factors_data: list[dict]) -> list[Any]:
        """批量创建因子数据"""
        try:
            async with get_db_session() as session:
                created_factors = []
                for factor_data in factors_data:
                    factor = await cls._create_instance(session, **factor_data)
                    created_factors.append(factor)
                
                await session.commit()
                return created_factors
        except SQLAlchemyError as e:
            logger.error(f"批量创建因子数据失败: {e}")
            raise e

    @classmethod
    @abstractmethod
    async def get_latest_by_stock(cls, stock_code: str, limit: int = 10) -> list[Any]:
        """获取股票最新的因子数据"""
        pass
        
    @classmethod
    async def _create_instance(cls, session: AsyncSession, **kwargs: Any) -> Any:
        """创建模型实例的内部方法"""
        if not cls.model_class:
            raise NotImplementedError("子类必须定义 model_class")
            
        kwargs.update({
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        })
        
        instance = cls.model_class(**kwargs)
        session.add(instance)
        await session.flush()
        return instance


class TechnicalFactorDAO(BaseFactorDAO):
    """技术因子数据访问类"""
    
    model_class: ClassVar[type] = TechnicalFactor

    @classmethod
    async def create(
        cls,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        trade_date: date,
        **kwargs: Any,
    ) -> TechnicalFactor:
        """创建技术因子数据"""
        try:
            async with get_db_session() as session:
                factor = await cls._create_instance(
                    session,
                    stock_code=stock_code,
                    factor_name=factor_name,
                    factor_value=factor_value,
                    trade_date=trade_date,
                    **kwargs
                )
                await session.commit()
                return factor
        except SQLAlchemyError as e:
            logger.error(f"创建技术因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_id(cls, factor_id: int) -> TechnicalFactor | None:
        """根据ID获取技术因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(TechnicalFactor).where(TechnicalFactor.id == factor_id)
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据ID获取技术因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_date(
        cls, stock_code: str, trade_date: date
    ) -> list[TechnicalFactor]:
        """根据股票代码和日期获取技术因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(TechnicalFactor).where(
                        and_(
                            TechnicalFactor.stock_code == stock_code,
                            TechnicalFactor.trade_date == trade_date,
                        )
                    )
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和日期获取技术因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_factor(
        cls,
        stock_code: str,
        factor_name: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TechnicalFactor]:
        """根据股票代码和因子名称获取数据"""
        try:
            async with get_db_session() as session:
                conditions = [
                    TechnicalFactor.stock_code == stock_code,
                    TechnicalFactor.factor_name == factor_name,
                ]
                
                if start_date:
                    conditions.append(TechnicalFactor.trade_date >= start_date)
                if end_date:
                    conditions.append(TechnicalFactor.trade_date <= end_date)
                
                result = await session.execute(
                    select(TechnicalFactor)
                    .where(and_(*conditions))
                    .order_by(desc(TechnicalFactor.trade_date))
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和因子名称获取技术因子数据失败: {e}")
            raise e

    @classmethod
    async def update(cls, factor_id: int, **kwargs: Any) -> bool:
        """更新技术因子数据"""
        try:
            async with get_db_session() as session:
                kwargs["updated_at"] = datetime.now()
                
                # 过滤有效字段
                update_data = {
                    k: v for k, v in kwargs.items()
                    if hasattr(TechnicalFactor, k)
                }
                
                result = await session.execute(
                    select(TechnicalFactor).where(TechnicalFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    for key, value in update_data.items():
                        setattr(factor, key, value)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"更新技术因子数据失败: {e}")
            raise e

    @classmethod
    async def delete(cls, factor_id: int) -> bool:
        """删除技术因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(TechnicalFactor).where(TechnicalFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    await session.delete(factor)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"删除技术因子数据失败: {e}")
            raise e

    @classmethod
    async def get_latest_by_stock(
        cls, stock_code: str, limit: int = 10
    ) -> list[TechnicalFactor]:
        """获取股票最新的技术因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(TechnicalFactor)
                    .where(TechnicalFactor.stock_code == stock_code)
                    .order_by(desc(TechnicalFactor.trade_date))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"获取股票最新技术因子数据失败: {e}")
            raise e


class FundamentalFactorDAO(BaseFactorDAO):
    """基本面因子数据访问类"""
    
    model_class: ClassVar[type] = FundamentalFactor

    @classmethod
    async def create(
        cls,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        report_period: str,
        ann_date: date,
        **kwargs: Any,
    ) -> FundamentalFactor:
        """创建基本面因子数据"""
        try:
            async with get_db_session() as session:
                factor = await cls._create_instance(
                    session,
                    stock_code=stock_code,
                    factor_name=factor_name,
                    factor_value=factor_value,
                    report_period=report_period,
                    ann_date=ann_date,
                    **kwargs
                )
                await session.commit()
                return factor
        except SQLAlchemyError as e:
            logger.error(f"创建基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_id(cls, factor_id: int) -> FundamentalFactor | None:
        """根据ID获取基本面因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(FundamentalFactor).where(FundamentalFactor.id == factor_id)
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据ID获取基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_date(
        cls, stock_code: str, ann_date: date
    ) -> list[FundamentalFactor]:
        """根据股票代码和公告日期获取基本面因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(FundamentalFactor).where(
                        and_(
                            FundamentalFactor.stock_code == stock_code,
                            FundamentalFactor.ann_date == ann_date,
                        )
                    )
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和公告日期获取基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_period(
        cls, stock_code: str, report_period: str
    ) -> list[FundamentalFactor]:
        """根据股票代码和报告期获取基本面因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(FundamentalFactor).where(
                        and_(
                            FundamentalFactor.stock_code == stock_code,
                            FundamentalFactor.report_period == report_period,
                        )
                    )
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和报告期获取基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_factor(
        cls,
        stock_code: str,
        factor_name: str,
        start_period: str | None = None,
        end_period: str | None = None,
    ) -> list[FundamentalFactor]:
        """根据股票代码和因子名称获取数据"""
        try:
            async with get_db_session() as session:
                conditions = [
                    FundamentalFactor.stock_code == stock_code,
                    FundamentalFactor.factor_name == factor_name,
                ]
                
                if start_period:
                    conditions.append(FundamentalFactor.report_period >= start_period)
                if end_period:
                    conditions.append(FundamentalFactor.report_period <= end_period)
                
                result = await session.execute(
                    select(FundamentalFactor)
                    .where(and_(*conditions))
                    .order_by(desc(FundamentalFactor.report_period))
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和因子名称获取基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def update(cls, factor_id: int, **kwargs: Any) -> bool:
        """更新基本面因子数据"""
        try:
            async with get_db_session() as session:
                kwargs["updated_at"] = datetime.now()
                
                # 过滤有效字段
                update_data = {
                    k: v for k, v in kwargs.items()
                    if hasattr(FundamentalFactor, k)
                }
                
                result = await session.execute(
                    select(FundamentalFactor).where(FundamentalFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    for key, value in update_data.items():
                        setattr(factor, key, value)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"更新基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def delete(cls, factor_id: int) -> bool:
        """删除基本面因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(FundamentalFactor).where(FundamentalFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    await session.delete(factor)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"删除基本面因子数据失败: {e}")
            raise e

    @classmethod
    async def get_latest_by_stock(
        cls, stock_code: str, limit: int = 10
    ) -> list[FundamentalFactor]:
        """获取股票最新的基本面因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(FundamentalFactor)
                    .where(FundamentalFactor.stock_code == stock_code)
                    .order_by(desc(FundamentalFactor.ann_date))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"获取股票最新基本面因子数据失败: {e}")
            raise e


class MarketFactorDAO(BaseFactorDAO):
    """市场因子数据访问类"""
    
    model_class: ClassVar[type] = MarketFactor

    @classmethod
    async def create(
        cls,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        trade_date: date,
        **kwargs: Any,
    ) -> MarketFactor:
        """创建市场因子数据"""
        try:
            async with get_db_session() as session:
                factor = await cls._create_instance(
                    session,
                    stock_code=stock_code,
                    factor_name=factor_name,
                    factor_value=factor_value,
                    trade_date=trade_date,
                    **kwargs
                )
                await session.commit()
                return factor
        except SQLAlchemyError as e:
            logger.error(f"创建市场因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_id(cls, factor_id: int) -> MarketFactor | None:
        """根据ID获取市场因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MarketFactor).where(MarketFactor.id == factor_id)
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据ID获取市场因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_date(
        cls, stock_code: str, trade_date: date
    ) -> list[MarketFactor]:
        """根据股票代码和日期获取市场因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MarketFactor).where(
                        and_(
                            MarketFactor.stock_code == stock_code,
                            MarketFactor.trade_date == trade_date,
                        )
                    )
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和日期获取市场因子数据失败: {e}")
            raise e

    @classmethod
    async def update(cls, factor_id: int, **kwargs: Any) -> bool:
        """更新市场因子数据"""
        try:
            async with get_db_session() as session:
                kwargs["updated_at"] = datetime.now()
                
                # 过滤有效字段
                update_data = {
                    k: v for k, v in kwargs.items()
                    if hasattr(MarketFactor, k)
                }
                
                result = await session.execute(
                    select(MarketFactor).where(MarketFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    for key, value in update_data.items():
                        setattr(factor, key, value)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"更新市场因子数据失败: {e}")
            raise e

    @classmethod
    async def delete(cls, factor_id: int) -> bool:
        """删除市场因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MarketFactor).where(MarketFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    await session.delete(factor)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"删除市场因子数据失败: {e}")
            raise e

    @classmethod
    async def get_latest_by_stock(
        cls, stock_code: str, limit: int = 10
    ) -> list[MarketFactor]:
        """获取股票最新的市场因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(MarketFactor)
                    .where(MarketFactor.stock_code == stock_code)
                    .order_by(desc(MarketFactor.trade_date))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"获取股票最新市场因子数据失败: {e}")
            raise e


class NewsSentimentFactorDAO(BaseFactorDAO):
    """新闻情绪因子数据访问类"""
    
    model_class: ClassVar[type] = SentimentFactor

    @classmethod
    async def create(
        cls,
        stock_code: str,
        factor_value: float,
        calculation_date: date,
        news_count: int,
        **kwargs: Any,
    ) -> SentimentFactor:
        """创建新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                factor = await cls._create_instance(
                    session,
                    stock_code=stock_code,
                    factor_value=factor_value,
                    calculation_date=calculation_date,
                    news_count=news_count,
                    **kwargs
                )
                await session.commit()
                return factor
        except SQLAlchemyError as e:
            logger.error(f"创建新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_id(cls, factor_id: int) -> SentimentFactor | None:
        """根据ID获取新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor).where(SentimentFactor.id == factor_id)
                )
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"根据ID获取新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def get_by_stock_and_date(
        cls, stock_code: str, calculation_date: date
    ) -> list[SentimentFactor]:
        """根据股票代码和计算日期获取新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date == calculation_date,
                        )
                    )
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"根据股票代码和计算日期获取新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def update(cls, factor_id: int, **kwargs: Any) -> bool:
        """更新新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                kwargs["updated_at"] = datetime.now()
                
                # 过滤有效字段
                update_data = {
                    k: v for k, v in kwargs.items()
                    if hasattr(SentimentFactor, k)
                }
                
                result = await session.execute(
                    select(SentimentFactor).where(SentimentFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    for key, value in update_data.items():
                        setattr(factor, key, value)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"更新新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def delete(cls, factor_id: int) -> bool:
        """删除新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor).where(SentimentFactor.id == factor_id)
                )
                factor = result.scalar_one_or_none()
                
                if factor:
                    await session.delete(factor)
                    await session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"删除新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def get_latest_by_stock(
        cls, stock_code: str, limit: int = 10
    ) -> list[SentimentFactor]:
        """获取股票最新的新闻情绪因子数据"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor)
                    .where(SentimentFactor.stock_code == stock_code)
                    .order_by(desc(SentimentFactor.calculation_date))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"获取股票最新新闻情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def get_sentiment_factors_by_date_str(
        cls, calculation_date: str, limit: int = 100
    ) -> list[SentimentFactor]:
        """获取指定日期的所有情绪因子
        
        Args:
            calculation_date: 计算日期 (YYYY-MM-DD)
            limit: 返回记录数限制
            
        Returns:
            list[SentimentFactor]: 情绪因子列表
        """
        try:
            # 将字符串日期转换为date对象
            date_obj = datetime.strptime(calculation_date, "%Y-%m-%d").date()
            
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor)
                    .where(SentimentFactor.calculation_date == date_obj)
                    .order_by(desc(SentimentFactor.factor_value))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"获取日期情绪因子数据失败: {e}")
            raise e

    @classmethod
    async def save_sentiment_factor_extended(
        cls,
        stock_code: str,
        sentiment_factor: float,
        positive_score: float,
        negative_score: float,
        neutral_score: float,
        confidence: float,
        news_count: int,
        calculation_date: str,
        start_date: str,
        end_date: str,
        volume_adjustment: float,
    ) -> int:
        """保存情绪因子数据

        Args:
            stock_code: 股票代码
            sentiment_factor: 情绪因子值
            positive_score: 积极情绪分数
            negative_score: 消极情绪分数
            neutral_score: 中性情绪分数
            confidence: 置信度
            news_count: 新闻数量
            calculation_date: 计算日期
            start_date: 数据开始日期
            end_date: 数据结束日期
            volume_adjustment: 成交量调整系数

        Returns:
            int: 保存的记录ID

        Raises:
            SQLAlchemyError: 数据库操作异常
        """

        try:
            async with get_db_session() as session:
                # 转换日期格式
                calc_date = datetime.strptime(calculation_date, "%Y-%m-%d").date()
                
                # 检查是否已存在相同记录
                existing = await session.execute(
                    select(SentimentFactor).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date == calc_date,
                        )
                    )
                )
                existing_record = existing.scalar_one_or_none()

                if existing_record:
                    # 更新现有记录
                    existing_record.factor_value = sentiment_factor
                    existing_record.news_count = news_count
                    existing_record.updated_at = datetime.now()

                    await session.commit()
                    logger.info(f"更新情绪因子数据: {stock_code} - {calculation_date}")
                    return int(existing_record.id)
                else:
                    # 创建新记录
                    sentiment_factor_record = SentimentFactor(
                        stock_code=stock_code,
                        factor_value=sentiment_factor,
                        calculation_date=calc_date,
                        news_count=news_count,
                    )

                    session.add(sentiment_factor_record)
                    await session.commit()
                    await session.refresh(sentiment_factor_record)

                    logger.info(f"保存情绪因子数据: {stock_code} - {calculation_date}")
                    return int(sentiment_factor_record.id)

        except SQLAlchemyError as e:
            logger.error(f"保存情绪因子数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"保存情绪因子数据时发生未知错误: {e}")
            raise

    @classmethod
    async def save_sentiment_factor(
        cls,
        stock_code: str,
        sentiment_factor: float,
        positive_score: float,
        negative_score: float,
        neutral_score: float,
        confidence: float,
        news_count: int,
        calculation_date: str,
        start_date: str,
        end_date: str,
        volume_adjustment: float,
    ) -> int:
        """保存情绪因子数据（简化版本）
        
        Args:
            stock_code: 股票代码
            sentiment_factor: 情绪因子值
            positive_score: 积极情绪分数
            negative_score: 消极情绪分数
            neutral_score: 中性情绪分数
            confidence: 置信度
            news_count: 新闻数量
            calculation_date: 计算日期
            start_date: 数据开始日期
            end_date: 数据结束日期
            volume_adjustment: 成交量调整系数
            
        Returns:
            int: 保存的记录ID
        """
        return await cls.save_sentiment_factor_extended(
            stock_code=stock_code,
            sentiment_factor=sentiment_factor,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            confidence=confidence,
            news_count=news_count,
            calculation_date=calculation_date,
            start_date=start_date,
            end_date=end_date,
            volume_adjustment=volume_adjustment,
        )

    @classmethod
    async def get_sentiment_factor_response(
        cls, stock_code: str, date: str
    ) -> Any:
        """获取指定股票和日期的情绪因子

        Args:
            stock_code: 股票代码
            date: 计算日期

        Returns:
            SentimentFactorResponse | None: 情绪因子响应对象或None
        """
        try:
            # 将字符串日期转换为date对象
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date == date_obj,
                        )
                    )
                )
                record = result.scalar_one_or_none()

                if record:
                    return SentimentFactorResponse(
                        stock_code=record.stock_code,
                        date=record.calculation_date.isoformat(),
                        sentiment_factors={
                            "sentiment_factor": record.factor_value,
                            "positive_score": 0.0,  # 默认值，因为SentimentFactor模型中没有这些字段
                            "negative_score": 0.0,
                            "neutral_score": 0.0,
                            "confidence": 0.0,
                        },
                        source_weights={"news": 1.0},
                        data_counts={"news_count": record.news_count},
                    )
                return None

        except SQLAlchemyError as e:
            logger.error(f"获取情绪因子数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取情绪因子数据时发生未知错误: {e}")
            raise

    @classmethod
    async def get_sentiment_factors_by_date_response(
        cls, calculation_date: str, limit: int = 100
    ) -> list[Any]:
        """获取指定日期的所有情绪因子

        Args:
            calculation_date: 计算日期
            limit: 返回记录数限制

        Returns:
            list[SentimentFactorResponse]: 情绪因子响应对象列表
        """
        try:
            async with get_db_session() as session:
                # 将字符串日期转换为date对象
                date_obj = datetime.strptime(calculation_date, "%Y-%m-%d").date()
                
                result = await session.execute(
                    select(SentimentFactor)
                    .where(SentimentFactor.calculation_date == date_obj)
                    .order_by(desc(SentimentFactor.factor_value))
                    .limit(limit)
                )
                records = result.scalars().all()

                return [
                    SentimentFactorResponse(
                        stock_code=record.stock_code,
                        date=record.calculation_date.isoformat(),
                        sentiment_factors={
                            "sentiment_factor": record.factor_value,
                        },
                        source_weights={"news": 1.0},
                        data_counts={"news_count": record.news_count},
                    )
                    for record in records
                ]

        except SQLAlchemyError as e:
            logger.error(f"获取日期情绪因子数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取日期情绪因子数据时发生未知错误: {e}")
            raise

    @classmethod
    async def get_sentiment_trend(
        cls, stock_code: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取股票情绪趋势数据

        Args:
            stock_code: 股票代码
            days: 查询天数

        Returns:
            list[dict[str, Any]]: 趋势数据列表
        """

        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor)
                    .where(SentimentFactor.stock_code == stock_code)
                    .order_by(desc(SentimentFactor.calculation_date))
                    .limit(days)
                )
                records = result.scalars().all()

                return [
                    {
                        "date": record.calculation_date.strftime("%Y-%m-%d"),
                        "sentiment_factor": float(record.factor_value),
                        "positive_score": 0.0,  # 暂时使用默认值
                        "negative_score": 0.0,  # 暂时使用默认值
                        "neutral_score": 1.0,   # 暂时使用默认值
                        "confidence": 0.5,      # 暂时使用默认值
                        "news_count": record.news_count,
                    }
                    for record in records
                ]

        except SQLAlchemyError as e:
            logger.error(f"获取情绪趋势数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取情绪趋势数据时发生未知错误: {e}")
            raise

    @classmethod
    async def get_sentiment_statistics(
        cls, stock_code: str, days: int = 30
    ) -> dict[str, Any]:
        """获取股票情绪统计数据

        Args:
            stock_code: 股票代码
            days: 统计天数

        Returns:
            dict[str, Any]: 统计数据
        """

        try:
            async with get_db_session() as session:
                # 获取统计数据
                result = await session.execute(
                    select(
                        func.avg(SentimentFactor.factor_value).label("avg_sentiment"),
                        func.max(SentimentFactor.factor_value).label("max_sentiment"),
                        func.min(SentimentFactor.factor_value).label("min_sentiment"),
                        func.stddev(SentimentFactor.factor_value).label("std_sentiment"),
                        func.sum(SentimentFactor.news_count).label("total_news"),
                        func.count(SentimentFactor.id).label("total_days"),
                    ).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date >= func.date_sub(
                                func.curdate(), text(f"INTERVAL {days} DAY")
                            ),
                        )
                    )
                )
                stats = result.first()

                if stats and stats.total_days > 0:
                    return {
                        "average_sentiment": float(stats.avg_sentiment or 0),
                        "max_sentiment": float(stats.max_sentiment or 0),
                        "min_sentiment": float(stats.min_sentiment or 0),
                        "std_sentiment": float(stats.std_sentiment or 0),
                        "total_news": int(stats.total_news or 0),
                        "total_days": int(stats.total_days or 0),
                        "avg_news_per_day": float((stats.total_news or 0) / stats.total_days),
                    }
                else:
                    return {
                        "average_sentiment": 0.0,
                        "max_sentiment": 0.0,
                        "min_sentiment": 0.0,
                        "std_sentiment": 0.0,
                        "total_news": 0,
                        "total_days": 0,
                        "avg_news_per_day": 0.0,
                    }

        except SQLAlchemyError as e:
            logger.error(f"获取情绪统计数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取情绪统计数据时发生未知错误: {e}")
            raise


class FactorDAOFactory:
    """因子DAO工厂类"""

    @staticmethod
    def create_dao(factor_type: str) -> type[BaseFactorDAO]:
        """根据因子类型创建对应的DAO类"""
        dao_mapping = {
            "technical": TechnicalFactorDAO,
            "fundamental": FundamentalFactorDAO,
            "market": MarketFactorDAO,
            "sentiment": NewsSentimentFactorDAO,
        }

        dao_class = dao_mapping.get(factor_type)
        if not dao_class:
            raise ValueError(f"不支持的因子类型: {factor_type}")

        return dao_class
