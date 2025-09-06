"""因子数据的Pydantic模型定义

本模块定义了因子计算引擎的API请求和响应模型，用于数据验证和序列化。
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class BaseFactorModel(BaseModel):
    """因子模型基类"""

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }


# ==================== 技术因子相关模型 ====================


class TechnicalFactorRequest(BaseFactorModel):
    """技术因子计算请求模型"""

    stock_code: str = Field(..., description="股票代码")
    factors: list[str] = Field(..., description="因子列表")
    end_date: str | None = Field(
        default=None, description="计算截止日期，格式：YYYY-MM-DD"
    )
    period: int | None = Field(default=20, description="计算周期")

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
        if not (v.isdigit() or 
                v.endswith(".SZ") or v.endswith(".SH") or 
                v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("end_date")
    def validate_end_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class TechnicalFactorResponse(BaseFactorModel):
    """技术因子计算响应模型"""

    stock_code: str
    calculation_date: str
    factors: dict[str, float | dict[str, float]]


class TechnicalFactorHistoryResponse(BaseFactorModel):
    """技术因子历史数据响应模型"""

    stock_code: str
    factor_name: str
    start_date: str
    end_date: str
    data: list[dict[str, str | float]]


class BatchTechnicalFactorRequest(BaseFactorModel):
    """批量技术因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    factors: list[str] = Field(..., description="因子列表")
    end_date: str | None = Field(
        default=None, description="计算截止日期，格式：YYYY-MM-DD"
    )

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
            if not (code.isdigit() or 
                    code.endswith(".SZ") or code.endswith(".SH") or 
                    code.startswith("SH") or code.startswith("SZ")):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("end_date")
    def validate_end_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class BatchTechnicalFactorResponse(BaseFactorModel):
    """批量技术因子计算响应模型"""

    calculation_date: str
    total_stocks: int
    successful_stocks: int
    failed_stocks: int
    results: dict[str, dict[str, float | dict[str, float]]]
    errors: dict[str, str] | None = None


class TechnicalFactor(BaseFactorModel):
    """技术因子数据模型"""

    id: int
    stock_code: str
    factor_name: str
    factor_value: float
    trade_date: date
    created_at: datetime
    updated_at: datetime


# ==================== 基本面因子相关模型 ====================


class FundamentalFactorRequest(BaseFactorModel):
    """基本面因子计算请求模型"""

    stock_code: str = Field(..., description="股票代码")
    factors: list[str] = Field(..., description="因子列表")
    period: str = Field(..., description="报告期，格式：2023Q4或2023")
    report_type: str = Field(
        default="quarterly", description="报告类型：quarterly或annual"
    )

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
        if not (v.isdigit() or 
                v.endswith(".SZ") or v.endswith(".SH") or 
                v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("period")
    def validate_period(cls, v: str) -> str:
        # 验证季度格式：2023Q1, 2023Q2, 2023Q3, 2023Q4
        # 或年度格式：2023
        if not (v.endswith(("Q1", "Q2", "Q3", "Q4")) or v.isdigit()):
            raise ValueError("报告期格式不正确，应为YYYYQX或YYYY")
        return v

    @validator("report_type")
    def validate_report_type(cls, v: str) -> str:
        if v not in ["quarterly", "annual"]:
            raise ValueError("报告类型必须是quarterly或annual")
        return v


class FundamentalFactorResponse(BaseFactorModel):
    """基本面因子计算响应模型"""

    stock_code: str
    period: str
    report_type: str
    factors: dict[str, float]
    growth_rates: dict[str, float] | None = None


class BatchFundamentalFactorRequest(BaseFactorModel):
    """批量基本面因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    factors: list[str] = Field(..., description="因子列表")
    period: str = Field(..., description="报告期，格式：2023Q4或2023")
    report_type: str = Field(
        default="quarterly", description="报告类型：quarterly或annual"
    )

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
            if not (code.isdigit() or 
                    code.endswith(".SZ") or code.endswith(".SH") or 
                    code.startswith("SH") or code.startswith("SZ")):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("period")
    def validate_period(cls, v: str) -> str:
        # 验证季度格式：2023Q1, 2023Q2, 2023Q3, 2023Q4
        # 或年度格式：2023
        if not (v.endswith(("Q1", "Q2", "Q3", "Q4")) or v.isdigit()):
            raise ValueError("报告期格式不正确，应为YYYYQX或YYYY")
        return v

    @validator("report_type")
    def validate_report_type(cls, v: str) -> str:
        if v not in ["quarterly", "annual"]:
            raise ValueError("报告类型必须是quarterly或annual")
        return v


class BatchFundamentalFactorResponse(BaseFactorModel):
    """批量基本面因子计算响应模型"""

    period: str
    report_type: str
    total_stocks: int
    successful_stocks: int
    failed_stocks: int
    results: dict[str, dict[str, float]]
    growth_rates: dict[str, dict[str, float]] | None = None
    errors: dict[str, str] | None = None


class FundamentalFactor(BaseFactorModel):
    """基本面因子数据模型"""

    id: int
    stock_code: str
    factor_name: str
    factor_value: float
    report_period: str
    ann_date: date
    created_at: datetime
    updated_at: datetime


# ==================== 市场因子相关模型 ====================


class MarketFactorRequest(BaseFactorModel):
    """市场因子计算请求模型"""

    stock_code: str = Field(..., description="股票代码")
    factors: list[str] = Field(..., description="因子列表")
    trade_date: str | None = Field(
        default=None, description="交易日期，格式：YYYY-MM-DD"
    )

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
        if not (v.isdigit() or 
                v.endswith(".SZ") or v.endswith(".SH") or 
                v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("trade_date")
    def validate_trade_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class MarketFactorResponse(BaseFactorModel):
    """市场因子计算响应模型"""

    stock_code: str
    trade_date: str
    factors: dict[str, float]


class MarketFactorHistoryResponse(BaseFactorModel):
    """市场因子历史数据响应模型"""

    stock_code: str
    factor_name: str
    start_date: str
    end_date: str
    data: list[dict[str, str | float]]


class BatchMarketFactorRequest(BaseFactorModel):
    """批量市场因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    factors: list[str] = Field(..., description="因子列表")
    trade_date: str | None = Field(
        default=None, description="交易日期，格式：YYYY-MM-DD"
    )

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            # 支持格式：000001.SZ, 600000.SH, SH600000, SZ000001, 000001, 600000
            if not (code.isdigit() or 
                    code.endswith(".SZ") or code.endswith(".SH") or 
                    code.startswith("SH") or code.startswith("SZ")):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("trade_date")
    def validate_trade_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class BatchMarketFactorResponse(BaseFactorModel):
    """批量市场因子计算响应模型"""

    trade_date: str
    total_stocks: int
    successful_stocks: int
    failed_stocks: int
    results: dict[str, dict[str, float]]
    errors: dict[str, str] | None = None


class MarketFactor(BaseFactorModel):
    """市场因子数据模型"""

    id: int
    stock_code: str
    factor_name: str
    factor_value: float
    trade_date: date
    created_at: datetime
    updated_at: datetime


# ==================== 新闻情绪因子相关模型 ====================


class SentimentFactorRequest(BaseFactorModel):
    """新闻情绪因子计算请求模型"""

    stock_code: str = Field(..., description="股票代码", min_length=6, max_length=10)
    date: str = Field(..., description="计算日期，格式：YYYY-MM-DD")
    sources: list[str] = Field(
        ["news", "announcements", "policies"], description="数据源列表"
    )
    time_window: int = Field(default=7, description="时间窗口（天）")

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        if not v.isdigit() and not (v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("date")
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class SentimentFactorResponse(BaseFactorModel):
    """新闻情绪因子计算响应模型"""

    stock_code: str
    date: str
    sentiment_factors: dict[str, float]
    source_weights: dict[str, float]
    data_counts: dict[str, int]


class NewsSentimentFactor(BaseFactorModel):
    """新闻情绪因子数据模型"""

    id: int
    stock_code: str
    factor_value: float
    calculation_date: date
    news_count: int
    created_at: datetime
    updated_at: datetime


# ==================== 批量操作相关模型 ====================


class BatchCalculateRequest(BaseFactorModel):
    """批量因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    factor_types: list[str] = Field(
        ["technical", "fundamental", "market", "news_sentiment"],
        description="因子类型列表",
    )
    calculation_date: str = Field(..., description="计算日期，格式：YYYY-MM-DD")

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            if not code.isdigit() and not (
                code.startswith("SH") or code.startswith("SZ")
            ):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("factor_types")
    def validate_factor_types(cls, v: list[str]) -> list[str]:
        valid_types = {"technical", "fundamental", "market", "news_sentiment"}
        for factor_type in v:
            if factor_type not in valid_types:
                raise ValueError(f"不支持的因子类型：{factor_type}")
        return v

    @validator("calculation_date")
    def validate_calculation_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class BatchCalculateResponse(BaseFactorModel):
    """批量因子计算响应模型"""

    task_id: str
    status: str
    total_stocks: int
    completed_stocks: int
    failed_stocks: int
    results: dict[str, dict[str, float]] | None = None


# ==================== 通用响应模型 ====================


class ApiResponse(BaseFactorModel):
    """API通用响应模型"""

    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict | list | str | int | float | None = Field(
        default=None, description="响应数据"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="响应时间戳"
    )


class ErrorResponse(BaseFactorModel):
    """错误响应模型"""

    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    detail: str | None = Field(default=None, description="错误详情")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="错误时间戳"
    )



    confidence: float
    news_count: int
    calculation_date: str
    start_date: str
    end_date: str
    volume_adjustment: float
    calculation_time: str


class BatchSentimentFactorRequest(BaseFactorModel):
    """批量情绪因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    calculation_date: str = Field(..., description="计算日期，格式：YYYY-MM-DD")
    days_back: int = Field(default=7, description="向前追溯天数")
    use_model: bool = Field(default=True, description="是否使用深度学习模型")

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            if not code.isdigit() and not (
                code.startswith("SH") or code.startswith("SZ")
            ):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("calculation_date")
    def validate_calculation_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v

    @validator("days_back")
    def validate_days_back(cls, v: int) -> int:
        if v <= 0 or v > 30:
            raise ValueError("追溯天数必须在1-30之间")
        return v


class BatchSentimentFactorResponse(BaseFactorModel):
    """批量情绪因子计算响应模型"""

    calculation_date: str
    total_stocks: int
    successful_stocks: int
    failed_stocks: int
    results: list[SentimentFactorResponse]
    errors: list[dict[str, str]] | None = None


class SentimentTrendRequest(BaseFactorModel):
    """情绪趋势查询请求模型"""

    stock_code: str = Field(..., description="股票代码")
    days: int = Field(default=30, description="查询天数")

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        if not v.isdigit() and not (v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("days")
    def validate_days(cls, v: int) -> int:
        if v <= 0 or v > 365:
            raise ValueError("查询天数必须在1-365之间")
        return v


class SentimentTrendResponse(BaseFactorModel):
    """情绪趋势查询响应模型"""

    stock_code: str
    period: str
    daily_factors: list[dict[str, str | float]]
    statistics: dict[str, str | float]


class SentimentFactor(BaseFactorModel):
    """情绪因子数据模型"""

    id: int
    stock_code: str
    sentiment_factor: float
    positive_score: float
    negative_score: float
    neutral_score: float
    confidence: float
    news_count: int
    calculation_date: str
    start_date: str
    end_date: str
    volume_adjustment: float
    created_at: str
    updated_at: str


# ==================== 统一因子计算相关模型 ====================


class UnifiedFactorRequest(BaseFactorModel):
    """统一因子计算请求模型"""

    stock_code: str = Field(..., description="股票代码")
    factor_types: list[str] = Field(
        ["technical", "fundamental", "market", "sentiment"],
        description="因子类型列表"
    )
    calculation_date: str | None = Field(
        default=None, description="计算日期，格式：YYYY-MM-DD"
    )
    technical_factors: list[str] | None = Field(
        default=["MA", "RSI", "MACD"], description="技术因子列表"
    )
    fundamental_factors: list[str] | None = Field(
        default=["ROE", "ROA", "GROSS_MARGIN"], description="基本面因子列表"
    )
    market_factors: list[str] | None = Field(
        default=["total_market_cap", "turnover_rate"], description="市场因子列表"
    )
    period: str | None = Field(
        default=None, description="基本面因子报告期，格式：2023Q4或2023"
    )
    time_window: int = Field(default=7, description="情绪因子时间窗口（天）")

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        if not v.isdigit() and not (v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("factor_types")
    def validate_factor_types(cls, v: list[str]) -> list[str]:
        valid_types = {"technical", "fundamental", "market", "sentiment"}
        for factor_type in v:
            if factor_type not in valid_types:
                raise ValueError(f"不支持的因子类型：{factor_type}")
        return v

    @validator("calculation_date")
    def validate_calculation_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class UnifiedFactorResponse(BaseFactorModel):
    """统一因子计算响应模型"""

    stock_code: str
    calculation_date: str
    technical_factors: dict[str, float | dict[str, float]] | None = None
    fundamental_factors: dict[str, float] | None = None
    market_factors: dict[str, float] | None = None
    sentiment_factors: dict[str, float] | None = None
    calculation_summary: dict[str, str | int]


class BatchUnifiedFactorRequest(BaseFactorModel):
    """批量统一因子计算请求模型"""

    stock_codes: list[str] = Field(..., description="股票代码列表")
    factor_types: list[str] = Field(
        ["technical", "fundamental", "market", "sentiment"],
        description="因子类型列表"
    )
    calculation_date: str | None = Field(
        default=None, description="计算日期，格式：YYYY-MM-DD"
    )
    technical_factors: list[str] | None = Field(
        default=["MA", "RSI", "MACD"], description="技术因子列表"
    )
    fundamental_factors: list[str] | None = Field(
        default=["ROE", "ROA", "GROSS_MARGIN"], description="基本面因子列表"
    )
    market_factors: list[str] | None = Field(
        default=["total_market_cap", "turnover_rate"], description="市场因子列表"
    )
    period: str | None = Field(
        default=None, description="基本面因子报告期，格式：2023Q4或2023"
    )
    time_window: int = Field(default=7, description="情绪因子时间窗口（天）")
    parallel: bool = Field(default=True, description="是否并行计算")

    @validator("stock_codes")
    def validate_stock_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            if not code.isdigit() and not (
                code.startswith("SH") or code.startswith("SZ")
            ):
                raise ValueError(f"股票代码{code}格式不正确")
        return v

    @validator("factor_types")
    def validate_factor_types(cls, v: list[str]) -> list[str]:
        valid_types = {"technical", "fundamental", "market", "sentiment"}
        for factor_type in v:
            if factor_type not in valid_types:
                raise ValueError(f"不支持的因子类型：{factor_type}")
        return v

    @validator("calculation_date")
    def validate_calculation_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class BatchUnifiedFactorResponse(BaseFactorModel):
    """批量统一因子计算响应模型"""

    calculation_date: str
    total_stocks: int
    successful_stocks: int
    failed_stocks: int
    results: dict[str, UnifiedFactorResponse]
    errors: dict[str, str] | None = None
    performance_metrics: dict[str, float | int] | None = None


class UnifiedFactorHistoryRequest(BaseFactorModel):
    """统一因子历史数据请求模型"""

    stock_code: str = Field(..., description="股票代码")
    factor_types: list[str] = Field(
        ["technical", "fundamental", "market", "sentiment"],
        description="因子类型列表"
    )
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    factor_names: dict[str, list[str]] | None = Field(
        default=None, description="各类型因子名称列表"
    )

    @validator("stock_code")
    def validate_stock_code(cls, v: str) -> str:
        if not v.isdigit() and not (v.startswith("SH") or v.startswith("SZ")):
            raise ValueError("股票代码格式不正确")
        return v

    @validator("factor_types")
    def validate_factor_types(cls, v: list[str]) -> list[str]:
        valid_types = {"technical", "fundamental", "market", "sentiment"}
        for factor_type in v:
            if factor_type not in valid_types:
                raise ValueError(f"不支持的因子类型：{factor_type}")
        return v

    @validator("start_date", "end_date")
    def validate_dates(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("日期格式不正确，应为YYYY-MM-DD") from e
        return v


class UnifiedFactorHistoryResponse(BaseFactorModel):
    """统一因子历史数据响应模型"""

    stock_code: str
    start_date: str
    end_date: str
    technical_history: list[dict[str, str | float]] | None = None
    fundamental_history: list[dict[str, str | float]] | None = None
    market_history: list[dict[str, str | float]] | None = None
    sentiment_history: list[dict[str, str | float]] | None = None
    data_summary: dict[str, int]
