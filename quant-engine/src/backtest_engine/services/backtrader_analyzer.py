"""Backtrader分析器模块

本模块实现回测结果分析和绩效指标计算：
- 集成Backtrader内置分析器
- 自定义绩效指标计算
- 结果格式化和输出
- 风险指标分析
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import backtrader as bt  # type: ignore
import numpy as np

from ..models.backtest_models import (
    BacktestConfig,
    BacktestFactorConfig,
    BacktestMode,
    BacktestResult,
)

logger = logging.getLogger(__name__)


class BacktraderAnalyzer:
    """Backtrader分析器

    负责配置分析器、提取结果和计算绩效指标
    """

    def __init__(self) -> None:
        """初始化分析器"""
        self.analyzers: dict[str, Any] = {}
        self.custom_data: dict[str, Any] = {}

        logger.info("Backtrader分析器初始化完成")

    def add_analyzers(self, cerebro: bt.Cerebro) -> None:
        """添加分析器到Cerebro

        Args:
            cerebro: Backtrader引擎实例
        """
        try:
            # 1. 基础分析器
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

            # 2. 收益分析器
            cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')

            # 3. 风险分析器
            cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')  # Variability-Weighted Return
            cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')  # System Quality Number

            # 4. 交易分析器
            cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
            cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='positions')

            # 5. 自定义分析器
            cerebro.addanalyzer(CalmarRatioAnalyzer, _name='calmar')
            cerebro.addanalyzer(PortfolioValueAnalyzer, _name='portfolio_value')

            logger.info("分析器添加完成")

        except Exception as e:
            logger.error(f"添加分析器失败: {e}")
            raise

    def extract_results(
        self,
        strategy_results: list[bt.Strategy],
        config: BacktestConfig | None = None
    ) -> BacktestResult:
        """提取回测结果

        Args:
            strategy_results: 策略执行结果列表
            config: 回测配置（可选）

        Returns:
            格式化的回测结果
        """
        try:
            if not strategy_results:
                raise ValueError("策略结果为空")

            # 获取第一个策略的分析器结果
            strategy = strategy_results[0]
            analyzers = strategy.analyzers

            # 提取各类指标
            performance_metrics = self._extract_performance_metrics(analyzers)
            risk_metrics = self._extract_risk_metrics(analyzers)
            trade_stats = self._extract_trade_statistics(analyzers)
            backtrader_metrics = self._extract_backtrader_metrics(analyzers)
            portfolio_data = self._extract_portfolio_data(analyzers)

            # 创建默认因子配置
            from ..models.backtest_models import FactorItem
            default_factor = FactorItem(
                factor_name="default",
                factor_type="technical",
                weight=1.0
            )
            default_factor_combination = BacktestFactorConfig(
                combination_id="default",
                factors=[default_factor],
                description="默认因子组合"
            )

            # 构建回测结果
            result = BacktestResult(
                # 基础信息
                config_id=config.id if config else UUID('00000000-0000-0000-0000-000000000000'),
                factor_combination=config.factor_combination if config else default_factor_combination,
                start_date=config.start_date if config else "2023-01-01",
                end_date=config.end_date if config else "2023-12-31",
                stock_code=config.stock_code if config else "000001.SZ",
                backtest_mode=config.backtest_mode if config else BacktestMode.HISTORICAL_SIMULATION,

                # 核心绩效指标
                total_return=performance_metrics.get('total_return', 0.0),
                annual_return=performance_metrics.get('annual_return', 0.0),
                sharpe_ratio=performance_metrics.get('sharpe_ratio', 0.0),
                max_drawdown=risk_metrics.get('max_drawdown', 0.0),
                volatility=risk_metrics.get('volatility', 0.0),

                # 交易统计
                trade_count=trade_stats.get('trade_count', 0),
                win_rate=trade_stats.get('win_rate', 0.0),
                avg_profit=trade_stats.get('avg_profit', 0.0),
                avg_loss=trade_stats.get('avg_loss', 0.0),
                profit_loss_ratio=trade_stats.get('profit_loss_ratio', 0.0),

                # 风险指标
                beta=risk_metrics.get('beta', 0.0),
                var_95=risk_metrics.get('var_95', 0.0),
                sortino_ratio=risk_metrics.get('sortino_ratio', 0.0),

                # Backtrader特有指标
                calmar_ratio=backtrader_metrics.get('calmar_ratio', 0.0),
                largest_win=backtrader_metrics.get('largest_win', 0.0),
                largest_loss=backtrader_metrics.get('largest_loss', 0.0),
                sqn=backtrader_metrics.get('sqn', 0.0),
                gross_leverage=backtrader_metrics.get('gross_leverage', 0.0),

                # 资金曲线数据
                portfolio_value=portfolio_data.get('portfolio_value', []),
                benchmark_value=portfolio_data.get('benchmark_value', []),
                dates=portfolio_data.get('dates', []),

                # 执行信息
                execution_time=0.0,
                data_points=0,
                completed_at=datetime.now()
            )

            logger.info("回测结果提取完成")
            return result

        except Exception as e:
            logger.error(f"提取回测结果失败: {e}")
            raise

    def _extract_performance_metrics(self, analyzers: Any) -> dict[str, float]:
        """提取绩效指标

        Args:
            analyzers: 分析器结果

        Returns:
            绩效指标字典
        """
        metrics = {}

        try:
            # 总收益率
            if hasattr(analyzers, 'returns'):
                returns_analysis = analyzers.returns.get_analysis()
                metrics['total_return'] = returns_analysis.get('rtot', 0.0)

            # 年化收益率
            if hasattr(analyzers, 'annual_return'):
                annual_analysis = analyzers.annual_return.get_analysis()
                if annual_analysis:
                    # 取最后一年的收益率作为年化收益率
                    last_year = max(annual_analysis.keys()) if annual_analysis else None
                    metrics['annual_return'] = annual_analysis.get(last_year, 0.0) if last_year else 0.0

            # 夏普比率
            if hasattr(analyzers, 'sharpe'):
                sharpe_analysis = analyzers.sharpe.get_analysis()
                metrics['sharpe_ratio'] = sharpe_analysis.get('sharperatio', 0.0) or 0.0

            logger.debug(f"绩效指标提取完成: {metrics}")

        except Exception as e:
            logger.error(f"提取绩效指标失败: {e}")

        return metrics

    def _extract_risk_metrics(self, analyzers: Any) -> dict[str, float]:
        """提取风险指标

        Args:
            analyzers: 分析器结果

        Returns:
            风险指标字典
        """
        metrics = {}

        try:
            # 最大回撤
            if hasattr(analyzers, 'drawdown'):
                dd_analysis = analyzers.drawdown.get_analysis()
                metrics['max_drawdown'] = abs(dd_analysis.get('max', {}).get('drawdown', 0.0))

            # 波动率（从收益率计算）
            if hasattr(analyzers, 'time_return'):
                time_return_analysis = analyzers.time_return.get_analysis()
                if time_return_analysis:
                    returns = list(time_return_analysis.values())
                    if returns:
                        metrics['volatility'] = float(np.std(returns) * np.sqrt(252))  # 年化波动率

            # VWR (Variability-Weighted Return)
            if hasattr(analyzers, 'vwr'):
                vwr_analysis = analyzers.vwr.get_analysis()
                metrics['vwr'] = vwr_analysis.get('vwr', 0.0)

            # 其他风险指标设置为默认值
            metrics.setdefault('beta', 1.0)
            metrics.setdefault('alpha', 0.0)
            metrics.setdefault('information_ratio', 0.0)
            metrics.setdefault('sortino_ratio', 0.0)

            logger.debug(f"风险指标提取完成: {metrics}")

        except Exception as e:
            logger.error(f"提取风险指标失败: {e}")

        return metrics

    def _extract_trade_statistics(self, analyzers: Any) -> dict[str, Any]:
        """提取交易统计

        Args:
            analyzers: 分析器结果

        Returns:
            交易统计字典
        """
        stats = {}

        try:
            if hasattr(analyzers, 'trades'):
                trade_analysis = analyzers.trades.get_analysis()

                # 交易次数
                stats['trade_count'] = trade_analysis.get('total', {}).get('total', 0)

                # 胜率（小数格式，0-1之间）
                won_trades = trade_analysis.get('won', {}).get('total', 0)
                total_trades = stats['trade_count']
                stats['win_rate'] = (won_trades / total_trades) if total_trades > 0 else 0.0

                # 平均盈利和亏损
                stats['avg_win'] = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0.0)
                stats['avg_loss'] = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0.0))

                # 盈亏比
                total_won = trade_analysis.get('won', {}).get('pnl', {}).get('total', 0.0)
                total_lost = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('total', 0.0))
                stats['profit_factor'] = (total_won / total_lost) if total_lost > 0 else 0.0

            logger.debug(f"交易统计提取完成: {stats}")

        except Exception as e:
            logger.error(f"提取交易统计失败: {e}")

        return stats

    def _extract_backtrader_metrics(self, analyzers: Any) -> dict[str, float]:
        """提取Backtrader指标

        Args:
            analyzers: 分析器结果

        Returns:
            Backtrader指标字典
        """
        metrics = {}

        try:
            # Calmar比率
            if hasattr(analyzers, 'calmar'):
                calmar_analysis = analyzers.calmar.get_analysis()
                metrics['calmar_ratio'] = calmar_analysis.get('calmar_ratio', 0.0)

            # SQN (System Quality Number)
            if hasattr(analyzers, 'sqn'):
                sqn_analysis = analyzers.sqn.get_analysis()
                metrics['sqn'] = sqn_analysis.get('sqn', 0.0)

            # 最大单笔盈利和亏损
            if hasattr(analyzers, 'trades'):
                trade_analysis = analyzers.trades.get_analysis()
                metrics['largest_win'] = trade_analysis.get('won', {}).get('pnl', {}).get('max', 0.0)
                metrics['largest_loss'] = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('max', 0.0))

            # 杠杆率（设置默认值）
            metrics['gross_leverage'] = 1.0

            logger.debug(f"Backtrader指标提取完成: {metrics}")

        except Exception as e:
            logger.error(f"提取Backtrader指标失败: {e}")

        return metrics

    def _extract_portfolio_data(self, analyzers: Any) -> dict[str, list[Any]]:
        """提取资金曲线数据

        Args:
            analyzers: 分析器结果

        Returns:
            资金曲线数据字典
        """
        data: dict[str, list[Any]] = {
            'portfolio_value': [],
            'benchmark_value': [],
            'dates': []
        }

        try:
            if hasattr(analyzers, 'portfolio_value'):
                portfolio_analysis = analyzers.portfolio_value.get_analysis()

                # 提取日期和资金曲线
                for date, value in portfolio_analysis.items():
                    data['dates'].append(date.strftime('%Y-%m-%d'))
                    data['portfolio_value'].append(float(value))
                    # 基准设置为初始值（简化处理）
                    data['benchmark_value'].append(100000.0)  # 假设初始资金10万

            logger.debug(f"资金曲线数据提取完成: {len(data['dates'])} 个数据点")

        except Exception as e:
            logger.error(f"提取资金曲线数据失败: {e}")

        return data


class CalmarRatioAnalyzer(bt.Analyzer):
    """Calmar比率分析器

    计算年化收益率与最大回撤的比值
    """

    def __init__(self) -> None:
        super().__init__()
        self.returns: list[float] = []
        self.peak: float = 0
        self.max_dd: float = 0

    def next(self) -> None:
        """每个交易日调用"""
        portfolio_value = self.strategy.broker.getvalue()

        # 记录收益率
        if len(self.returns) == 0:
            self.returns.append(0.0)
            self.peak = portfolio_value
        else:
            prev_value = self.peak if self.peak > 0 else portfolio_value
            daily_return = (portfolio_value - prev_value) / prev_value
            self.returns.append(daily_return)

            # 更新峰值和最大回撤
            if portfolio_value > self.peak:
                self.peak = portfolio_value

            drawdown = (self.peak - portfolio_value) / self.peak
            if drawdown > self.max_dd:
                self.max_dd = drawdown

    def get_analysis(self) -> dict[str, float]:
        """返回分析结果"""
        if not self.returns or self.max_dd == 0:
            return {'calmar_ratio': 0.0}

        # 计算年化收益率
        total_return = sum(self.returns)
        trading_days = len(self.returns)
        annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0

        # 计算Calmar比率
        calmar_ratio = annual_return / self.max_dd if self.max_dd > 0 else 0

        return {'calmar_ratio': calmar_ratio}


class PortfolioValueAnalyzer(bt.Analyzer):
    """资金曲线分析器

    记录每日的资金曲线变化
    """

    def __init__(self) -> None:
        super().__init__()
        self.portfolio_values: dict[Any, float] = {}

    def next(self) -> None:
        """每个交易日调用"""
        current_date = self.strategy.datetime.date()
        portfolio_value = self.strategy.broker.getvalue()
        self.portfolio_values[current_date] = portfolio_value

    def get_analysis(self) -> dict[Any, float]:
        """返回分析结果"""
        return self.portfolio_values
