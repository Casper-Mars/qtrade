"""因子服务层模块

提供统一的因子计算服务接口，包括：
- 技术因子计算服务
- 缓存策略管理
- 数据持久化逻辑
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from ...clients.tushare_client import TushareClient
from ..calculators.fundamental import FundamentalFactorCalculator
from ..calculators.market import MarketFactorCalculator
from ..calculators.sentiment import SentimentFactorCalculator
from ..calculators.technical import TechnicalFactorCalculator
from ..dao.factor_dao import FactorDAO
from ..models.schemas import (
    BatchFundamentalFactorRequest,
    BatchFundamentalFactorResponse,
    BatchMarketFactorRequest,
    BatchMarketFactorResponse,
    BatchTechnicalFactorRequest,
    BatchTechnicalFactorResponse,
    BatchUnifiedFactorRequest,
    BatchUnifiedFactorResponse,
    FundamentalFactorRequest,
    FundamentalFactorResponse,
    MarketFactorHistoryResponse,
    MarketFactorRequest,
    MarketFactorResponse,
    TechnicalFactorHistoryResponse,
    TechnicalFactorRequest,
    TechnicalFactorResponse,
    UnifiedFactorHistoryResponse,
    UnifiedFactorRequest,
    UnifiedFactorResponse,
)

logger = logging.getLogger(__name__)


class FactorService:
    """因子服务类

    提供统一的因子计算和管理服务
    """

    def __init__(self, factor_dao: FactorDAO, data_client: TushareClient):
        """初始化因子服务

        Args:
            factor_dao: 因子数据访问对象
            data_client: Tushare数据客户端
        """
        self.factor_dao = factor_dao
        self.data_client = data_client
        self.technical_calculator = TechnicalFactorCalculator()
        self.fundamental_calculator = FundamentalFactorCalculator(data_client)
        self.market_calculator = MarketFactorCalculator(data_client)
        self.sentiment_calculator = SentimentFactorCalculator()

    async def calculate_technical_factors(
        self, request: TechnicalFactorRequest
    ) -> TechnicalFactorResponse:
        """计算技术因子

        Args:
            request: 技术因子计算请求

        Returns:
            技术因子计算响应
        """
        try:
            # 获取股票价格数据
            price_data = await self._get_price_data(
                request.stock_code, request.end_date, request.period or 100
            )

            if price_data.empty:
                raise ValueError(f"无法获取股票{request.stock_code}的价格数据")

            # 验证价格数据格式
            self.technical_calculator.validate_price_data(price_data)

            # 计算技术因子
            factors_result = self.technical_calculator.calculate_factors(
                price_data=price_data,
                factors=request.factors,
                periods=getattr(request, "periods", None),
            )

            # 保存计算结果到数据库
            calculation_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
            await self._save_technical_factors(
                request.stock_code, calculation_date, factors_result
            )

            # 构造响应
            response = TechnicalFactorResponse(
                stock_code=request.stock_code,
                calculation_date=calculation_date,
                factors=factors_result,
            )

            logger.info(
                f"成功计算股票{request.stock_code}的技术因子: {list(factors_result.keys())}"
            )
            return response

        except Exception as e:
            logger.error(f"计算技术因子失败: {str(e)}")
            raise

    async def get_technical_factor_history(
        self, stock_code: str, factor_name: str, start_date: str, end_date: str
    ) -> TechnicalFactorHistoryResponse:
        """获取技术因子历史数据

        Args:
            stock_code: 股票代码
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            技术因子历史数据响应
        """
        try:
            # 从数据库查询历史数据
            history_data = await self.factor_dao.get_factor_history(
                stock_code=stock_code,
                factor_name=factor_name,
                start_date=start_date,
                end_date=end_date,
            )

            # 构造响应数据
            data = []
            for record in history_data:
                data.append(
                    {
                        "trade_date": record["trade_date"].strftime("%Y-%m-%d"),
                        "factor_value": record["factor_value"],
                    }
                )

            response = TechnicalFactorHistoryResponse(
                stock_code=stock_code,
                factor_name=factor_name,
                start_date=start_date,
                end_date=end_date,
                data=data,
            )

            logger.info(
                f"成功获取股票{stock_code}因子{factor_name}的历史数据，共{len(data)}条记录"
            )
            return response

        except Exception as e:
            logger.error(f"获取技术因子历史数据失败: {str(e)}")
            raise

    async def batch_calculate_technical_factors(
        self, request: BatchTechnicalFactorRequest
    ) -> BatchTechnicalFactorResponse:
        """批量计算技术因子

        Args:
            request: 批量技术因子计算请求

        Returns:
            批量技术因子计算响应
        """
        calculation_date = request.end_date or datetime.now().strftime("%Y-%m-%d")
        total_stocks = len(request.stock_codes)
        successful_stocks = 0
        failed_stocks = 0
        results = {}
        errors = {}

        logger.info(f"开始批量计算技术因子，股票数量: {total_stocks}")

        for stock_code in request.stock_codes:
            try:
                # 创建单个股票的计算请求
                single_request = TechnicalFactorRequest(
                    stock_code=stock_code,
                    factors=request.factors,
                    end_date=request.end_date,
                    period=20,
                )

                # 计算技术因子
                single_response = await self.calculate_technical_factors(single_request)

                # 记录成功结果
                results[stock_code] = single_response.factors
                successful_stocks += 1

            except Exception as e:
                # 记录失败信息
                error_msg = str(e)
                errors[stock_code] = error_msg
                failed_stocks += 1
                logger.warning(f"股票{stock_code}计算失败: {error_msg}")

        response = BatchTechnicalFactorResponse(
            calculation_date=calculation_date,
            total_stocks=total_stocks,
            successful_stocks=successful_stocks,
            failed_stocks=failed_stocks,
            results=results,
            errors=errors if errors else None,
        )

        logger.info(f"批量计算完成，成功: {successful_stocks}, 失败: {failed_stocks}")
        return response

    async def _get_price_data(
        self, stock_code: str, end_date: str | None = None, period: int = 100
    ) -> pd.DataFrame:
        """获取股票价格数据

        Args:
            stock_code: 股票代码
            end_date: 结束日期
            period: 数据周期（天数）

        Returns:
            价格数据DataFrame
        """
        try:
            # 计算开始日期
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = datetime.now()

            start_dt = end_dt - timedelta(days=period)
            start_date = start_dt.strftime("%Y-%m-%d")

            # 从数据访问层获取价格数据
            price_data = await self.factor_dao.get_stock_price_data(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date or end_dt.strftime("%Y-%m-%d"),
            )

            return price_data

        except Exception as e:
            logger.error(f"获取股票{stock_code}价格数据失败: {str(e)}")
            raise

    async def _save_technical_factors(
        self,
        stock_code: str,
        calculation_date: str,
        factors_result: dict[str, float | dict[str, float]],
    ) -> None:
        """保存技术因子计算结果

        Args:
            stock_code: 股票代码
            calculation_date: 计算日期
            factors_result: 因子计算结果
        """
        try:
            for factor_name, factor_value in factors_result.items():
                if isinstance(factor_value, dict):
                    # 处理复合因子（如MACD）
                    for sub_factor, sub_value in factor_value.items():
                        await self.factor_dao.save_technical_factor(
                            stock_code=stock_code,
                            factor_name=f"{factor_name}_{sub_factor}",
                            factor_value=float(sub_value),
                            trade_date=calculation_date,
                        )
                else:
                    # 处理简单因子
                    await self.factor_dao.save_technical_factor(
                        stock_code=stock_code,
                        factor_name=factor_name,
                        factor_value=float(factor_value),
                        trade_date=calculation_date,
                    )

            logger.debug(f"成功保存股票{stock_code}的技术因子数据")

        except Exception as e:
            logger.error(f"保存技术因子数据失败: {str(e)}")
            raise

    async def get_cached_factors(
        self, stock_code: str, factor_names: list[str], calculation_date: str
    ) -> dict[str, float]:
        """获取缓存的因子数据

        Args:
            stock_code: 股票代码
            factor_names: 因子名称列表
            calculation_date: 计算日期

        Returns:
            缓存的因子数据
        """
        try:
            cached_factors = await self.factor_dao.get_cached_factors(
                stock_code=stock_code,
                factor_names=factor_names,
                calculation_date=calculation_date,
            )

            return cached_factors

        except Exception as e:
            logger.warning(f"获取缓存因子数据失败: {str(e)}")
            return {}

    async def cache_factors(
        self,
        stock_code: str,
        calculation_date: str,
        factors_data: dict[str, float],
        ttl: int = 3600,
    ) -> None:
        """缓存因子数据

        Args:
            stock_code: 股票代码
            calculation_date: 计算日期
            factors_data: 因子数据
            ttl: 缓存过期时间（秒）
        """
        try:
            await self.factor_dao.cache_factors(
                stock_code=stock_code,
                calculation_date=calculation_date,
                factors_data=factors_data,
                ttl=ttl,
            )

            logger.debug(f"成功缓存股票{stock_code}的因子数据")

        except Exception as e:
            logger.warning(f"缓存因子数据失败: {str(e)}")

    # ==================== 基本面因子服务方法 ====================

    async def calculate_fundamental_factors(
        self, request: FundamentalFactorRequest
    ) -> FundamentalFactorResponse:
        """计算基本面因子

        Args:
            request: 基本面因子计算请求

        Returns:
            基本面因子计算响应
        """
        try:
            # 检查缓存
            cached_data = await self._get_cached_fundamental_factors(
                request.stock_code, request.period
            )
            if cached_data:
                logger.info(f"从缓存获取股票{request.stock_code}的基本面因子数据")
                return cached_data

            # 计算基本面因子
            factors_result = await self.fundamental_calculator.calculate_factors(
                stock_code=request.stock_code,
                factors=request.factors,
                period=request.period,
                report_type=request.report_type,
            )

            # 计算同比增长率
            growth_rates = await self.fundamental_calculator.calculate_growth_rates(
                stock_code=request.stock_code,
                factors=request.factors,
                current_period=request.period,
            )

            # 保存计算结果到数据库
            await self.factor_dao.save_fundamental_factors(
                stock_code=request.stock_code,
                factors=factors_result,
                growth_rates=growth_rates,
                period=request.period,
                ann_date=request.period,  # 使用period作为ann_date
            )

            # 过滤None值
            filtered_factors = {k: v for k, v in factors_result.items() if v is not None}
            filtered_growth_rates = {k: v for k, v in growth_rates.items() if v is not None}
            # 构造响应
            response = FundamentalFactorResponse(
                stock_code=request.stock_code,
                period=request.period,
                report_type=request.report_type,
                factors=filtered_factors,
                growth_rates=filtered_growth_rates if filtered_growth_rates else None,
            )

            logger.info(
                f"成功计算股票{request.stock_code}的基本面因子: {list(factors_result.keys())}"
            )
            return response

        except Exception as e:
            logger.error(f"计算基本面因子失败: {str(e)}")
            raise

    async def batch_calculate_fundamental_factors(
        self, request: BatchFundamentalFactorRequest
    ) -> BatchFundamentalFactorResponse:
        """批量计算基本面因子

        Args:
            request: 批量基本面因子计算请求

        Returns:
            批量基本面因子计算响应
        """
        total_stocks = len(request.stock_codes)
        successful_stocks = 0
        failed_stocks = 0
        results = {}
        errors = {}

        logger.info(f"开始批量计算基本面因子，股票数量: {total_stocks}")

        for stock_code in request.stock_codes:
            try:
                # 创建单个股票的计算请求
                single_request = FundamentalFactorRequest(
                    stock_code=stock_code,
                    factors=request.factors,
                    period=request.period,
                    report_type=request.report_type,
                )

                # 计算基本面因子
                single_response = await self.calculate_fundamental_factors(
                    single_request
                )

                # 记录成功结果
                results[stock_code] = single_response.factors
                successful_stocks += 1

            except Exception as e:
                # 记录失败信息
                error_msg = str(e)
                errors[stock_code] = error_msg
                failed_stocks += 1
                logger.warning(f"股票{stock_code}计算失败: {error_msg}")

        response = BatchFundamentalFactorResponse(
            period=request.period,
            report_type=request.report_type,
            total_stocks=total_stocks,
            successful_stocks=successful_stocks,
            failed_stocks=failed_stocks,
            results=results,
            growth_rates=None,
            errors=errors if errors else None,
        )

        logger.info(f"批量计算完成，成功: {successful_stocks}, 失败: {failed_stocks}")
        return response

    async def get_fundamental_factor_history(
        self, stock_code: str, factor_name: str, start_period: str, end_period: str
    ) -> list[dict]:
        """获取基本面因子历史数据

        Args:
            stock_code: 股票代码
            factor_name: 因子名称
            start_period: 开始期间
            end_period: 结束期间

        Returns:
            基本面因子历史数据
        """
        try:
            history_data = await self.factor_dao.get_fundamental_factor_history(
                stock_code=stock_code,
                factor_name=factor_name,
                start_period=start_period,
                end_period=end_period,
            )

            logger.info(
                f"成功获取股票{stock_code}因子{factor_name}的历史数据，共{len(history_data)}条记录"
            )
            return history_data

        except Exception as e:
            logger.error(f"获取基本面因子历史数据失败: {str(e)}")
            raise

    async def _get_cached_fundamental_factors(
        self, stock_code: str, period: str
    ) -> FundamentalFactorResponse | None:
        """获取缓存的基本面因子数据

        Args:
            stock_code: 股票代码
            period: 报告期间

        Returns:
            缓存的基本面因子响应或None
        """
        try:
            cached_data = await self.factor_dao.get_cached_fundamental_factors(
                stock_code=stock_code, period=period
            )

            if cached_data:
                return FundamentalFactorResponse(
                    stock_code=stock_code,
                    period=period,
                    report_type=cached_data.get("report_type", "annual"),
                    factors=cached_data.get("factors", {}),
                    growth_rates=cached_data.get("growth_rates", {}),
                )

            return None

        except Exception as e:
            logger.warning(f"获取缓存基本面因子数据失败: {str(e)}")
            return None

    # ==================== 市场因子相关方法 ====================

    async def calculate_market_factors(
        self, request: MarketFactorRequest
    ) -> MarketFactorResponse:
        """计算市场因子

        Args:
            request: 市场因子计算请求

        Returns:
            市场因子计算响应
        """
        try:
            # 获取交易日期
            trade_date = request.trade_date or datetime.now().strftime("%Y-%m-%d")

            # 计算市场因子
            factors_result = {}
            for factor_name in request.factors:
                if factor_name == "total_market_cap":
                    value = await self.market_calculator.calculate_market_cap(
                        request.stock_code, trade_date
                    )
                elif factor_name == "tradable_market_cap":
                    value = await self.market_calculator.calculate_float_market_cap(
                        request.stock_code, trade_date
                    )
                elif factor_name == "turnover_rate":
                    value = await self.market_calculator.calculate_turnover_rate(
                        request.stock_code, trade_date
                    )
                elif factor_name == "volume_ratio":
                    value = await self.market_calculator.calculate_volume_ratio(
                        request.stock_code, trade_date
                    )
                elif factor_name == "price_volatility":
                    value = await self.market_calculator.calculate_price_volatility(
                        request.stock_code, trade_date
                    )
                elif factor_name == "return_volatility":
                    value = await self.market_calculator.calculate_return_volatility(
                        request.stock_code, trade_date
                    )
                elif factor_name == "price_momentum":
                    value = await self.market_calculator.calculate_price_momentum(
                        request.stock_code, trade_date
                    )
                elif factor_name == "return_momentum":
                    value = await self.market_calculator.calculate_return_momentum(
                        request.stock_code, trade_date
                    )
                else:
                    logger.warning(f"未知的市场因子: {factor_name}")
                    continue

                factors_result[factor_name] = value

            # 保存计算结果到数据库
            await self._save_market_factors(
                request.stock_code, trade_date, factors_result
            )

            # 构造响应
            response = MarketFactorResponse(
                stock_code=request.stock_code,
                trade_date=trade_date,
                factors=factors_result,
            )

            logger.info(
                f"成功计算股票{request.stock_code}的市场因子: {list(factors_result.keys())}"
            )
            return response

        except Exception as e:
            logger.error(f"计算市场因子失败: {str(e)}")
            raise

    async def get_market_factor_history(
        self, stock_code: str, factor_name: str, start_date: str, end_date: str
    ) -> MarketFactorHistoryResponse:
        """获取市场因子历史数据

        Args:
            stock_code: 股票代码
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            市场因子历史数据响应
        """
        try:
            history_data = await self.factor_dao.get_market_factor_history(
                stock_code=stock_code,
                factor_name=factor_name,
                start_date=start_date,
                end_date=end_date,
            )

            response = MarketFactorHistoryResponse(
                stock_code=stock_code,
                factor_name=factor_name,
                start_date=start_date,
                end_date=end_date,
                data=history_data,
            )

            logger.info(
                f"成功获取股票{stock_code}因子{factor_name}的历史数据，共{len(history_data)}条记录"
            )
            return response

        except Exception as e:
            logger.error(f"获取市场因子历史数据失败: {str(e)}")
            raise

    async def batch_calculate_market_factors(
        self, request: BatchMarketFactorRequest
    ) -> BatchMarketFactorResponse:
        """批量计算市场因子

        Args:
            request: 批量市场因子计算请求

        Returns:
            批量市场因子计算响应
        """
        try:
            trade_date = request.trade_date or datetime.now().strftime("%Y-%m-%d")
            total_stocks = len(request.stock_codes)
            successful_stocks = 0
            failed_stocks = 0
            results = {}
            errors = {}

            for stock_code in request.stock_codes:
                try:
                    # 为每个股票创建单独的请求
                    single_request = MarketFactorRequest(
                        stock_code=stock_code,
                        factors=request.factors,
                        trade_date=trade_date,
                    )

                    # 计算市场因子
                    single_response = await self.calculate_market_factors(
                        single_request
                    )
                    results[stock_code] = single_response.factors
                    successful_stocks += 1

                except Exception as e:
                    logger.error(f"计算股票{stock_code}的市场因子失败: {str(e)}")
                    errors[stock_code] = str(e)
                    failed_stocks += 1

            # 构造响应
            response = BatchMarketFactorResponse(
                trade_date=trade_date,
                total_stocks=total_stocks,
                successful_stocks=successful_stocks,
                failed_stocks=failed_stocks,
                results=results,
                errors=errors if errors else None,
            )

            logger.info(f"批量计算完成，成功: {successful_stocks}, 失败: {failed_stocks}")
            return response

        except Exception as e:
            logger.error(f"批量计算市场因子失败: {str(e)}")
            raise

    async def _save_market_factors(
        self, stock_code: str, trade_date: str, factors: dict[str, float]
    ) -> None:
        """保存市场因子到数据库

        Args:
            stock_code: 股票代码
            trade_date: 交易日期
            factors: 因子数据
        """
        try:
            await self.factor_dao.save_market_factors(
                stock_code=stock_code, trade_date=trade_date, factors=factors
            )
            logger.debug(f"成功保存股票{stock_code}的市场因子数据")

        except Exception as e:
            logger.error(f"保存市场因子数据失败: {str(e)}")
            # 不抛出异常，避免影响计算流程
            pass

    # ==================== 统一因子计算方法 ====================

    async def calculate_all_factors(
        self, request: UnifiedFactorRequest
    ) -> UnifiedFactorResponse:
        """计算所有类型的因子

        Args:
            request: 统一因子计算请求

        Returns:
            统一因子计算响应
        """
        try:
            from datetime import datetime, timedelta
            all_factors: dict[str, dict[str, float] | dict[str, float | dict[str, float]] | None] = {}
            calculation_date = request.calculation_date or datetime.now().strftime("%Y-%m-%d")

            # 计算技术因子
            if "technical" in request.factor_types and request.technical_factors:
                tech_request = TechnicalFactorRequest(
                    stock_code=request.stock_code,
                    factors=request.technical_factors,
                    end_date=calculation_date,
                )
                tech_response = await self.calculate_technical_factors(tech_request)
                # 技术因子可能包含嵌套字典
                all_factors["technical_factors"] = tech_response.factors

            # 计算基本面因子
            if "fundamental" in request.factor_types and request.fundamental_factors:
                fund_request = FundamentalFactorRequest(
                    stock_code=request.stock_code,
                    factors=request.fundamental_factors,
                    period=request.period or calculation_date[:4],
                )
                fund_response = await self.calculate_fundamental_factors(fund_request)
                # 基本面因子直接赋值
                all_factors["fundamental_factors"] = fund_response.factors

            # 计算市场因子
            if "market" in request.factor_types and request.market_factors:
                market_request = MarketFactorRequest(
                    stock_code=request.stock_code,
                    factors=request.market_factors,
                    trade_date=calculation_date,
                )
                market_response = await self.calculate_market_factors(market_request)
                # 市场因子直接赋值
                all_factors["market_factors"] = market_response.factors

            # 计算情绪因子
            if "sentiment" in request.factor_types:
                try:
                    end_date = datetime.strptime(calculation_date, "%Y-%m-%d")
                    start_date = end_date - timedelta(days=request.time_window)

                    sentiment_data = await self.sentiment_calculator.calculate_stock_sentiment_factor(
                        request.stock_code, start_date, end_date
                    )

                    # 提取情绪详情
                    sentiment_details = sentiment_data.get("sentiment_details", {})
                    all_factors["sentiment_factors"] = {
                        "sentiment_factor": sentiment_data.get("sentiment_factor", 0.0),
                        "positive_score": sentiment_details.get("positive_score", 0.0),
                        "negative_score": sentiment_details.get("negative_score", 0.0),
                        "neutral_score": sentiment_details.get("neutral_score", 0.0),
                        "confidence": sentiment_details.get("confidence", 0.0),
                        "news_count": sentiment_details.get("news_count", 0),
                    }
                except Exception as e:
                    logger.warning(f"计算情绪因子失败: {str(e)}")
                    # 情绪因子计算失败时不添加到all_factors中

            # 构建计算摘要
            calculation_summary: dict[str, str | int] = {
                "total_factor_types": len([k for k, v in all_factors.items() if v is not None]),
                "calculation_time": datetime.now().isoformat(),
                "status": "success"
            }

            # 类型转换以匹配UnifiedFactorResponse的期望类型
            technical_factors: dict[str, float | dict[str, float]] | None = None
            fundamental_factors: dict[str, float] | None = None
            market_factors: dict[str, float] | None = None
            sentiment_factors: dict[str, float] | None = None

            # 安全获取技术因子
            tech_data = all_factors.get("technical_factors")
            if isinstance(tech_data, dict):
                technical_factors = tech_data  # type: ignore

            # 安全获取基本面因子
            fund_data = all_factors.get("fundamental_factors")
            if isinstance(fund_data, dict) and all(isinstance(v, int | float) for v in fund_data.values()):
                fundamental_factors = fund_data  # type: ignore

            # 安全获取市场因子
            market_data = all_factors.get("market_factors")
            if isinstance(market_data, dict) and all(isinstance(v, int | float) for v in market_data.values()):
                market_factors = market_data  # type: ignore

            # 安全获取情绪因子
            sentiment_factor_data = all_factors.get("sentiment_factors")
            if isinstance(sentiment_factor_data, dict) and all(isinstance(v, int | float) for v in sentiment_factor_data.values()):
                sentiment_factors = {k: float(v) for k, v in sentiment_factor_data.items() if isinstance(v, int | float)}

            response = UnifiedFactorResponse(
                stock_code=request.stock_code,
                calculation_date=calculation_date,
                technical_factors=technical_factors,
                fundamental_factors=fundamental_factors,
                market_factors=market_factors,
                sentiment_factors=sentiment_factors,
                calculation_summary=calculation_summary,
            )

            logger.info(
                f"成功计算股票{request.stock_code}的所有因子类型: {list(all_factors.keys())}"
            )
            return response

        except Exception as e:
            logger.error(f"计算统一因子失败: {str(e)}")
            raise

    async def batch_calculate_all_factors(
        self, request: BatchUnifiedFactorRequest
    ) -> BatchUnifiedFactorResponse:
        """批量计算所有类型的因子

        Args:
            request: 批量统一因子计算请求

        Returns:
            批量统一因子计算响应
        """
        calculation_date = request.calculation_date or datetime.now().strftime("%Y-%m-%d")
        total_stocks = len(request.stock_codes)
        successful_stocks = 0
        failed_stocks = 0
        results = {}
        errors = {}

        logger.info(f"开始批量计算所有因子，股票数量: {total_stocks}")

        for stock_code in request.stock_codes:
            try:
                # 创建单个股票的计算请求
                single_request = UnifiedFactorRequest(
                    stock_code=stock_code,
                    factor_types=request.factor_types,
                    technical_factors=request.technical_factors,
                    fundamental_factors=request.fundamental_factors,
                    market_factors=request.market_factors,
                    calculation_date=calculation_date,
                    period=request.period,
                    time_window=request.time_window,
                )

                # 计算所有因子
                single_response = await self.calculate_all_factors(single_request)

                # 记录成功结果
                results[stock_code] = single_response
                successful_stocks += 1

            except Exception as e:
                # 记录失败信息
                error_msg = str(e)
                errors[stock_code] = error_msg
                failed_stocks += 1
                logger.warning(f"股票{stock_code}计算失败: {error_msg}")

        response = BatchUnifiedFactorResponse(
            calculation_date=calculation_date,
            total_stocks=total_stocks,
            successful_stocks=successful_stocks,
            failed_stocks=failed_stocks,
            results=results,
            errors=errors if errors else None,
        )

        logger.info(f"批量计算完成，成功: {successful_stocks}, 失败: {failed_stocks}")
        return response

    async def get_all_factors_history(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        technical_factors: list[str] | None = None,
        fundamental_factors: list[str] | None = None,
        market_factors: list[str] | None = None,
    ) -> UnifiedFactorHistoryResponse:
        """获取所有类型因子的历史数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            technical_factors: 技术因子列表
            fundamental_factors: 基本面因子列表
            market_factors: 市场因子列表

        Returns:
            统一因子历史数据响应
        """
        try:
            # 初始化历史数据列表
            technical_history: list[dict[str, str | float]] = []
            fundamental_history: list[dict[str, str | float]] = []
            market_history: list[dict[str, str | float]] = []
            sentiment_history: list[dict[str, str | float]] = []

            # 获取技术因子历史数据
            if technical_factors:
                for factor_name in technical_factors:
                    tech_history = await self.get_technical_factor_history(
                        stock_code, factor_name, start_date, end_date
                    )
                    if tech_history and tech_history.data:
                        technical_history.extend(tech_history.data)

            # 获取基本面因子历史数据
            if fundamental_factors:
                for factor_name in fundamental_factors:
                    fund_history = await self.get_fundamental_factor_history(
                        stock_code, factor_name, start_date, end_date
                    )
                    if fund_history:
                        fundamental_history.extend(fund_history)

            # 获取市场因子历史数据
            if market_factors:
                for factor_name in market_factors:
                    market_hist = await self.get_market_factor_history(
                        stock_code, factor_name, start_date, end_date
                    )
                    if market_hist and market_hist.data:
                        market_history.extend(market_hist.data)

            # 构建数据摘要
            data_summary = {
                "technical_count": len(technical_history),
                "fundamental_count": len(fundamental_history),
                "market_count": len(market_history),
                "sentiment_count": len(sentiment_history),
            }

            response = UnifiedFactorHistoryResponse(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                technical_history=technical_history if technical_history else None,
                fundamental_history=fundamental_history if fundamental_history else None,
                market_history=market_history if market_history else None,
                sentiment_history=sentiment_history if sentiment_history else None,
                data_summary=data_summary,
            )

            logger.info(
                f"成功获取股票{stock_code}的所有因子历史数据，时间范围: {start_date} - {end_date}"
            )
            return response

        except Exception as e:
            logger.error(f"获取统一因子历史数据失败: {str(e)}")
            raise
