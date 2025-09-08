"""回测引擎数据模型定义

本模块定义了回测引擎所需的所有数据模型，包括：
- 回测配置模型：BacktestConfig
- 因子配置模型：BacktestFactorConfig、FactorItem
- 回测结果模型：BacktestResult
- 交易信号模型：TradingSignal
- 回测模式枚举：BacktestMode
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator, validator


class BacktestMode(str, Enum):
    """回测模式枚举"""
    HISTORICAL_SIMULATION = "historical_simulation"  # 历史模拟模式
    MODEL_VALIDATION = "model_validation"  # 模型验证模式


class FactorItem(BaseModel):
    """单个因子配置"""
    factor_name: str = Field(..., description="因子名称，如 PE, ROE, MA, RSI")
    factor_type: str = Field(..., description="因子类型：technical, fundamental, market, sentiment")
    weight: float = Field(..., ge=0, le=1, description="因子权重，范围0-1")

    @validator('factor_type')
    def validate_factor_type(cls, v: str) -> str:
        """验证因子类型"""
        valid_types = {"technical", "fundamental", "market", "sentiment"}
        if v not in valid_types:
            raise ValueError(f'因子类型必须是以下之一：{valid_types}')
        return v

    @validator('factor_name')
    def validate_factor_name(cls, v: str) -> str:
        """验证因子名称"""
        if not v or not v.strip():
            raise ValueError('因子名称不能为空')
        return v.strip()

    class Config:
        """Pydantic配置"""
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class BacktestFactorConfig(BaseModel):
    """回测因子组合配置"""
    combination_id: str = Field(..., description="因子组合唯一标识")
    factors: list[FactorItem] = Field(..., description="因子列表", min_length=1)
    description: str | None = Field(None, max_length=500, description="配置描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @model_validator(mode='after')
    def validate_factor_config(self) -> 'BacktestFactorConfig':
        """验证因子组合配置"""
        if not self.factors:
            raise ValueError('因子组合至少需要包含一个因子')

        # 验证权重总和
        total_weight = sum(factor.weight for factor in self.factors)
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f'因子权重总和必须等于1.0，当前为{total_weight}')

        # 验证因子名称唯一性
        factor_names = [factor.factor_name for factor in self.factors]
        if len(factor_names) != len(set(factor_names)):
            raise ValueError('因子组合中不能包含重复的因子名称')

        return self

    def get_factors_by_type(self, factor_type: str) -> list[str]:
        """根据因子类型获取因子名称列表"""
        return [f.factor_name for f in self.factors if f.factor_type == factor_type]

    def get_technical_factors(self) -> list[str]:
        """获取技术因子列表"""
        return self.get_factors_by_type("technical")

    def get_fundamental_factors(self) -> list[str]:
        """获取基本面因子列表"""
        return self.get_factors_by_type("fundamental")

    def get_market_factors(self) -> list[str]:
        """获取市场因子列表"""
        return self.get_factors_by_type("market")

    def get_sentiment_factors(self) -> list[str]:
        """获取情绪因子列表"""
        return self.get_factors_by_type("sentiment")

    def get_factor_weight(self, factor_name: str) -> float:
        """获取指定因子的权重"""
        for factor in self.factors:
            if factor.factor_name == factor_name:
                return factor.weight
        return 0.0

    def get_factor_names(self) -> list[str]:
        """获取所有因子名称列表"""
        return [factor.factor_name for factor in self.factors]

    def validate_weights(self) -> bool:
        """验证权重总和是否为1"""
        total_weight = sum(f.weight for f in self.factors)
        return abs(total_weight - 1.0) < 1e-6

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class BacktestConfig(BaseModel):
    """回测配置模型"""
    id: UUID = Field(default_factory=uuid4, description="回测配置唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="回测配置名称")
    stock_code: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="回测开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="回测结束日期，格式：YYYY-MM-DD")
    factor_combination: BacktestFactorConfig = Field(..., description="因子组合配置")
    optimization_result_id: str | None = Field(None, description="优化引擎结果ID")
    rebalance_frequency: str = Field(default="daily", description="调仓频率")
    transaction_cost: float = Field(default=0.001, ge=0, le=0.1, description="交易成本")
    backtest_mode: BacktestMode = Field(default=BacktestMode.HISTORICAL_SIMULATION, description="回测模式")
    use_factor_cache: bool = Field(default=True, description="是否使用因子缓存")
    initial_capital: Decimal = Field(default=Decimal('100000'), gt=0, description="初始资金")
    max_position_size: Decimal = Field(default=Decimal('1.0'), gt=0, le=1, description="最大仓位比例")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @validator('stock_code')
    def validate_stock_code(cls, v: str) -> str:
        """验证股票代码格式"""
        if not v or not v.strip():
            raise ValueError('股票代码不能为空')

        # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
        v = v.strip().upper()
        if not (v.isdigit() or
                v.endswith(".SZ") or v.endswith(".SH") or
                v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v: str) -> str:
        """验证日期格式"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v

    @validator('end_date')
    def validate_date_range(cls, v: str, values: dict) -> str:
        """验证日期范围"""
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('结束日期必须大于开始日期')
        return v

    @validator('rebalance_frequency')
    def validate_rebalance_frequency(cls, v: str) -> str:
        """验证调仓频率"""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        if v not in valid_frequencies:
            raise ValueError(f'调仓频率必须是以下之一：{valid_frequencies}')
        return v

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """验证配置名称"""
        if not v or not v.strip():
            raise ValueError('配置名称不能为空')
        return v.strip()

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class TradingSignal(BaseModel):
    """交易信号模型"""
    signal_type: str = Field(..., description="信号类型：BUY, SELL, HOLD")
    strength: float = Field(..., ge=0, le=1, description="信号强度，范围0-1")
    position_size: float = Field(..., ge=0, le=1, description="建议仓位大小，范围0-1")
    confidence: float = Field(..., ge=0, le=1, description="信号置信度，范围0-1")
    timestamp: str = Field(..., description="信号生成时间")
    composite_score: float = Field(..., description="因子综合评分")
    stock_code: str = Field(..., description="股票代码")
    factor_scores: dict[str, float] = Field(default_factory=dict, description="各因子评分")

    @validator('signal_type')
    def validate_signal_type(cls, v: str) -> str:
        """验证信号类型"""
        valid_types = {'BUY', 'SELL', 'HOLD'}
        v = v.upper()
        if v not in valid_types:
            raise ValueError(f'信号类型必须是以下之一：{valid_types}')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v: str) -> str:
        """验证时间戳格式"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError("时间戳格式不正确") from e
        return v

    def is_buy_signal(self) -> bool:
        """判断是否为买入信号"""
        return self.signal_type == 'BUY'

    def is_sell_signal(self) -> bool:
        """判断是否为卖出信号"""
        return self.signal_type == 'SELL'

    def is_hold_signal(self) -> bool:
        """判断是否为持有信号"""
        return self.signal_type == 'HOLD'

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BacktestResult(BaseModel):
    """回测结果模型"""
    id: UUID = Field(default_factory=uuid4, description="回测结果唯一标识")
    config_id: UUID = Field(..., description="回测配置ID")

    # 回测配置信息
    factor_combination: BacktestFactorConfig = Field(..., description="使用的因子组合和权重")
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    stock_code: str = Field(..., description="股票代码")
    backtest_mode: BacktestMode = Field(..., description="回测模式")

    # 绩效指标
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float | None = Field(None, description="索提诺比率")
    win_rate: float = Field(..., ge=0, le=1, description="胜率")
    trade_count: int = Field(..., ge=0, description="交易次数")

    # 风险指标
    volatility: float = Field(..., ge=0, description="波动率")
    var_95: float | None = Field(None, description="95%置信度VaR")
    beta: float | None = Field(None, description="贝塔系数")

    # 交易统计
    avg_profit: float | None = Field(None, description="平均盈利")
    avg_loss: float | None = Field(None, description="平均亏损")
    profit_loss_ratio: float | None = Field(None, description="盈亏比")

    # 执行信息
    execution_time: float = Field(..., ge=0, description="执行时间（秒）")
    data_points: int = Field(..., ge=0, description="数据点数量")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: datetime | None = Field(None, description="完成时间")

    def get_performance_summary(self) -> dict[str, float]:
        """获取绩效摘要"""
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "volatility": self.volatility
        }

    def is_profitable(self) -> bool:
        """判断是否盈利"""
        return self.total_return > 0

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }



# API请求和响应模型

class BacktestRunRequest(BaseModel):
    """回测执行请求模型"""
    config: BacktestConfig = Field(..., description="回测配置")

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class BacktestRunResponse(BaseModel):
    """回测执行响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: BacktestResult | None = Field(None, description="回测结果")
    task_id: str | None = Field(None, description="异步任务ID")

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BacktestResultsRequest(BaseModel):
    """回测结果查询请求模型"""
    result_id: str | None = Field(None, description="结果ID")
    config_id: str | None = Field(None, description="配置ID")
    stock_code: str | None = Field(None, description="股票代码")
    start_date: str | None = Field(None, description="开始日期")
    end_date: str | None = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=10, ge=1, le=100, description="每页大小")

    @validator('start_date', 'end_date')
    def validate_date_format(cls, v: str | None) -> str | None:
        """验证日期格式"""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class BacktestResultsData(BaseModel):
    """回测结果列表数据模型"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    results: list[BacktestResult] = Field(default_factory=list, description="结果列表")


class BacktestResultsResponse(BaseModel):
    """回测结果查询响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: BacktestResultsData | None = Field(None, description="查询结果")

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
