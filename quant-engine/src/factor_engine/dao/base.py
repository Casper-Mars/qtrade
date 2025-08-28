"""因子数据访问层基础类

本模块定义了因子数据访问的基础类和接口，提供统一的数据访问模式。
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.database import (
    FundamentalFactor,
    MarketFactor,
    SentimentFactor,
    TechnicalFactor,
)


class BaseFactorDAO(ABC):
    """因子数据访问基础类"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    @abstractmethod
    def create(self, *args: Any, **kwargs: Any) -> Any:
        """创建因子数据"""
        pass

    @abstractmethod
    def get_by_id(self, factor_id: int) -> Any | None:
        """根据ID获取因子数据"""
        pass

    @abstractmethod
    def get_by_stock_and_date(self, stock_code: str, trade_date: date) -> list[Any]:
        """根据股票代码和日期获取因子数据"""
        pass

    @abstractmethod
    def update(self, factor_id: int, **kwargs: Any) -> bool:
        """更新因子数据"""
        pass

    @abstractmethod
    def delete(self, factor_id: int) -> bool:
        """删除因子数据"""
        pass

    def batch_create(self, factors_data: list[dict]) -> list[Any]:
        """批量创建因子数据"""
        try:
            created_factors = []
            for factor_data in factors_data:
                factor = self.create(**factor_data)
                created_factors.append(factor)

            self.db_session.commit()
            return created_factors
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    @abstractmethod
    def get_latest_by_stock(self, stock_code: str, limit: int = 10) -> list[Any]:
        """获取股票最新的因子数据"""
        pass


class TechnicalFactorDAO(BaseFactorDAO):
    """技术因子数据访问类"""

    def create(
        self,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        trade_date: date,
        **kwargs: Any,
    ) -> TechnicalFactor:
        """创建技术因子数据"""
        try:
            factor = TechnicalFactor(
                stock_code=stock_code,
                factor_name=factor_name,
                factor_value=factor_value,
                trade_date=trade_date,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db_session.add(factor)
            self.db_session.flush()  # 获取ID但不提交事务
            return factor
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_by_id(self, factor_id: int) -> TechnicalFactor | None:
        """根据ID获取技术因子数据"""
        return (
            self.db_session.query(TechnicalFactor)
            .filter(TechnicalFactor.id == factor_id)
            .first()
        )

    def get_by_stock_and_date(
        self, stock_code: str, trade_date: date
    ) -> list[TechnicalFactor]:
        """根据股票代码和日期获取技术因子数据"""
        return (
            self.db_session.query(TechnicalFactor)
            .filter(
                and_(
                    TechnicalFactor.stock_code == stock_code,
                    TechnicalFactor.trade_date == trade_date,
                )
            )
            .all()
        )

    def get_by_stock_and_factor(
        self,
        stock_code: str,
        factor_name: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TechnicalFactor]:
        """根据股票代码和因子名称获取数据"""
        query = self.db_session.query(TechnicalFactor).filter(
            and_(
                TechnicalFactor.stock_code == stock_code,
                TechnicalFactor.factor_name == factor_name,
            )
        )

        if start_date:
            query = query.filter(TechnicalFactor.trade_date >= start_date)
        if end_date:
            query = query.filter(TechnicalFactor.trade_date <= end_date)

        return query.order_by(desc(TechnicalFactor.trade_date)).all()

    def update(self, factor_id: int, **kwargs: Any) -> bool:
        """更新技术因子数据"""
        try:
            kwargs["updated_at"] = datetime.now()
            update_data = {
                getattr(TechnicalFactor, k): v
                for k, v in kwargs.items()
                if hasattr(TechnicalFactor, k)
            }
            result = (
                self.db_session.query(TechnicalFactor)
                .filter(TechnicalFactor.id == factor_id)
                .update(update_data)
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def delete(self, factor_id: int) -> bool:
        """删除技术因子数据"""
        try:
            result = (
                self.db_session.query(TechnicalFactor)
                .filter(TechnicalFactor.id == factor_id)
                .delete()
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_latest_by_stock(
        self, stock_code: str, limit: int = 10
    ) -> list[TechnicalFactor]:
        """获取股票最新的技术因子数据"""
        return (
            self.db_session.query(TechnicalFactor)
            .filter(TechnicalFactor.stock_code == stock_code)
            .order_by(desc(TechnicalFactor.trade_date))
            .limit(limit)
            .all()
        )


class FundamentalFactorDAO(BaseFactorDAO):
    """基本面因子数据访问类"""

    def create(
        self,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        report_period: str,
        ann_date: date,
        **kwargs: Any,
    ) -> FundamentalFactor:
        """创建基本面因子数据"""
        try:
            factor = FundamentalFactor(
                stock_code=stock_code,
                factor_name=factor_name,
                factor_value=factor_value,
                report_period=report_period,
                ann_date=ann_date,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db_session.add(factor)
            self.db_session.flush()
            return factor
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_by_id(self, factor_id: int) -> FundamentalFactor | None:
        """根据ID获取基本面因子数据"""
        return (
            self.db_session.query(FundamentalFactor)
            .filter(FundamentalFactor.id == factor_id)
            .first()
        )

    def get_by_stock_and_date(
        self, stock_code: str, ann_date: date
    ) -> list[FundamentalFactor]:
        """根据股票代码和公告日期获取基本面因子数据"""
        return (
            self.db_session.query(FundamentalFactor)
            .filter(
                and_(
                    FundamentalFactor.stock_code == stock_code,
                    FundamentalFactor.ann_date == ann_date,
                )
            )
            .all()
        )

    def get_by_stock_and_period(
        self, stock_code: str, report_period: str
    ) -> list[FundamentalFactor]:
        """根据股票代码和报告期获取基本面因子数据"""
        return (
            self.db_session.query(FundamentalFactor)
            .filter(
                and_(
                    FundamentalFactor.stock_code == stock_code,
                    FundamentalFactor.report_period == report_period,
                )
            )
            .all()
        )

    def get_by_stock_and_factor(
        self,
        stock_code: str,
        factor_name: str,
        start_period: str | None = None,
        end_period: str | None = None,
    ) -> list[FundamentalFactor]:
        """根据股票代码和因子名称获取数据"""
        query = self.db_session.query(FundamentalFactor).filter(
            and_(
                FundamentalFactor.stock_code == stock_code,
                FundamentalFactor.factor_name == factor_name,
            )
        )

        if start_period:
            query = query.filter(FundamentalFactor.report_period >= start_period)
        if end_period:
            query = query.filter(FundamentalFactor.report_period <= end_period)

        return query.order_by(desc(FundamentalFactor.report_period)).all()

    def update(self, factor_id: int, **kwargs: Any) -> bool:
        """更新基本面因子数据"""
        try:
            kwargs["updated_at"] = datetime.now()
            update_data = {
                getattr(FundamentalFactor, k): v
                for k, v in kwargs.items()
                if hasattr(FundamentalFactor, k)
            }
            result = (
                self.db_session.query(FundamentalFactor)
                .filter(FundamentalFactor.id == factor_id)
                .update(update_data)
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def delete(self, factor_id: int) -> bool:
        """删除基本面因子数据"""
        try:
            result = (
                self.db_session.query(FundamentalFactor)
                .filter(FundamentalFactor.id == factor_id)
                .delete()
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_latest_by_stock(
        self, stock_code: str, limit: int = 10
    ) -> list[FundamentalFactor]:
        """获取股票最新的基本面因子数据"""
        return (
            self.db_session.query(FundamentalFactor)
            .filter(FundamentalFactor.stock_code == stock_code)
            .order_by(desc(FundamentalFactor.ann_date))
            .limit(limit)
            .all()
        )


class MarketFactorDAO(BaseFactorDAO):
    """市场因子数据访问类"""

    def create(
        self,
        stock_code: str,
        factor_name: str,
        factor_value: float,
        trade_date: date,
        **kwargs: Any,
    ) -> MarketFactor:
        """创建市场因子数据"""
        try:
            factor = MarketFactor(
                stock_code=stock_code,
                factor_name=factor_name,
                factor_value=factor_value,
                trade_date=trade_date,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db_session.add(factor)
            self.db_session.flush()
            return factor
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_by_id(self, factor_id: int) -> MarketFactor | None:
        """根据ID获取市场因子数据"""
        return (
            self.db_session.query(MarketFactor)
            .filter(MarketFactor.id == factor_id)
            .first()
        )

    def get_by_stock_and_date(
        self, stock_code: str, trade_date: date
    ) -> list[MarketFactor]:
        """根据股票代码和日期获取市场因子数据"""
        return (
            self.db_session.query(MarketFactor)
            .filter(
                and_(
                    MarketFactor.stock_code == stock_code,
                    MarketFactor.trade_date == trade_date,
                )
            )
            .all()
        )

    def update(self, factor_id: int, **kwargs: Any) -> bool:
        """更新市场因子数据"""
        try:
            kwargs["updated_at"] = datetime.now()
            update_data = {
                getattr(MarketFactor, k): v
                for k, v in kwargs.items()
                if hasattr(MarketFactor, k)
            }
            result = (
                self.db_session.query(MarketFactor)
                .filter(MarketFactor.id == factor_id)
                .update(update_data)
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def delete(self, factor_id: int) -> bool:
        """删除市场因子数据"""
        try:
            result = (
                self.db_session.query(MarketFactor)
                .filter(MarketFactor.id == factor_id)
                .delete()
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_latest_by_stock(
        self, stock_code: str, limit: int = 10
    ) -> list[MarketFactor]:
        """获取股票最新的市场因子数据"""
        return (
            self.db_session.query(MarketFactor)
            .filter(MarketFactor.stock_code == stock_code)
            .order_by(desc(MarketFactor.trade_date))
            .limit(limit)
            .all()
        )


class NewsSentimentFactorDAO(BaseFactorDAO):
    """新闻情绪因子数据访问类"""

    def create(
        self,
        stock_code: str,
        factor_value: float,
        calculation_date: date,
        news_count: int,
        **kwargs: Any,
    ) -> SentimentFactor:
        """创建新闻情绪因子数据"""
        try:
            factor = SentimentFactor(
                stock_code=stock_code,
                factor_value=factor_value,
                calculation_date=calculation_date,
                news_count=news_count,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db_session.add(factor)
            self.db_session.flush()
            return factor
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_by_id(self, factor_id: int) -> SentimentFactor | None:
        """根据ID获取新闻情绪因子数据"""
        return (
            self.db_session.query(SentimentFactor)
            .filter(SentimentFactor.id == factor_id)
            .first()
        )

    def get_by_stock_and_date(
        self, stock_code: str, calculation_date: date
    ) -> list[SentimentFactor]:
        """根据股票代码和计算日期获取新闻情绪因子数据"""
        return (
            self.db_session.query(SentimentFactor)
            .filter(
                and_(
                    SentimentFactor.stock_code == stock_code,
                    SentimentFactor.calculation_date == calculation_date,
                )
            )
            .all()
        )

    def update(self, factor_id: int, **kwargs: Any) -> bool:
        """更新新闻情绪因子数据"""
        try:
            kwargs["updated_at"] = datetime.now()
            update_data = {
                getattr(SentimentFactor, k): v
                for k, v in kwargs.items()
                if hasattr(SentimentFactor, k)
            }
            result = (
                self.db_session.query(SentimentFactor)
                .filter(SentimentFactor.id == factor_id)
                .update(update_data)
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def delete(self, factor_id: int) -> bool:
        """删除新闻情绪因子数据"""
        try:
            result = (
                self.db_session.query(SentimentFactor)
                .filter(SentimentFactor.id == factor_id)
                .delete()
            )

            self.db_session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_latest_by_stock(
        self, stock_code: str, limit: int = 10
    ) -> list[SentimentFactor]:
        """获取股票最新的新闻情绪因子数据"""
        return (
            self.db_session.query(SentimentFactor)
            .filter(SentimentFactor.stock_code == stock_code)
            .order_by(desc(SentimentFactor.calculation_date))
            .limit(limit)
            .all()
        )


class FactorDAOFactory:
    """因子DAO工厂类"""

    @staticmethod
    def create_dao(factor_type: str, db_session: Session) -> Any:
        """根据因子类型创建对应的DAO实例"""
        dao_mapping = {
            "technical": TechnicalFactorDAO,
            "fundamental": FundamentalFactorDAO,
            "market": MarketFactorDAO,
            "news_sentiment": NewsSentimentFactorDAO,
        }

        dao_class = dao_mapping.get(factor_type)
        if not dao_class:
            raise ValueError(f"不支持的因子类型: {factor_type}")

        return dao_class(db_session)  # type: ignore
