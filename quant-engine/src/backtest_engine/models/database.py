"""回测引擎数据库模型定义

本模块定义了回测引擎的SQLAlchemy数据库模型，包括回测批次、任务和结果的数据表结构。
"""

from typing import Any

from sqlalchemy import (
    CHAR,
    DECIMAL,
    JSON,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base: Any = declarative_base()


class BacktestBatchTable(Base):
    """回测批次表模型"""
    __tablename__ = "backtest_batches"

    id = Column(CHAR(36), primary_key=True, comment="批次ID")
    name = Column(String(255), nullable=False, comment="批次名称")
    description = Column(Text, comment="批次描述")
    status: Any = Column(
        Enum("pending", "running", "completed", "failed", "cancelled"),
        nullable=False,
        default="pending",
        comment="批次状态"
    )
    total_tasks: Any = Column(Integer(), nullable=False, default=0, comment="总任务数")
    completed_tasks: Any = Column(Integer(), nullable=False, default=0, comment="已完成任务数")
    failed_tasks: Any = Column(Integer(), nullable=False, default=0, comment="失败任务数")
    config: Any = Column(JSON, comment="批次配置信息")
    created_at = Column(
        DateTime,
        default=func.current_timestamp(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")

    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        {"comment": "回测批次表"}
    )


class BacktestTaskTable(Base):
    """回测任务表模型"""
    __tablename__ = "backtest_tasks"

    id = Column(CHAR(36), primary_key=True, comment="任务ID")
    batch_id = Column(
        CHAR(36),
        ForeignKey("backtest_batches.id", ondelete="CASCADE"),
        comment="所属批次ID"
    )
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    status: Any = Column(
        Enum("pending", "running", "completed", "failed", "cancelled"),
        nullable=False,
        default="pending",
        comment="任务状态"
    )
    config: Any = Column(JSON, nullable=False, comment="回测配置")
    result_id: Any = Column(CHAR(36), comment="关联的结果ID")
    error_message: Any = Column(Text, comment="错误信息")
    progress: Any = Column(DECIMAL(5, 2), default=0.00, comment="执行进度(0-100)")
    created_at = Column(
        DateTime,
        default=func.current_timestamp(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")

    __table_args__ = (
        Index("idx_batch_id", "batch_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        Index("idx_result_id", "result_id"),
        {"comment": "回测任务表"}
    )


class BacktestResultTable(Base):
    """回测结果表模型"""
    __tablename__ = "backtest_results"

    id = Column(CHAR(36), primary_key=True, comment="结果ID")
    task_id = Column(
        CHAR(36),
        ForeignKey("backtest_tasks.id", ondelete="CASCADE"),
        comment="关联的任务ID"
    )
    batch_id = Column(
        CHAR(36),
        ForeignKey("backtest_batches.id", ondelete="CASCADE"),
        comment="关联的批次ID"
    )
    stock_code: Any = Column(String(20), nullable=False, comment="股票代码")
    start_date: Any = Column(Date, nullable=False, comment="回测开始日期")
    end_date: Any = Column(Date, nullable=False, comment="回测结束日期")
    backtest_mode: Any = Column(
        Enum("historical_simulation", "model_validation"),
        nullable=False,
        default="historical_simulation",
        comment="回测模式"
    )

    # 基础配置信息
    transaction_cost: Any = Column(DECIMAL(8, 6), default=0.001, comment="交易成本")

    # 因子配置
    factor_config: Any = Column(JSON, nullable=False, comment="因子配置信息")

    # 绩效指标
    total_return: Any = Column(DECIMAL(10, 6), comment="总收益率")
    annual_return: Any = Column(DECIMAL(10, 6), comment="年化收益率")
    sharpe_ratio: Any = Column(DECIMAL(10, 6), comment="夏普比率")
    sortino_ratio: Any = Column(DECIMAL(10, 6), comment="索提诺比率")
    max_drawdown: Any = Column(DECIMAL(10, 6), comment="最大回撤")
    volatility: Any = Column(DECIMAL(10, 6), comment="波动率")

    # 交易统计
    total_trades: Any = Column(Integer(), default=0, comment="总交易次数")
    winning_trades: Any = Column(Integer(), default=0, comment="盈利交易次数")
    losing_trades: Any = Column(Integer(), default=0, comment="亏损交易次数")
    win_rate: Any = Column(DECIMAL(5, 4), comment="胜率")
    avg_win: Any = Column(DECIMAL(10, 6), comment="平均盈利")
    avg_loss: Any = Column(DECIMAL(10, 6), comment="平均亏损")
    profit_loss_ratio: Any = Column(DECIMAL(10, 6), comment="盈亏比")

    # 风险指标
    var_95: Any = Column(DECIMAL(10, 6), comment="95% VaR")
    var_99: Any = Column(DECIMAL(10, 6), comment="99% VaR")
    calmar_ratio: Any = Column(DECIMAL(10, 6), comment="Calmar比率")

    # 详细数据
    daily_returns: Any = Column(JSON, comment="每日收益率序列")
    equity_curve: Any = Column(JSON, comment="资金曲线数据")
    trade_history: Any = Column(JSON, comment="交易历史记录")
    position_history: Any = Column(JSON, comment="持仓历史记录")

    # 元数据
    execution_time: Any = Column(DECIMAL(10, 3), comment="执行时间(秒)")
    created_at = Column(
        DateTime,
        default=func.current_timestamp(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )

    __table_args__ = (
        Index("idx_task_id", "task_id"),
        Index("idx_batch_id", "batch_id"),
        Index("idx_stock_code", "stock_code"),
        Index("idx_date_range", "start_date", "end_date"),
        Index("idx_backtest_mode", "backtest_mode"),
        Index("idx_created_at", "created_at"),
        Index("idx_total_return", "total_return"),
        Index("idx_sharpe_ratio", "sharpe_ratio"),
        {"comment": "回测结果表"}
    )
