"""基本面因子计算器模块

实现各种基本面财务指标的计算，包括：
- ROE (净资产收益率)
- ROA (总资产收益率)
- 毛利率 (Gross Margin)
- 净利率 (Net Margin)
- 资产负债率 (Debt Ratio)
- 流动比率 (Current Ratio)
- 同比和环比增长率计算
"""

import logging
from typing import Any

from ...clients.tushare_client import TushareClient

logger = logging.getLogger(__name__)


class FundamentalFactorCalculator:
    """基本面因子计算器

    提供各种基本面财务指标的计算功能
    """

    def __init__(self, data_client: TushareClient) -> None:
        """初始化基本面因子计算器

        Args:
            data_client: Tushare数据客户端
        """
        self.data_client = data_client
        self.supported_factors = {
            "ROE": self.calculate_roe,
            "ROA": self.calculate_roa,
            "GROSS_MARGIN": self.calculate_gross_margin,
            "NET_MARGIN": self.calculate_net_profit_margin,
            "DEBT_RATIO": self.calculate_debt_ratio,
            "CURRENT_RATIO": self.calculate_current_ratio,
        }

    async def calculate_factors(
        self,
        stock_code: str,
        factors: list[str],
        period: str,
        report_type: str = "quarterly",
    ) -> dict[str, float | None]:
        """计算指定的基本面因子

        Args:
            stock_code: 股票代码
            factors: 要计算的因子列表
            period: 报告期，如2023Q3
            report_type: 报告类型，quarterly或annual

        Returns:
            计算结果字典，包含factors和growth_rates
        """
        try:
            # 获取财务数据
            financial_data = await self._get_financial_data(
                stock_code, period, report_type
            )
            if not financial_data:
                raise ValueError(f"无法获取股票{stock_code}在{period}的财务数据")

            # 计算各项因子
            factor_results = {}
            for factor in factors:
                if factor in self.supported_factors:
                    try:
                        value = await self.supported_factors[factor](
                            stock_code, period, financial_data
                        )
                        factor_results[factor] = value
                    except Exception as e:
                        logger.warning(f"计算因子{factor}失败: {e}")
                        factor_results[factor] = None
                else:
                    logger.warning(f"不支持的因子: {factor}")
                    factor_results[factor] = None

            return factor_results

        except Exception as e:
            logger.error(f"计算基本面因子失败: {e}")
            raise

    async def calculate_roe(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算净资产收益率 ROE = 净利润 / 平均股东权益

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            ROE值
        """
        try:
            net_profit = financial_data.get("net_profit", 0)
            total_equity = financial_data.get("total_equity", 0)

            if total_equity == 0:
                return None

            # 获取期初股东权益计算平均值
            prev_period = self._get_previous_period(period)
            prev_financial_data = await self._get_financial_data(
                stock_code, prev_period
            )

            if prev_financial_data:
                prev_equity = prev_financial_data.get("total_equity", total_equity)
                avg_equity = (total_equity + prev_equity) / 2
            else:
                avg_equity = total_equity

            if avg_equity == 0:
                return None

            roe = net_profit / avg_equity
            return float(round(roe, 6))

        except Exception as e:
            logger.error(f"计算ROE失败: {e}")
            return None

    async def calculate_roa(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算总资产收益率 ROA = 净利润 / 平均总资产

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            ROA值
        """
        try:
            net_profit = financial_data.get("net_profit", 0)
            total_assets = financial_data.get("total_assets", 0)

            if total_assets == 0:
                return None

            # 获取期初总资产计算平均值
            prev_period = self._get_previous_period(period)
            prev_financial_data = await self._get_financial_data(
                stock_code, prev_period
            )

            if prev_financial_data:
                prev_assets = prev_financial_data.get("total_assets", total_assets)
                avg_assets = (total_assets + prev_assets) / 2
            else:
                avg_assets = total_assets

            if avg_assets == 0:
                return None

            roa = net_profit / avg_assets
            return float(round(roa, 6))

        except Exception as e:
            logger.error(f"计算ROA失败: {e}")
            return None

    async def calculate_gross_margin(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算毛利率 = (营业收入 - 营业成本) / 营业收入

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            毛利率
        """
        try:
            revenue = financial_data.get("revenue", 0)
            cost_of_sales = financial_data.get("cost_of_sales", 0)

            if revenue == 0:
                return None

            gross_margin = (revenue - cost_of_sales) / revenue
            return float(round(gross_margin, 6))

        except Exception as e:
            logger.error(f"计算毛利率失败: {e}")
            return None

    async def calculate_net_profit_margin(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算净利率 = 净利润 / 营业收入

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            净利率
        """
        try:
            net_profit = financial_data.get("net_profit", 0)
            revenue = financial_data.get("revenue", 0)

            if revenue == 0:
                return None

            net_margin = net_profit / revenue
            return float(round(net_margin, 6))

        except Exception as e:
            logger.error(f"计算净利率失败: {e}")
            return None

    async def calculate_debt_ratio(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算资产负债率 = 总负债 / 总资产

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            资产负债率
        """
        try:
            total_liabilities = financial_data.get("total_liabilities", 0)
            total_assets = financial_data.get("total_assets", 0)

            if total_assets == 0:
                return None

            debt_ratio = total_liabilities / total_assets
            return float(round(debt_ratio, 6))

        except Exception as e:
            logger.error(f"计算资产负债率失败: {e}")
            return None

    async def calculate_current_ratio(
        self, stock_code: str, period: str, financial_data: dict
    ) -> float | None:
        """计算流动比率 = 流动资产 / 流动负债

        Args:
            stock_code: 股票代码
            period: 报告期
            financial_data: 财务数据

        Returns:
            流动比率
        """
        try:
            current_assets = financial_data.get("current_assets", 0)
            current_liabilities = financial_data.get("current_liabilities", 0)

            if current_liabilities == 0:
                return None

            current_ratio = current_assets / current_liabilities
            return float(round(current_ratio, 6))

        except Exception as e:
            logger.error(f"计算流动比率失败: {e}")
            return None

    async def calculate_growth_rates(
        self,
        stock_code: str,
        current_period: str,
        factors: list[str],
        report_type: str = "quarterly",
    ) -> dict[str, float | None]:
        """计算同比增长率

        Args:
            stock_code: 股票代码
            current_period: 当前报告期
            factors: 因子列表
            report_type: 报告类型

        Returns:
            增长率字典
        """
        growth_rates: dict[str, float | None] = {}

        try:
            # 获取上年同期
            prev_year_period = self._get_previous_year_period(current_period)

            # 获取当前期和上年同期的财务数据
            current_data = await self._get_financial_data(
                stock_code, current_period, report_type
            )
            prev_data = await self._get_financial_data(
                stock_code, prev_year_period, report_type
            )

            if not current_data or not prev_data:
                logger.warning(f"无法获取{stock_code}的历史数据进行同比计算")
                return {f"{factor}_YOY": None for factor in factors}

            # 计算各因子的同比增长率
            for factor in factors:
                if factor in self.supported_factors:
                    try:
                        current_value = await self.supported_factors[factor](
                            stock_code, current_period, current_data
                        )
                        prev_value = await self.supported_factors[factor](
                            stock_code, prev_year_period, prev_data
                        )

                        if (
                            current_value is not None
                            and prev_value is not None
                            and prev_value != 0
                        ):
                            growth_rate = (current_value - prev_value) / abs(prev_value)
                            growth_rates[f"{factor}_YOY"] = round(growth_rate, 6)
                        else:
                            growth_rates[f"{factor}_YOY"] = None
                    except Exception as e:
                        logger.warning(f"计算{factor}同比增长率失败: {e}")
                        growth_rates[f"{factor}_YOY"] = None

        except Exception as e:
            logger.error(f"计算同比增长率失败: {e}")

        return growth_rates

    async def _get_financial_data(
        self, stock_code: str, period: str, report_type: str = "quarterly"
    ) -> dict[str, Any] | None:
        """获取财务数据

        Args:
            stock_code: 股票代码
            period: 报告期，如2023Q3或2023
            report_type: 报告类型，quarterly或annual

        Returns:
            财务数据字典
        """
        try:
            # 转换股票代码格式（如000001 -> 000001.SZ）
            ts_code = self._convert_stock_code(stock_code)

            # 解析期间
            if report_type == "quarterly":
                # 解析季度期间，如2023Q3 -> 20230930
                end_date = self._parse_quarter_period(period)
                period_type = 'Q'
            else:
                # 年度数据
                end_date = f"{period}1231"
                period_type = 'A'

            # 获取利润表数据
            income_data = await self.data_client.get_income_statement(
                ts_code=ts_code,
                end_date=end_date,
                period=period_type
            )

            # 获取资产负债表数据
            balance_data = await self.data_client.get_balance_sheet(
                ts_code=ts_code,
                end_date=end_date,
                period=period_type
            )

            # 获取现金流量表数据
            cashflow_data = await self.data_client.get_cashflow_statement(
                ts_code=ts_code,
                end_date=end_date,
                period=period_type
            )

            # 获取财务指标数据
            indicator_data = await self.data_client.get_financial_indicators(
                ts_code=ts_code,
                end_date=end_date,
                period=period_type
            )

            # 合并财务数据
            financial_data = {}

            # 处理利润表数据
            if not income_data.empty:
                latest_income = income_data.iloc[0].to_dict()
                financial_data.update({
                    'revenue': latest_income.get('revenue', 0),  # 营业收入
                    'total_profit': latest_income.get('total_profit', 0),  # 利润总额
                    'n_income': latest_income.get('n_income', 0),  # 净利润
                    'operate_profit': latest_income.get('operate_profit', 0),  # 营业利润
                    'oper_cost': latest_income.get('oper_cost', 0),  # 营业成本
                })

            # 处理资产负债表数据
            if not balance_data.empty:
                latest_balance = balance_data.iloc[0].to_dict()
                financial_data.update({
                    'total_assets': latest_balance.get('total_assets', 0),  # 总资产
                    'total_liab': latest_balance.get('total_liab', 0),  # 总负债
                    'total_hldr_eqy_exc_min_int': latest_balance.get('total_hldr_eqy_exc_min_int', 0),  # 股东权益
                    'total_cur_assets': latest_balance.get('total_cur_assets', 0),  # 流动资产
                    'total_cur_liab': latest_balance.get('total_cur_liab', 0),  # 流动负债
                })

            # 处理现金流量表数据
            if not cashflow_data.empty:
                latest_cashflow = cashflow_data.iloc[0].to_dict()
                financial_data.update({
                    'n_cashflow_act': latest_cashflow.get('n_cashflow_act', 0),  # 经营活动现金流
                })

            # 处理财务指标数据
            if not indicator_data.empty:
                latest_indicator = indicator_data.iloc[0].to_dict()
                financial_data.update({
                    'roe': latest_indicator.get('roe', 0),  # ROE
                    'roa': latest_indicator.get('roa', 0),  # ROA
                    'gross_margin': latest_indicator.get('grossprofit_margin', 0),  # 毛利率
                    'netprofit_margin': latest_indicator.get('netprofit_margin', 0),  # 净利率
                    'debt_to_assets': latest_indicator.get('debt_to_assets', 0),  # 资产负债率
                    'current_ratio': latest_indicator.get('current_ratio', 0),  # 流动比率
                })

            return financial_data if financial_data else None

        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return None

    def _convert_stock_code(self, stock_code: str) -> str:
        """转换股票代码格式

        Args:
            stock_code: 原始股票代码，如000001

        Returns:
            Tushare格式的股票代码，如000001.SZ
        """
        if '.' in stock_code:
            return stock_code

        # 根据股票代码判断交易所
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"  # 上海证券交易所
        elif stock_code.startswith(('0', '3')):
            return f"{stock_code}.SZ"  # 深圳证券交易所
        else:
            # 默认深圳
            return f"{stock_code}.SZ"

    def _parse_quarter_period(self, period: str) -> str:
        """解析季度期间

        Args:
            period: 季度期间，如2023Q3

        Returns:
            结束日期，如20230930
        """
        if 'Q' not in period:
            return f"{period}1231"  # 如果不是季度格式，默认为年末

        year, quarter = period.split('Q')
        quarter_end_dates = {
            '1': '0331',
            '2': '0630',
            '3': '0930',
            '4': '1231'
        }

        return f"{year}{quarter_end_dates.get(quarter, '1231')}"



    def _get_previous_period(self, period: str) -> str:
        """获取上一期间

        Args:
            period: 当前期间，如2023Q3

        Returns:
            上一期间，如2023Q2
        """
        try:
            if "Q" in period:
                year_str, quarter_str = period.split("Q")
                year = int(year_str)
                quarter = int(quarter_str)

                if quarter == 1:
                    return f"{year - 1}Q4"
                else:
                    return f"{year}Q{quarter - 1}"
            else:
                # 年度数据
                return str(int(period) - 1)
        except Exception:
            return period





    def _get_previous_year_period(self, period: str) -> str:
        """获取上年同期

        Args:
            period: 当前期间，如2023Q3

        Returns:
            上年同期，如2022Q3
        """
        try:
            if "Q" in period:
                year_str, quarter_str = period.split("Q")
                return f"{int(year_str) - 1}Q{quarter_str}"
            else:
                # 年度数据
                return str(int(period) - 1)
        except Exception:
            return period
