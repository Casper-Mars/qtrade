"""情绪因子数据访问层"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from ..factor_engine.models.database import SentimentFactor
from ..factor_engine.models.schemas import (
    SentimentFactorResponse,
)
from .connection_pool import get_db_session


class SentimentFactorDAO:
    """情绪因子数据访问对象"""

    @staticmethod
    async def save_sentiment_factor(
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
                # 检查是否已存在相同记录
                existing = await session.execute(
                    select(SentimentFactor).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date == calculation_date,
                            SentimentFactor.start_date == start_date,
                            SentimentFactor.end_date == end_date,
                        )
                    )
                )
                existing_record = existing.scalar_one_or_none()

                if existing_record:
                    # 更新现有记录
                    existing_record.sentiment_factor = sentiment_factor
                    existing_record.positive_score = positive_score
                    existing_record.negative_score = negative_score
                    existing_record.neutral_score = neutral_score
                    existing_record.confidence = confidence
                    existing_record.news_count = news_count
                    existing_record.volume_adjustment = volume_adjustment
                    existing_record.updated_at = datetime.now()

                    await session.commit()
                    logger.info(f"更新情绪因子数据: {stock_code} - {calculation_date}")
                    return int(existing_record.id)
                else:
                    # 创建新记录
                    sentiment_factor_record = SentimentFactor(
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

    @staticmethod
    async def get_sentiment_factor(
        stock_code: str, calculation_date: str
    ) -> SentimentFactorResponse | None:
        """获取指定股票和日期的情绪因子

        Args:
            stock_code: 股票代码
            calculation_date: 计算日期

        Returns:
            SentimentFactorResponse | None: 情绪因子响应对象或None
        """
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
                record = result.scalar_one_or_none()

                if record:
                    return SentimentFactorResponse(
                        stock_code=record.stock_code,
                        date=record.calculation_date,
                        sentiment_factors={
                            "sentiment_factor": record.sentiment_factor,
                            "positive_score": record.positive_score,
                            "negative_score": record.negative_score,
                            "neutral_score": record.neutral_score,
                            "confidence": record.confidence,
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

    @staticmethod
    async def get_sentiment_factors_by_date(
        calculation_date: str, limit: int = 100
    ) -> list[SentimentFactorResponse]:
        """获取指定日期的所有情绪因子

        Args:
            calculation_date: 计算日期
            limit: 返回记录数限制

        Returns:
            list[SentimentFactorResponse]: 情绪因子响应对象列表
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(SentimentFactor)
                    .where(SentimentFactor.calculation_date == calculation_date)
                    .order_by(desc(SentimentFactor.sentiment_factor))
                    .limit(limit)
                )
                records = result.scalars().all()

                return [
                    SentimentFactorResponse(
                        stock_code=record.stock_code,
                        date=record.calculation_date,
                        sentiment_factors={
                            "sentiment_factor": record.sentiment_factor,
                            "positive_score": record.positive_score,
                            "negative_score": record.negative_score,
                            "neutral_score": record.neutral_score,
                            "confidence": record.confidence,
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

    @staticmethod
    async def get_sentiment_trend(
        stock_code: str, days: int = 30
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
                        "date": record.calculation_date,
                        "sentiment_factor": record.sentiment_factor,
                        "positive_score": record.positive_score,
                        "negative_score": record.negative_score,
                        "neutral_score": record.neutral_score,
                        "confidence": record.confidence,
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

    @staticmethod
    async def get_sentiment_statistics(
        stock_code: str, days: int = 30
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
                        func.avg(SentimentFactor.sentiment_factor).label("avg_sentiment"),
                        func.max(SentimentFactor.sentiment_factor).label("max_sentiment"),
                        func.min(SentimentFactor.sentiment_factor).label("min_sentiment"),
                        func.stddev(SentimentFactor.sentiment_factor).label("std_sentiment"),
                        func.sum(SentimentFactor.news_count).label("total_news"),
                        func.count(SentimentFactor.id).label("total_days"),
                    ).where(
                        and_(
                            SentimentFactor.stock_code == stock_code,
                            SentimentFactor.calculation_date >= func.date_sub(
                                func.curdate(), func.interval(days, "DAY")
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

    @staticmethod
    async def delete_old_sentiment_factors(days_to_keep: int = 90) -> int:
        """删除过期的情绪因子数据

        Args:
            days_to_keep: 保留天数

        Returns:
            int: 删除的记录数
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(func.count(SentimentFactor.id)).where(
                        SentimentFactor.calculation_date < func.date_sub(
                            func.curdate(), func.interval(days_to_keep, "DAY")
                        )
                    )
                )
                count_to_delete = result.scalar() or 0

                if count_to_delete > 0:
                    await session.execute(
                        SentimentFactor.__table__.delete().where(
                            SentimentFactor.calculation_date < func.date_sub(
                                func.curdate(), func.interval(days_to_keep, "DAY")
                            )
                        )
                    )
                    await session.commit()
                    logger.info(f"删除了 {count_to_delete} 条过期情绪因子数据")

                return count_to_delete

        except SQLAlchemyError as e:
            logger.error(f"删除过期情绪因子数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"删除过期情绪因子数据时发生未知错误: {e}")
            raise
