"""任务管理数据模型

本模块定义了任务管理器所需的核心数据模型，包括：
- TaskStatus: 任务状态枚举
- TaskRequest: 任务创建请求模型
- TaskInfo: 任务信息模型
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """任务状态枚举

    定义任务的生命周期状态，包括状态转换规则和验证逻辑
    """
    PENDING = "pending"      # 排队中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 已失败
    CANCELLED = "cancelled"  # 已取消

    @classmethod
    def get_valid_transitions(cls) -> dict[str, list[str]]:
        """获取有效的状态转换规则

        Returns:
            状态转换映射表
        """
        return {
            cls.PENDING: [cls.RUNNING, cls.CANCELLED],
            cls.RUNNING: [cls.COMPLETED, cls.FAILED, cls.CANCELLED],
            cls.COMPLETED: [],  # 完成状态不能转换
            cls.FAILED: [cls.PENDING],  # 失败可以重新排队
            cls.CANCELLED: [cls.PENDING]  # 取消可以重新排队
        }

    def can_transition_to(self, target_status: 'TaskStatus') -> bool:
        """检查是否可以转换到目标状态

        Args:
            target_status: 目标状态

        Returns:
            是否可以转换
        """
        valid_transitions = self.get_valid_transitions()
        return target_status in valid_transitions.get(self, [])

    def get_description(self) -> str:
        """获取状态描述

        Returns:
            状态描述文本
        """
        descriptions = {
            self.PENDING: "任务已创建，等待执行",
            self.RUNNING: "任务正在执行中",
            self.COMPLETED: "任务执行完成",
            self.FAILED: "任务执行失败",
            self.CANCELLED: "任务已取消"
        }
        return descriptions.get(self, "未知状态")


class TaskRequest(BaseModel):
    """任务创建请求模型

    用于接收客户端的任务创建请求，包含任务配置和参数
    """
    task_name: str = Field(..., description="任务名称", min_length=1, max_length=200)
    stock_code: str = Field(..., description="股票代码", pattern=r'^\d{6}\.(SH|SZ)$')
    start_date: str = Field(..., description="回测开始日期", pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., description="回测结束日期", pattern=r'^\d{4}-\d{2}-\d{2}$')
    initial_capital: float = Field(default=1000000.0, description="初始资金", gt=0)
    factor_combination_id: str | None = Field(None, description="因子组合ID")
    config: dict[str, Any] = Field(default_factory=dict, description="任务配置参数")
    batch_id: str | None = Field(None, description="批次ID，用于分组查询")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: str, info: Any) -> str:
        """验证日期范围"""
        if info.data and 'start_date' in info.data:
            start_date = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(v, '%Y-%m-%d')
            if end_date <= start_date:
                raise ValueError('结束日期必须大于开始日期')
        return v

    @field_validator('config')
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        """验证配置参数"""
        # 基本配置验证
        if not isinstance(v, dict):
            raise ValueError('配置参数必须是字典类型')

        # 检查必要的配置项
        required_keys = ['backtest_mode']
        for key in required_keys:
            if key not in v:
                v[key] = 'historical_simulation'  # 设置默认值

        # 验证回测模式
        valid_modes = ['historical_simulation', 'model_validation']
        if v.get('backtest_mode') not in valid_modes:
            raise ValueError(f'回测模式必须是以下之一: {valid_modes}')

        return v

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典

        Returns:
            字典格式的任务请求数据
        """
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TaskRequest':
        """从字典反序列化

        Args:
            data: 字典数据

        Returns:
            TaskRequest实例
        """
        return cls(**data)


class TaskInfo(BaseModel):
    """任务信息模型

    存储任务的完整信息，包括状态、结果等
    """
    task_id: str = Field(..., description="任务唯一标识")
    batch_id: str | None = Field(None, description="批次ID，用于分组查询")
    task_name: str = Field(..., description="任务名称")
    stock_code: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    initial_capital: float = Field(..., description="初始资金")
    factor_combination_id: str | None = Field(None, description="因子组合ID")
    config: dict[str, Any] = Field(default_factory=dict, description="任务配置")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    error_message: str | None = Field(None, description="错误信息")
    backtest_result_id: str | None = Field(None, description="关联的回测结果ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="创建时间")
    started_at: datetime | None = Field(None, description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="更新时间")

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @classmethod
    def create_from_request(cls, request: TaskRequest, task_id: str | None = None,
                           batch_id: str | None = None) -> 'TaskInfo':
        """从TaskRequest创建TaskInfo

        Args:
            request: 任务请求
            task_id: 任务ID，如果不提供则自动生成
            batch_id: 批次ID，如果不提供则使用请求中的batch_id

        Returns:
            TaskInfo实例
        """
        if task_id is None:
            task_id = f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

        if batch_id is None:
            batch_id = request.batch_id or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return cls(
            task_id=task_id,
            batch_id=batch_id,
            task_name=request.task_name,
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            factor_combination_id=request.factor_combination_id,
            config=request.config,
            status=TaskStatus.PENDING,
            error_message=None,
            backtest_result_id=None,
            started_at=None,
            completed_at=None
        )

    def update_status(self, new_status: TaskStatus, error_message: str | None = None) -> bool:
        """更新任务状态

        Args:
            new_status: 新状态
            error_message: 错误信息（状态为FAILED时必须提供）

        Returns:
            是否更新成功
        """
        # 验证状态转换是否有效
        if not self.status.can_transition_to(new_status):
            return False

        # 更新状态
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(UTC)

        # 根据状态更新相关字段
        if new_status == TaskStatus.RUNNING and old_status == TaskStatus.PENDING:
            self.started_at = datetime.now(UTC)
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = datetime.now(UTC)

        # 设置错误信息
        if new_status == TaskStatus.FAILED:
            self.error_message = error_message or "任务执行失败"
        elif new_status == TaskStatus.COMPLETED:
            self.error_message = None  # 清除之前的错误信息

        return True

    def set_result(self, backtest_result_id: str) -> None:
        """设置回测结果ID

        Args:
            backtest_result_id: 回测结果ID
        """
        self.backtest_result_id = backtest_result_id
        self.updated_at = datetime.now(UTC)

    def get_duration(self) -> float | None:
        """获取任务执行时长（秒）

        Returns:
            执行时长，如果任务未开始或未完成则返回None
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_finished(self) -> bool:
        """检查任务是否已结束

        Returns:
            任务是否已结束（完成、失败或取消）
        """
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典

        Returns:
            字典格式的任务信息
        """
        data = self.dict()
        # 转换datetime为ISO格式字符串
        for key in ['created_at', 'started_at', 'completed_at', 'updated_at']:
            if data[key]:
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TaskInfo':
        """从字典反序列化

        Args:
            data: 字典数据

        Returns:
            TaskInfo实例
        """
        # 转换字符串为datetime
        for key in ['created_at', 'started_at', 'completed_at', 'updated_at']:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))

        return cls(**data)
