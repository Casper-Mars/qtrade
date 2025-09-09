"""基于Backtrader的回测引擎核心模块

本模块实现基于Backtrader框架的回测引擎核心功能：
- Cerebro引擎封装和配置管理
- 因子策略集成和参数配置
- 数据源管理和回测执行
- 分析器集成和结果收集
"""

import logging
from datetime import datetime
from typing import Any

import backtrader as bt  # type: ignore
from pydantic import ValidationError

from ...clients.tushare_client import TushareClient
from ...factor_engine.services.factor_service import FactorService
from ...utils.exceptions import ValidationException
from ..models.backtest_models import (
    BacktestConfig,
    BacktestResult,
)
from .backtrader_analyzer import BacktraderAnalyzer
from .factor_data_feed import FactorDataFeed
from .factor_strategy import FactorStrategy

logger = logging.getLogger(__name__)


class BacktestEngine:
    """基于Backtrader的回测引擎核心类

    封装Backtrader的Cerebro引擎，提供统一的回测接口
    """

    def __init__(
        self,
        factor_service: FactorService,
        data_client: TushareClient,
    ):
        """初始化回测引擎

        Args:
            factor_service: 因子服务实例
            data_client: 数据客户端
        """
        self.factor_service = factor_service
        self.data_client = data_client

        # Cerebro引擎实例
        self.cerebro: bt.Cerebro = bt.Cerebro()

        # 运行时状态
        self._current_config: BacktestConfig | None = None
        self._results: list[BacktestResult] = []

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """执行完整回测流程

        Args:
            config: 回测配置

        Returns:
            回测结果

        Raises:
            ValidationException: 配置验证失败
            Exception: 回测执行失败
        """
        try:
            # 1. 验证回测配置
            self._validate_config(config)
            self._current_config = config

            logger.info(f"开始执行回测: {config.stock_code}, {config.start_date} - {config.end_date}")
            start_time = datetime.now()

            # 2. 初始化Cerebro引擎
            self._initialize_cerebro(config)

            # 3. 配置数据源
            self._setup_data_feeds(config)

            # 4. 配置策略
            self._setup_strategy(config)

            # 5. 配置分析器
            self._setup_analyzers(config)

            # 6. 执行回测
            logger.info("开始执行Backtrader回测")
            results = self.cerebro.run()

            # 7. 处理结果
            execution_time = (datetime.now() - start_time).total_seconds()
            backtest_result = self._process_results(results, config, execution_time)

            logger.info(f"回测完成: 总收益率={backtest_result.total_return:.2%}")
            return backtest_result

        except ValidationError as e:
            logger.error(f"配置验证失败: {e}")
            raise ValidationException(f"回测配置验证失败: {e}") from e
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            raise
        finally:
            self._current_config = None
            # 保持cerebro实例，不设为None

    def _validate_config(self, config: BacktestConfig) -> None:
        """验证回测配置

        Args:
            config: 回测配置

        Raises:
            ValidationException: 配置验证失败
        """
        # 验证日期范围
        start_date = datetime.strptime(config.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(config.end_date, "%Y-%m-%d")

        if start_date >= end_date:
            raise ValidationException("开始日期必须早于结束日期")

        # 验证因子组合
        if not config.factor_combination or not config.factor_combination.factors:
            raise ValidationException("因子组合不能为空")

        # 验证因子权重总和
        total_weight = sum(factor.weight for factor in config.factor_combination.factors)
        if abs(total_weight - 1.0) > 0.01:
            raise ValidationException(f"因子权重总和必须为1.0，当前为{total_weight:.3f}")

        # 验证初始资金
        if config.initial_capital <= 0:
            raise ValidationException("初始资金必须大于0")

        # 验证Backtrader特有参数
        if config.slippage < 0:
            raise ValidationException("滑点不能为负数")

        if not (0 <= config.buy_threshold <= 1):
            raise ValidationException("买入阈值必须在0-1之间")

        if not (0 <= config.sell_threshold <= 1):
            raise ValidationException("卖出阈值必须在0-1之间")

    def _initialize_cerebro(self, config: BacktestConfig) -> None:
        """初始化Cerebro引擎

        Args:
            config: 回测配置
        """
        # 重置Cerebro引擎
        self.cerebro = bt.Cerebro()

        # 设置初始资金
        self.cerebro.broker.setcash(config.initial_capital)

        # 设置佣金
        self.cerebro.broker.setcommission(commission=config.transaction_cost)

        # 设置滑点
        if config.slippage > 0:
            self.cerebro.broker.set_slippage_perc(config.slippage)

        # 设置订单大小
        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=95)  # 使用95%资金

        logger.info(f"Cerebro引擎初始化完成，初始资金: {config.initial_capital}")

    def _setup_data_feeds(self, config: BacktestConfig) -> None:
        """配置数据源

        Args:
            config: 回测配置
        """
        # 创建因子数据源
        data_feed = FactorDataFeed(
            factor_service=self.factor_service,
            data_client=self.data_client,
            stock_code=config.stock_code,
            start_date=config.start_date,
            end_date=config.end_date,
            factor_combination=config.factor_combination
        )

        # 添加数据源到Cerebro
        self.cerebro.adddata(data_feed)

        logger.info(f"数据源配置完成: {config.stock_code}")

    def _setup_strategy(self, config: BacktestConfig) -> None:
        """配置策略

        Args:
            config: 回测配置
        """
        # 添加因子策略
        self.cerebro.addstrategy(
            FactorStrategy,
            factor_combination=config.factor_combination,
            buy_threshold=config.buy_threshold,
            sell_threshold=config.sell_threshold,
            backtest_mode=config.backtest_mode
        )

        logger.info("策略配置完成")

    def _setup_analyzers(self, config: BacktestConfig) -> None:
        """配置分析器

        Args:
            config: 回测配置
        """
        # 添加内置分析器
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')

        # 添加自定义性能分析器
        self.cerebro.addanalyzer(BacktraderAnalyzer, _name='performance')

        logger.info("分析器配置完成")

    def _process_results(self, results: list[Any], config: BacktestConfig, execution_time: float) -> BacktestResult:
        """处理回测结果

        Args:
            results: Backtrader回测结果
            config: 回测配置
            execution_time: 执行时间

        Returns:
            格式化的回测结果
        """
        if not results:
            raise Exception("回测结果为空")

        # 获取第一个策略的结果
        strategy = results[0]

        # 提取分析器结果
        returns_analyzer = strategy.analyzers.returns.get_analysis()
        sharpe_analyzer = strategy.analyzers.sharpe.get_analysis()
        drawdown_analyzer = strategy.analyzers.drawdown.get_analysis()
        trades_analyzer = strategy.analyzers.trades.get_analysis()
        sqn_analyzer = strategy.analyzers.sqn.get_analysis()
        performance_analyzer = strategy.analyzers.performance.get_analysis()

        # 计算绩效指标
        total_return = returns_analyzer.get('rtot', 0.0)
        annual_return = returns_analyzer.get('rnorm', 0.0)
        max_drawdown = drawdown_analyzer.get('max', {}).get('drawdown', 0.0) / 100.0
        sharpe_ratio = sharpe_analyzer.get('sharperatio', 0.0) or 0.0

        # 交易统计
        trade_count = trades_analyzer.get('total', {}).get('total', 0)
        won_trades = trades_analyzer.get('won', {}).get('total', 0)
        win_rate = won_trades / trade_count if trade_count > 0 else 0.0

        # 构建回测结果
        result = BacktestResult(
            config_id=config.id,
            factor_combination=config.factor_combination,
            start_date=config.start_date,
            end_date=config.end_date,
            stock_code=config.stock_code,
            backtest_mode=config.backtest_mode,

            # 核心绩效指标
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=performance_analyzer.get('sortino_ratio'),
            calmar_ratio=performance_analyzer.get('calmar_ratio'),

            # 交易统计
            trade_count=trade_count,
            win_rate=win_rate,
            avg_profit=trades_analyzer.get('won', {}).get('pnl', {}).get('average', None),
            avg_loss=trades_analyzer.get('lost', {}).get('pnl', {}).get('average', None),
            profit_loss_ratio=performance_analyzer.get('profit_loss_ratio'),
            largest_win=trades_analyzer.get('won', {}).get('pnl', {}).get('max', None),
            largest_loss=trades_analyzer.get('lost', {}).get('pnl', {}).get('max', None),

            # 风险指标
            volatility=performance_analyzer.get('volatility', 0.0),
            var_95=performance_analyzer.get('var_95'),
            beta=performance_analyzer.get('beta'),

            # Backtrader特有指标
            sqn=sqn_analyzer.get('sqn'),
            gross_leverage=performance_analyzer.get('gross_leverage'),

            # 资金曲线数据
            portfolio_value=performance_analyzer.get('portfolio_values'),
            benchmark_value=performance_analyzer.get('benchmark_values'),
            dates=performance_analyzer.get('dates'),

            # 执行信息
            execution_time=execution_time,
            data_points=performance_analyzer.get('data_points', 0),
            completed_at=datetime.now()
        )

        return result

    def get_cerebro_info(self) -> dict[str, Any]:
        """获取Cerebro引擎信息

        Returns:
            引擎信息字典
        """
        if not self.cerebro:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "cash": self.cerebro.broker.getcash(),
            "value": self.cerebro.broker.getvalue(),
            "data_feeds": len(self.cerebro.datas),
            "strategies": len(self.cerebro.strats),
            "analyzers": len(self.cerebro.analyzers)
        }
