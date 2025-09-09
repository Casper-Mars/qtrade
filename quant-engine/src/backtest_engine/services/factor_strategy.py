"""基于因子的Backtrader策略模块

本模块实现基于因子组合的交易策略：
- 因子信号计算和组合
- 买卖信号生成
- 仓位管理和风险控制
- 交易执行逻辑
"""

from loguru import logger

import backtrader as bt  # type: ignore

from ..models.backtest_models import BacktestFactorConfig, BacktestMode


class FactorStrategy(bt.Strategy):
    """基于因子组合的交易策略

    根据因子组合计算综合信号，执行买卖决策
    """

    # 策略参数
    params = (
        ('factor_combination', None),  # 因子组合配置
        ('buy_threshold', 0.6),        # 买入阈值
        ('sell_threshold', 0.4),       # 卖出阈值
        ('backtest_mode', BacktestMode.HISTORICAL_SIMULATION),  # 回测模式
        ('position_size', 0.95),       # 仓位大小（资金使用比例）
        ('stop_loss', None),           # 止损比例
        ('take_profit', None),         # 止盈比例
    )

    def __init__(self) -> None:
        """初始化策略"""
        super().__init__()

        # 验证参数
        if not self.p.factor_combination:
            raise ValueError("因子组合配置不能为空")

        self.factor_combination: BacktestFactorConfig = self.p.factor_combination

        # 策略状态
        self.current_position = 0  # 当前仓位
        self.last_signal = 0.0     # 上一次信号值
        self.trade_count = 0       # 交易次数

        # 因子权重映射
        self.factor_weights = {
            factor.factor_name: factor.weight
            for factor in self.factor_combination.factors
        }


        logger.info(f"因子策略初始化完成，因子数量: {len(self.factor_weights)}")
        logger.info(f"买入阈值: {self.p.buy_threshold}, 卖出阈值: {self.p.sell_threshold}")

    def next(self) -> None:
        """策略主逻辑，每个数据点调用一次"""
        try:
            # 1. 计算综合因子信号
            composite_signal = self._calculate_composite_signal()

            # 2. 生成交易信号
            trade_signal = self._generate_trade_signal(composite_signal)

            # 3. 执行交易决策
            self._execute_trade_decision(trade_signal, composite_signal)

            # 4. 更新状态
            self.last_signal = composite_signal

        except Exception as e:
            logger.error(f"策略执行错误: {e}")

    def _calculate_composite_signal(self) -> float:
        """计算综合因子信号

        Returns:
            综合信号值 (0-1之间)
        """
        if not hasattr(self.data, 'factor_data') or self.data.factor_data[0] is None:
            logger.warning("因子数据不可用，返回中性信号")
            return 0.5

        # 获取当前因子数据
        current_factors = self.data.factor_data[0]

        # 计算加权综合信号
        composite_signal = 0.0
        total_weight = 0.0

        for factor_name, weight in self.factor_weights.items():
            if factor_name in current_factors:
                factor_value = current_factors[factor_name]

                # 标准化因子值到0-1区间
                normalized_value = self._normalize_factor_value(factor_value, factor_name)

                # 加权累加
                composite_signal += normalized_value * weight
                total_weight += weight

        # 归一化
        if total_weight > 0:
            composite_signal /= total_weight
        else:
            composite_signal = 0.5  # 默认中性信号

        # 确保信号在0-1范围内
        composite_signal = max(0.0, min(1.0, composite_signal))

        return composite_signal

    def _normalize_factor_value(self, value: float | None, factor_name: str) -> float:
        """标准化因子值到0-1区间

        Args:
            value: 原始因子值
            factor_name: 因子名称

        Returns:
            标准化后的值 (0-1之间)
        """
        # 简单的标准化方法，可以根据具体因子类型优化
        if value is None or not isinstance(value, int | float):
            normalized = 0.5
        else:
            # 使用sigmoid函数进行标准化
            import math
            try:
                normalized = 1 / (1 + math.exp(-value))
            except (OverflowError, ValueError):
                normalized = 0.5
        return normalized

    def _generate_trade_signal(self, composite_signal: float) -> str:
        """生成交易信号

        Args:
            composite_signal: 综合信号值

        Returns:
            交易信号: 'BUY', 'SELL', 'HOLD'
        """
        if composite_signal >= self.p.buy_threshold:
            return 'BUY'
        elif composite_signal <= self.p.sell_threshold:
            return 'SELL'
        else:
            return 'HOLD'

    def _execute_trade_decision(self, trade_signal: str, composite_signal: float) -> None:
        """执行交易决策

        Args:
            trade_signal: 交易信号
            composite_signal: 综合信号值
        """
        current_position = self.position.size

        if trade_signal == 'BUY' and current_position <= 0:
            # 买入信号且当前无多头仓位
            self._execute_buy_order(composite_signal)

        elif trade_signal == 'SELL' and current_position >= 0:
            # 卖出信号且当前无空头仓位
            self._execute_sell_order(composite_signal)

        # 检查止损止盈
        if current_position != 0:
            self._check_stop_conditions()

    def _execute_buy_order(self, signal_strength: float) -> None:
        """执行买入订单

        Args:
            signal_strength: 信号强度
        """
        # 计算订单大小
        cash = self.broker.getcash()
        price = self.data.close[0]

        # 根据信号强度调整仓位大小
        position_ratio = self.p.position_size * signal_strength
        order_value = cash * position_ratio
        size = int(order_value / price)

        if size > 0:
            self.buy(size=size)
            self.trade_count += 1
            logger.info(f"买入订单: 数量={size}, 价格={price:.2f}, 信号强度={signal_strength:.3f}")

    def _execute_sell_order(self, signal_strength: float) -> None:
        """执行卖出订单

        Args:
            signal_strength: 信号强度
        """
        current_position = self.position.size

        if current_position > 0:
            # 平多头仓位
            self.close()
            self.trade_count += 1
            logger.info(f"平仓订单: 数量={current_position}, 价格={self.data.close[0]:.2f}, 信号强度={signal_strength:.3f}")

        # 如果允许做空，可以在这里添加做空逻辑
        # 当前实现只支持多头策略

    def _check_stop_conditions(self) -> None:
        """检查止损止盈条件"""
        if not self.position:
            return

        current_price = self.data.close[0]
        entry_price = self.position.price

        # 计算收益率
        if self.position.size > 0:  # 多头仓位
            return_rate = (current_price - entry_price) / entry_price
        else:  # 空头仓位
            return_rate = (entry_price - current_price) / entry_price

        # 检查止损
        if self.p.stop_loss and return_rate <= -self.p.stop_loss:
            self.close()
            logger.info(f"止损平仓: 收益率={return_rate:.3f}, 止损线={-self.p.stop_loss:.3f}")
            return

        # 检查止盈
        if self.p.take_profit and return_rate >= self.p.take_profit:
            self.close()
            logger.info(f"止盈平仓: 收益率={return_rate:.3f}, 止盈线={self.p.take_profit:.3f}")
            return

    def notify_order(self, order: bt.Order) -> None:
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                logger.debug(f"买入执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}")
            else:
                logger.debug(f"卖出执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning(f"订单失败: 状态={order.status}")

    def notify_trade(self, trade: bt.Trade) -> None:
        """交易完成通知"""
        if not trade.isclosed:
            return

        logger.info(f"交易完成: 盈亏={trade.pnl:.2f}, 净盈亏={trade.pnlcomm:.2f}")

    def get_strategy_stats(self) -> dict:
        """获取策略统计信息

        Returns:
            策略统计字典
        """
        return {
            'trade_count': self.trade_count,
            'current_position': self.position.size if self.position else 0,
            'last_signal': self.last_signal,
            'factor_count': len(self.factor_weights),
            'buy_threshold': self.p.buy_threshold,
            'sell_threshold': self.p.sell_threshold
        }
