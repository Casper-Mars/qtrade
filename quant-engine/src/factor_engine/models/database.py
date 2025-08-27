"""因子数据库模型定义

本模块定义了因子计算引擎的数据库模型，包括技术因子、基本面因子、市场因子和情绪因子的数据表结构。
"""

from typing import Any

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base: Any = declarative_base()


class TechnicalFactor(Base):
    """技术因子数据表

    存储基于股票行情数据计算的技术指标因子，如移动平均线、RSI、MACD等 。
    """

    __tablename__ = "technical_factors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    stock_code = Column(String(10), nullable=False, comment="股票代码")
    factor_name = Column(String(50), nullable=False, comment="因子名称")
    factor_value: Any = Column(DECIMAL(20, 6), nullable=False, comment="因子值")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="更新时间",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_stock_factor_date", "stock_code", "factor_name", "trade_date"),
        Index("idx_trade_date", "trade_date"),
        UniqueConstraint(
            "stock_code", "factor_name", "trade_date", name="uk_stock_factor_date"
        ),
        {"comment": "技术因子表"},
    )


class FundamentalFactor(Base):
    """基本面因子数据表

    存储基于财务报表数据计算的基本面指标因子，如ROE、ROA、毛利率等。
    """

    __tablename__ = "fundamental_factors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    stock_code = Column(String(10), nullable=False, comment="股票代码")
    factor_name = Column(String(50), nullable=False, comment="因子名称")
    factor_value: Any = Column(DECIMAL(20, 6), nullable=False, comment="因子值")
    report_period = Column(String(10), nullable=False, comment="报告期")
    ann_date = Column(Date, nullable=False, comment="公告日期")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="更新时间",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_stock_factor_period", "stock_code", "factor_name", "report_period"),
        Index("idx_ann_date", "ann_date"),
        UniqueConstraint(
            "stock_code", "factor_name", "report_period", name="uk_stock_factor_period"
        ),
        {"comment": "基本面因子表"},
    )


class MarketFactor(Base):
    """市场因子数据表

    存储基于市场数据计算的市场特征因子，如市值、换手率、成交量等。
    """

    __tablename__ = "market_factors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    stock_code = Column(String(10), nullable=False, comment="股票代码")
    factor_name = Column(String(50), nullable=False, comment="因子名称")
    factor_value: Any = Column(DECIMAL(20, 6), nullable=False, comment="因子值")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="更新时间",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_stock_factor_date", "stock_code", "factor_name", "trade_date"),
        Index("idx_trade_date", "trade_date"),
        UniqueConstraint(
            "stock_code", "factor_name", "trade_date", name="uk_stock_factor_date"
        ),
        {"comment": "市场因子表"},
    )


class NewsSentimentFactor(Base):
    """新闻情绪因子数据表

    存储基于新闻文本情绪分析计算的情绪因子。
    """

    __tablename__ = "news_sentiment_factors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    stock_code = Column(String(10), nullable=False, comment="股票代码")
    factor_value: Any = Column(DECIMAL(10, 6), nullable=False, comment="情绪因子值")
    calculation_date = Column(Date, nullable=False, comment="计算日期")
    news_count = Column(
        Integer, nullable=False, default=0, comment="参与计算的新闻数量"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment="更新时间",
    )

    # 索引定义
    __table_args__ = (
        Index("idx_stock_date", "stock_code", "calculation_date"),
        Index("idx_calculation_date", "calculation_date"),
        UniqueConstraint("stock_code", "calculation_date", name="uk_stock_date"),
        {"comment": "新闻情绪因子表"},
    )
