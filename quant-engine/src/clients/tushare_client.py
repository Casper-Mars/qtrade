"""Tushare金融数据客户端"""

import asyncio
from collections.abc import Callable
from typing import Any, Dict, List

import pandas as pd
import tushare as ts  # type: ignore
from loguru import logger

from ..config.settings import settings
from ..utils.exceptions import DataSourceError


class TushareClient:
    """Tushare金融数据客户端

    提供股票基本信息、日线数据、财务报表数据等金融数据获取功能
    """

    def __init__(self) -> None:
        """初始化Tushare客户端"""
        self._api: Any | None = None
        self._initialized = False

    async def __aenter__(self) -> "TushareClient":
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器退出"""
        # Tushare客户端不需要特殊的清理操作
        pass

    async def initialize(self) -> None:
        """初始化Tushare API连接"""
        try:
            if not settings.tushare_token:
                raise DataSourceError("Tushare token未配置")

            # 设置token
            ts.set_token(settings.tushare_token)

            # 获取API实例
            self._api = ts.pro_api()

            # 测试连接
            await self._test_connection()

            self._initialized = True
            logger.info("Tushare客户端初始化成功")

        except Exception as e:
            logger.error(f"Tushare客户端初始化失败: {e}")
            raise DataSourceError(f"Tushare客户端初始化失败: {e}") from e

    async def _test_connection(self) -> None:
        """测试Tushare连接"""
        try:
            # 获取交易日历测试连接
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            
            # 直接调用API，不使用重试机制避免递归
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: api.trade_cal(exchange='SSE', start_date='20240101', end_date='20240102')
            )
            if result is None or len(result) == 0:
                raise DataSourceError("Tushare连接测试失败")
            logger.info("Tushare连接测试成功")
        except Exception as e:
            error_msg = str(e)
            # 如果是权限问题，记录警告但不阻止初始化
            if "没有接口访问权限" in error_msg or "权限" in error_msg:
                logger.warning(f"Tushare权限受限，将以受限模式运行: {error_msg}")
                return  # 允许初始化继续
            # 其他错误仍然抛出异常
            raise DataSourceError(f"Tushare连接测试失败: {e}") from e

    async def _execute_with_retry(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """带重试机制的API调用"""
        if not self._initialized:
            await self.initialize()

        last_error = None

        for attempt in range(settings.tushare_retry_count):
            try:
                # 在线程池中执行同步调用
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Tushare API调用失败 (尝试 {attempt + 1}/{settings.tushare_retry_count}): {e}")

                if attempt < settings.tushare_retry_count - 1:
                    await asyncio.sleep(settings.tushare_retry_delay)

        raise DataSourceError(f"Tushare API调用失败，已重试{settings.tushare_retry_count}次: {last_error}")

    async def get_stock_basic(self,
                             exchange: str | None = None,
                             list_status: str = 'L') -> Any:
        """获取股票基本信息

        Args:
            exchange: 交易所代码 SSE上交所 SZSE深交所
            list_status: 上市状态 L上市 D退市 P暂停上市

        Returns:
            包含股票基本信息的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.stock_basic(
                    exchange=exchange,
                    list_status=list_status,
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
            )

            if result is None or len(result) == 0:
                logger.warning("获取股票基本信息为空")
                return pd.DataFrame()

            logger.info(f"成功获取{len(result)}条股票基本信息")
            return result

        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            raise DataSourceError(f"获取股票基本信息失败: {e}") from e

    async def get_daily_data(self,
                           ts_code: str,
                           start_date: str | None = None,
                           end_date: str | None = None,
                           limit: int = 1000) -> Any:
        """获取股票日线数据

        Args:
            ts_code: 股票代码 (如: 000001.SZ)
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)
            limit: 数据条数限制

        Returns:
            包含日线数据的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )
            )

            if result is None or len(result) == 0:
                logger.warning(f"股票{ts_code}日线数据为空")
                return pd.DataFrame()

            # 按日期排序
            result = result.sort_values('trade_date')

            logger.info(f"成功获取股票{ts_code}的{len(result)}条日线数据")
            return result

        except Exception as e:
            logger.error(f"获取股票{ts_code}日线数据失败: {e}")
            raise DataSourceError(f"获取股票{ts_code}日线数据失败: {e}") from e

    async def get_income_statement(self,
                                 ts_code: str,
                                 start_date: str | None = None,
                                 end_date: str | None = None,
                                 period: str = 'A') -> Any:
        """获取利润表数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 报告期类型 A年报 Q季报

        Returns:
            包含利润表数据的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.income(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_revenue,revenue,oper_profit,total_profit,n_income,n_income_attr_p'
                )
            )

            if result is None or len(result) == 0:
                logger.warning(f"股票{ts_code}利润表数据为空")
                return pd.DataFrame()

            logger.info(f"成功获取股票{ts_code}的{len(result)}条利润表数据")
            return result

        except Exception as e:
            logger.error(f"获取股票{ts_code}利润表数据失败: {e}")
            raise DataSourceError(f"获取股票{ts_code}利润表数据失败: {e}") from e

    async def get_balance_sheet(self,
                              ts_code: str,
                              start_date: str | None = None,
                              end_date: str | None = None,
                              period: str = 'A') -> Any:
        """获取资产负债表数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 报告期类型 A年报 Q季报

        Returns:
            包含资产负债表数据的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.balancesheet(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_assets,total_liab,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int'
                )
            )

            if result is None or len(result) == 0:
                logger.warning(f"股票{ts_code}资产负债表数据为空")
                return pd.DataFrame()

            logger.info(f"成功获取股票{ts_code}的{len(result)}条资产负债表数据")
            return result

        except Exception as e:
            logger.error(f"获取股票{ts_code}资产负债表数据失败: {e}")
            raise DataSourceError(f"获取股票{ts_code}资产负债表数据失败: {e}") from e

    async def get_cashflow_statement(self,
                                   ts_code: str,
                                   start_date: str | None = None,
                                   end_date: str | None = None,
                                   period: str = 'A') -> Any:
        """获取现金流量表数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 报告期类型 A年报 Q季报

        Returns:
            包含现金流量表数据的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.cashflow(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,net_profit,finan_exp,c_fr_sale_sg,recp_tax_rends,n_cashflow_act,c_paid_invest,c_disp_withdrwl_invest,n_cashflow_inv_act,c_recp_borrow,proc_issue_bonds,c_pay_dist_dpcp_int_exp,n_cashflow_fin_act,c_recp_cap_contrib,n_incr_cash_cash_equ'
                )
            )

            if result is None or len(result) == 0:
                logger.warning(f"股票{ts_code}现金流量表数据为空")
                return pd.DataFrame()

            logger.info(f"成功获取股票{ts_code}的{len(result)}条现金流量表数据")
            return result

        except Exception as e:
            logger.error(f"获取股票{ts_code}现金流量表数据失败: {e}")
            raise DataSourceError(f"获取股票{ts_code}现金流量表数据失败: {e}") from e

    async def get_financial_indicators(self,
                                     ts_code: str,
                                     start_date: str | None = None,
                                     end_date: str | None = None,
                                     period: str = 'A') -> Any:
        """获取财务指标数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 报告期类型 A年报 Q季报

        Returns:
            包含财务指标数据的DataFrame
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            result = await self._execute_with_retry(
                lambda: api.fina_indicator(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    fields='ts_code,ann_date,end_date,eps,dt_eps,total_revenue_ps,revenue_ps,capital_rese_ps,surplus_rese_ps,undist_profit_ps,extra_item,profit_dedt,gross_margin,current_ratio,quick_ratio,cash_ratio,invturn_days,arturn_days,inv_turn,ar_turn,ca_turn,fa_turn,assets_turn,op_income,valuechange_income,interst_income,daa,ebit,ebitda,fcff,fcfe,current_exint,noncurrent_exint,interestdebt,netdebt,tangible_asset,working_capital,networking_capital,invest_capital,retained_earnings,diluted2_eps,bps,ocfps,retainedps,cfps,ebit_ps,fcff_ps,fcfe_ps,netprofit_margin,grossprofit_margin,cogs_of_sales,expense_of_sales,profit_to_gr,saleexp_to_gr,adminexp_of_gr,finaexp_of_gr,impai_ttm,gc_of_gr,op_of_gr,ebit_of_gr,roe,roe_waa,roe_dt,roa,npta,roic,roe_yearly,roa_yearly,roe_avg,opincome_of_ebt,investincome_of_ebt,n_op_profit_of_ebt,tax_to_ebt,dtprofit_to_profit,salescash_to_or,ocf_to_or,ocf_to_opincome,capitalized_to_da,debt_to_assets,assets_to_eqt,dp_assets_to_eqt,ca_to_assets,nca_to_assets,tbassets_to_totalassets,int_to_talcap,eqt_to_talcapital,currentdebt_to_debt,longdeb_to_debt,ocf_to_shortdebt,debt_to_eqt,eqt_to_debt,eqt_to_interestdebt,tangibleasset_to_debt,tangasset_to_intdebt,tangibleasset_to_netdebt,ocf_to_debt,ocf_to_interestdebt,ocf_to_netdebt,ebit_to_interest,longdebt_to_workingcapital,ebitda_to_debt,turn_days,roa_yearly,roa_dp,fixed_assets,profit_prefin_exp,non_op_profit,op_to_ebt,nop_to_ebt,ocf_to_profit,cash_to_liqdebt,cash_to_liqdebt_withinterest,op_to_liqdebt,op_to_debt,roic_yearly,total_fa_trun,profit_to_op,q_opincome,q_investincome,q_dtprofit,q_eps,q_netprofit_margin,q_gsprofit_margin,q_exp_to_sales,q_profit_to_gr,q_saleexp_to_gr,q_adminexp_to_gr,q_finaexp_to_gr,q_impair_to_gr_ttm,q_gc_to_gr,q_op_to_gr,q_roe,q_dt_roe,q_npta,q_ocf_to_sales,q_ocf_to_or,basic_eps_yoy,dt_eps_yoy,cfps_yoy,op_yoy,ebt_yoy,netprofit_yoy,dt_netprofit_yoy,ocf_yoy,roe_yoy,bps_yoy,assets_yoy,eqt_yoy,tr_yoy,or_yoy,q_gr_yoy,q_gr_qoq,q_sales_yoy,q_sales_qoq,q_op_yoy,q_op_qoq,q_profit_yoy,q_profit_qoq,q_netprofit_yoy,q_netprofit_qoq,equity_yoy,rd_exp,update_flag'
                )
            )

            if result is None or len(result) == 0:
                logger.warning(f"股票{ts_code}财务指标数据为空")
                return pd.DataFrame()

            logger.info(f"成功获取股票{ts_code}的{len(result)}条财务指标数据")
            return result

        except Exception as e:
            logger.error(f"获取股票{ts_code}财务指标数据失败: {e}")
            raise DataSourceError(f"获取股票{ts_code}财务指标数据失败: {e}") from e

    async def get_daily_basic(self, ts_code: str = None, trade_date: str = None, 
                             start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        获取股票每日基本面数据（市值、换手率等）
        
        Args:
            ts_code: 股票代码（如：000001.SZ）
            trade_date: 交易日期（YYYYMMDD格式）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            包含每日基本面数据的字典列表
            
        Raises:
            DataSourceError: 当数据获取失败时抛出
        """
        try:
            if self._api is None:
                raise DataSourceError("API未初始化")
            api = self._api  # 类型断言
            
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            result = await self._execute_with_retry(
                lambda: api.daily_basic(**params)
            )
            
            if result is None or len(result) == 0:
                logger.warning("未获取到每日基本面数据")
                return []
                
            # 转换为字典列表格式
            data_list = result.to_dict('records')
            logger.info(f"成功获取{len(data_list)}条每日基本面数据")
            return data_list
                
        except Exception as e:
            logger.error(f"获取每日基本面数据失败: {e}")
            raise DataSourceError(f"获取每日基本面数据失败: {e}") from e

    async def get_stock_basic(self, ts_code: str = None, name: str = None, 
                             exchange: str = None, market: str = None, 
                             is_hs: str = None, list_status: str = 'L') -> List[Dict[str, Any]]:
        """
        获取股票基本信息
        
        Args:
            ts_code: 股票代码
            name: 股票名称
            exchange: 交易所代码
            market: 市场类别
            is_hs: 是否沪深港通标的
            list_status: 上市状态（L上市 D退市 P暂停上市）
            
        Returns:
            包含股票基本信息的字典列表
            
        Raises:
            DataSourceError: 当数据获取失败时抛出
        """
        try:
            params = {'list_status': list_status}
            if ts_code:
                params['ts_code'] = ts_code
            if name:
                params['name'] = name
            if exchange:
                params['exchange'] = exchange
            if market:
                params['market'] = market
            if is_hs:
                params['is_hs'] = is_hs
                
            result = await self._call_api('stock_basic', **params)
            
            if result and 'data' in result:
                # 转换为字典列表格式
                columns = result['data']['fields']
                rows = result['data']['items']
                
                data_list = []
                for row in rows:
                    data_dict = dict(zip(columns, row))
                    data_list.append(data_dict)
                    
                logger.info(f"成功获取{len(data_list)}条股票基本信息")
                return data_list
            else:
                logger.warning("未获取到股票基本信息")
                return []
                
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {e}")
            raise DataSourceError(f"获取股票基本信息失败: {e}") from e


# 全局Tushare客户端实例
tushare_client = TushareClient()
