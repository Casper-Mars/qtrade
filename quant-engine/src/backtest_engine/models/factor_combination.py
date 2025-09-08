"""因子组合管理模块的数据模型定义

本模块定义了因子组合管理所需的所有数据模型，包括：
- 因子配置模型：FactorConfig
- 因子类型枚举：FactorType
- 验证结果模型：ValidationResult
- 因子组合模型：FactorCombination
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator, validator


class FactorType(str, Enum):
    """因子类型枚举"""
    TECHNICAL = "technical"  # 技术因子
    FUNDAMENTAL = "fundamental"  # 基本面因子
    MARKET = "market"  # 市场因子
    SENTIMENT = "sentiment"  # 情绪因子
    MACRO = "macro"  # 宏观因子


class ValidationResult(BaseModel):
    """验证结果模型"""
    is_valid: bool = Field(..., description="验证是否通过")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")
    warnings: list[str] = Field(default_factory=list, description="警告信息列表")

    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """添加警告信息"""
        self.warnings.append(warning)


class FactorConfig(BaseModel):
    """因子配置模型"""
    id: UUID = Field(default_factory=uuid4, description="因子配置唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="因子名称")
    factor_type: FactorType = Field(..., description="因子类型")
    weight: Decimal = Field(..., ge=0, le=1, description="因子权重，范围0-1")
    parameters: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="因子计算参数"
    )
    is_active: bool = Field(default=True, description="是否启用")
    description: str | None = Field(None, max_length=500, description="因子描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @validator('weight')
    def validate_weight(cls, v: Decimal) -> Decimal:
        """验证权重值"""
        if v < 0 or v > 1:
            raise ValueError('权重必须在0-1之间')
        return v

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """验证因子名称"""
        if not v or not v.strip():
            raise ValueError('因子名称不能为空')
        return v.strip()

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


# API请求和响应模型

class FactorCombinationCreateRequest(BaseModel):
    """创建因子组合配置请求模型"""
    stock_code: str = Field(..., description="股票代码")
    description: str | None = Field(None, description="配置描述")
    technical_factors: list[str] = Field(default_factory=list, description="技术因子列表")
    fundamental_factors: list[str] = Field(default_factory=list, description="基本面因子列表")
    sentiment_factors: list[str] = Field(default_factory=list, description="情绪因子列表")
    factor_weights: dict[str, float] = Field(..., description="因子权重配置")


class FactorConfigGetRequest(BaseModel):
    """获取因子组合配置请求模型"""
    config_id: str = Field(..., description="配置ID")


class FactorCombinationUpdateRequest(BaseModel):
    """更新因子组合配置请求模型"""
    config_id: str = Field(..., description="配置ID")
    description: str | None = Field(None, description="配置描述")
    technical_factors: list[str] | None = Field(None, description="技术因子列表")
    fundamental_factors: list[str] | None = Field(None, description="基本面因子列表")
    sentiment_factors: list[str] | None = Field(None, description="情绪因子列表")
    factor_weights: dict[str, float] | None = Field(None, description="因子权重配置")


class FactorCombinationDeleteRequest(BaseModel):
    """删除因子组合配置请求模型"""
    config_id: str = Field(..., description="配置ID")


class FactorCombinationListRequest(BaseModel):
    """获取配置列表请求模型"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=10, ge=1, le=100, description="每页大小")


class FactorCombinationGetByStockRequest(BaseModel):
    """按股票代码查询配置请求模型"""
    stock_code: str = Field(..., description="股票代码")


class FactorCombinationData(BaseModel):
    """因子组合配置数据模型"""
    config_id: str = Field(..., description="配置ID")
    stock_code: str = Field(..., description="股票代码")
    description: str | None = Field(None, description="配置描述")
    technical_factors: list[str] = Field(default_factory=list, description="技术因子列表")
    fundamental_factors: list[str] = Field(default_factory=list, description="基本面因子列表")
    sentiment_factors: list[str] = Field(default_factory=list, description="情绪因子列表")
    factor_weights: dict[str, float] = Field(..., description="因子权重配置")
    factor_count: int = Field(..., description="因子总数")
    created_at: str | None = Field(None, description="创建时间")
    updated_at: str | None = Field(None, description="更新时间")


class FactorCombinationResponse(BaseModel):
    """因子组合配置响应模型"""
    code: int = Field(..., description="响应码")
    message: str = Field(..., description="响应消息")
    data: FactorCombinationData | None = Field(None, description="响应数据")


class FactorCombinationListData(BaseModel):
    """因子组合配置列表数据模型"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    configs: list[FactorCombinationData] = Field(default_factory=list, description="配置列表")


class FactorCombinationListResponse(BaseModel):
    """因子组合配置列表响应模型"""
    code: int = Field(..., description="响应码")
    message: str = Field(..., description="响应消息")
    data: FactorCombinationListData | None = Field(None, description="响应数据")


class FactorCombination(BaseModel):
    """因子组合模型"""
    id: UUID = Field(default_factory=uuid4, description="组合唯一标识")
    name: str = Field(min_length=1, max_length=100, description="组合名称")
    description: str | None = Field(default=None, max_length=1000, description="组合描述")
    factors: list[FactorConfig] = Field(default_factory=list, min_length=1, description="因子配置列表")
    total_weight: Decimal = Field(default=Decimal('0'), description="总权重")
    is_active: bool = Field(default=True, description="是否启用")
    created_by: str | None = Field(default=None, description="创建者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @root_validator(pre=True)
    def validate_combination(cls, values: dict) -> dict:
        """验证因子组合"""
        factors = values.get('factors', [])
        if not factors:
            raise ValueError('因子组合至少需要包含一个因子')

        # 计算总权重
        total_weight = sum(factor.weight for factor in factors)
        values['total_weight'] = total_weight

        # 验证权重总和
        if abs(total_weight - 1) > 0.001:  # 允许0.1%的误差
            raise ValueError(f'因子权重总和必须等于1.0，当前为{total_weight}')

        # 验证因子名称唯一性
        factor_names = [factor.name for factor in factors]
        if len(factor_names) != len(set(factor_names)):
            raise ValueError('因子组合中不能包含重复的因子名称')

        return values

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """验证组合名称"""
        if not v or not v.strip():
            raise ValueError('组合名称不能为空')
        return v.strip()

    def validate_combination_data(self) -> ValidationResult:
        """验证因子组合的有效性"""
        result = ValidationResult(is_valid=True)

        # 检查因子数量
        if not self.factors:
            result.add_error("因子组合至少需要包含一个因子")
            return result

        # 检查权重总和
        total_weight = sum(factor.weight for factor in self.factors)
        if abs(float(total_weight) - 1) > 0.001:
            result.add_error(f"因子权重总和必须等于1.0，当前为{total_weight}")

        # 检查因子名称唯一性
        factor_names = [factor.name for factor in self.factors]
        if len(factor_names) != len(set(factor_names)):
            result.add_error("因子组合中不能包含重复的因子名称")

        # 检查非活跃因子
        inactive_factors = [f.name for f in self.factors if not f.is_active]
        if inactive_factors:
            result.add_warning(f"包含非活跃因子：{', '.join(inactive_factors)}")

        # 检查权重分布
        max_weight = max(factor.weight for factor in self.factors)
        if max_weight > 0.8:
            result.add_warning(f"存在权重过高的因子（>{max_weight}），可能影响组合分散性")

        return result

    def get_active_factors(self) -> list[FactorConfig]:
        """获取活跃的因子配置"""
        return [factor for factor in self.factors if factor.is_active]

    def get_factors_by_type(self, factor_type: FactorType) -> list[FactorConfig]:
        """根据类型获取因子配置"""
        return [factor for factor in self.factors if factor.factor_type == factor_type]

    def update_factor_weight(self, factor_name: str, new_weight: Decimal) -> bool:
        """更新指定因子的权重"""
        for factor in self.factors:
            if factor.name == factor_name:
                factor.weight = new_weight
                factor.updated_at = datetime.now()
                self.updated_at = datetime.now()
                # 重新计算总权重
                self.total_weight = Decimal(str(sum(f.weight for f in self.factors)))
                return True
        return False

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class StockCode(BaseModel):
    """股票代码模型"""
    code: str = Field(..., description="股票代码")
    market: str = Field(..., description="市场标识，如SH、SZ")

    @validator('code')
    def validate_code(cls, v: str) -> str:
        """验证股票代码格式"""
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('股票代码必须是6位数字')
        return v

    @validator('market')
    def validate_market(cls, v: str) -> str:
        """验证市场标识"""
        if v.upper() not in ['SH', 'SZ', 'BJ']:
            raise ValueError('市场标识必须是SH、SZ或BJ')
        return v.upper()

    @property
    def full_code(self) -> str:
        """获取完整股票代码"""
        return f"{self.code}.{self.market}"

    def __str__(self) -> str:
        return self.full_code

    class Config:
        """Pydantic配置"""
        schema_extra = {
            "example": {
                "code": "000001",
                "market": "SZ"
            }
        }


class BacktestConfig(BaseModel):
    """回测配置模型"""
    id: UUID = Field(default_factory=uuid4, description="回测配置唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="回测配置名称")
    factor_combination: FactorCombination = Field(..., description="因子组合配置")
    stock_pool: list[StockCode] = Field(min_length=1, description="股票池")
    start_date: datetime = Field(..., description="回测开始日期")
    end_date: datetime = Field(..., description="回测结束日期")
    initial_capital: Decimal = Field(..., gt=0, description="初始资金")
    benchmark: str | None = Field(None, description="基准指数代码")
    rebalance_frequency: str = Field(default="monthly", description="调仓频率")
    transaction_cost: Decimal = Field(default=Decimal('0.001'), description="交易成本")
    max_position_size: Decimal = Field(default=Decimal('0.1'), description="单只股票最大仓位")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @validator('end_date')
    def validate_date_range(cls, v: date, values: dict) -> date:
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

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }
