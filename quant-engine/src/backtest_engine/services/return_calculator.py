"""收益计算器模块

本模块实现回测引擎的收益计算功能，包括：
- 投资组合收益计算
- 交易成本计算
- 绩效指标计算
- 风险控制应用
"""

import logging
from datetime import datetime
from decimal import Decimal

import numpy as np
from pydantic import BaseModel, Field

from ..models.backtest_models import TradingSignal

logger = logging.getLogger(__name__)


class PortfolioPosition(BaseModel):
    """投资组合持仓信息"""
    stock_code: str = Field(..., description="股票代码")
    shares: int = Field(default=0, description="持股数量")
    avg_cost: Decimal = Field(default=Decimal('0'), description="平均成本")
    market_value: Decimal = Field(default=Decimal('0'), description="市值")
    unrealized_pnl: Decimal = Field(default=Decimal('0'), description="浮动盈亏")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class TransactionCost(BaseModel):
    """交易成本信息"""
    commission: Decimal = Field(default=Decimal('0'), description="佣金")
    stamp_tax: Decimal = Field(default=Decimal('0'), description="印花税")
    transfer_fee: Decimal = Field(default=Decimal('0'), description="过户费")
    slippage: Decimal = Field(default=Decimal('0'), description="滑点成本")
    total_cost: Decimal = Field(default=Decimal('0'), description="总成本")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(default=0.0, description="总收益率")
    annual_return: float = Field(default=0.0, description="年化收益率")
    max_drawdown: float = Field(default=0.0, description="最大回撤")
    sharpe_ratio: float | None = Field(None, description="夏普比率")
    sortino_ratio: float | None = Field(None, description="索提诺比率")
    win_rate: float = Field(default=0.0, description="胜率")
    avg_win: float = Field(default=0.0, description="平均盈利")
    avg_loss: float = Field(default=0.0, description="平均亏损")
    profit_loss_ratio: float = Field(default=0.0, description="盈亏比")
    trade_count: int = Field(default=0, description="交易次数")
    volatility: float = Field(default=0.0, description="波动率")
    var_95: float | None = Field(None, description="95% VaR")


class ReturnCalculator:
    """收益计算器

    负责计算投资组合的收益表现，包括：
    - 投资组合收益计算
    - 交易成本计算
    - 绩效指标计算
    - 风险控制应用
    """

    def __init__(self, initial_capital: Decimal = Decimal('1000000')):
        """初始化收益计算器

        Args:
            initial_capital: 初始资金，默认100万
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: dict[str, PortfolioPosition] = {}
        self.daily_returns: list[Decimal] = []
        self.daily_values: list[Decimal] = [initial_capital]
        self.trade_records: list[dict] = []

        # 交易成本配置
        self.commission_rate = Decimal('0.0003')  # 佣金费率 0.03%
        self.stamp_tax_rate = Decimal('0.001')    # 印花税 0.1% (仅卖出)
        self.transfer_fee_rate = Decimal('0.00002')  # 过户费 0.002%
        self.slippage_rate = Decimal('0.001')     # 滑点 0.1%

        # 风险控制参数
        self.max_position_ratio = Decimal('0.1')  # 单股票最大仓位比例 10%
        self.stop_loss_ratio = Decimal('0.05')    # 止损比例 5%

        logger.info(f"收益计算器初始化完成，初始资金: {initial_capital}")

    def calculate_portfolio_returns(
        self,
        signal: TradingSignal,
        current_price: Decimal,
        timestamp: datetime
    ) -> tuple[Decimal, PerformanceMetrics]:
        """计算投资组合收益

        Args:
            signal: 交易信号
            current_price: 当前价格
            timestamp: 时间戳

        Returns:
            Tuple[当期收益, 绩效指标]
        """
        try:
            # 1. 执行交易
            self._execute_trade(signal, current_price, timestamp)

            # 2. 更新持仓
            self._update_positions(signal.stock_code, current_price)

            # 3. 计算当期收益
            current_return = self._calculate_current_return()

            # 4. 更新收益序列
            self.daily_returns.append(current_return)
            self.daily_values.append(self.current_capital)

            # 5. 计算绩效指标
            metrics = self._calculate_performance_metrics()

            logger.debug(f"投资组合收益计算完成: {signal.stock_code}, 当期收益: {current_return}")
            return current_return, metrics

        except Exception as e:
            logger.error(f"计算投资组合收益失败: {e}")
            raise

    def calculate_transaction_costs(
        self,
        signal: TradingSignal,
        price: Decimal,
        shares: int
    ) -> TransactionCost:
        """计算交易成本

        Args:
            signal: 交易信号
            price: 交易价格
            shares: 交易股数

        Returns:
            交易成本对象
        """
        try:
            trade_amount = price * Decimal(str(shares))

            # 佣金（买卖都收取）
            commission = trade_amount * self.commission_rate
            commission = max(commission, Decimal('5'))  # 最低5元

            # 印花税（仅卖出收取）
            stamp_tax = Decimal('0')
            if signal.signal_type == 'SELL':
                stamp_tax = trade_amount * self.stamp_tax_rate

            # 过户费（买卖都收取）
            transfer_fee = trade_amount * self.transfer_fee_rate
            transfer_fee = max(transfer_fee, Decimal('1'))  # 最低1元

            # 滑点成本
            slippage = trade_amount * self.slippage_rate

            # 总成本
            total_cost = commission + stamp_tax + transfer_fee + slippage

            cost = TransactionCost(
                commission=commission,
                stamp_tax=stamp_tax,
                transfer_fee=transfer_fee,
                slippage=slippage,
                total_cost=total_cost
            )

            logger.debug(f"交易成本计算完成: {signal.stock_code}, 总成本: {total_cost}")
            return cost

        except Exception as e:
            logger.error(f"计算交易成本失败: {e}")
            raise

    def apply_risk_controls(
        self,
        signal: TradingSignal,
        current_price: Decimal
    ) -> TradingSignal:
        """应用风险控制

        Args:
            signal: 原始交易信号
            current_price: 当前价格

        Returns:
            风险控制后的交易信号
        """
        try:
            # 复制信号对象
            controlled_signal = signal.model_copy()

            # 1. 仓位控制
            controlled_signal = self._apply_position_control(controlled_signal, current_price)

            # 2. 止损控制
            controlled_signal = self._apply_stop_loss_control(controlled_signal, current_price)

            # 3. 资金充足性检查
            controlled_signal = self._check_capital_sufficiency(controlled_signal, current_price)

            logger.debug(f"风险控制应用完成: {signal.stock_code}")
            return controlled_signal

        except Exception as e:
            logger.error(f"应用风险控制失败: {e}")
            raise

    def _execute_trade(
        self,
        signal: TradingSignal,
        price: Decimal,
        timestamp: datetime
    ) -> TransactionCost:
        """执行交易"""
        if signal.signal_type == 'HOLD':
            return TransactionCost()

        # 计算交易股数
        shares = self._calculate_trade_shares(signal, price)
        if shares == 0:
            return TransactionCost()

        # 计算交易成本
        cost = self.calculate_transaction_costs(signal, price, shares)

        # 更新资金
        if signal.signal_type == 'BUY':
            trade_amount = price * Decimal(str(shares)) + cost.total_cost
            self.current_capital -= trade_amount
        else:  # SELL
            trade_amount = price * Decimal(str(shares)) - cost.total_cost
            self.current_capital += trade_amount

        # 记录交易
        self.trade_records.append({
            'timestamp': timestamp,
            'stock_code': signal.stock_code,
            'signal_type': signal.signal_type,
            'price': price,
            'shares': shares,
            'cost': cost.total_cost
        })

        return cost

    def _calculate_trade_shares(self, signal: TradingSignal, price: Decimal) -> int:
        """计算交易股数"""
        if signal.signal_type == 'BUY':
            # 买入：根据仓位大小计算
            target_amount = self.current_capital * Decimal(str(signal.position_size))
            shares = int(float(target_amount / price) / 100.0) * 100  # 按手数取整
            return shares
        elif signal.signal_type == 'SELL':
            # 卖出：卖出全部持仓
            position = self.positions.get(signal.stock_code)
            return position.shares if position else 0
        else:
            return 0

    def _update_positions(self, stock_code: str, current_price: Decimal) -> None:
        """更新持仓信息"""
        if stock_code not in self.positions:
            self.positions[stock_code] = PortfolioPosition(stock_code=stock_code)

        position = self.positions[stock_code]

        # 更新市值和浮动盈亏
        if position.shares > 0:
            position.market_value = Decimal(str(position.shares)) * current_price
            position.unrealized_pnl = position.market_value - (Decimal(str(position.shares)) * position.avg_cost)

    def _calculate_current_return(self) -> Decimal:
        """计算当期收益率"""
        if len(self.daily_values) < 2:
            return Decimal('0')

        previous_value = self.daily_values[-2]
        current_value = self.daily_values[-1]

        if previous_value == 0:
            return Decimal('0')

        return (current_value - previous_value) / previous_value

    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """计算绩效指标"""
        if not self.daily_returns:
            return PerformanceMetrics(
                sharpe_ratio=None,
                sortino_ratio=None,
                var_95=None
            )

        returns_array = np.array([float(r) for r in self.daily_returns])

        # 总收益率
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital

        # 年化收益率
        trading_days = len(self.daily_returns)
        annual_return = Decimal('0')
        if trading_days > 0:
            annual_return = total_return * Decimal('252') / Decimal(str(trading_days))

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()

        # 波动率
        volatility = float(np.std(returns_array) * np.sqrt(252)) if len(returns_array) > 1 else 0.0

        # 夏普比率
        sharpe_ratio = None
        if volatility > 0:
            risk_free_rate = 0.03  # 假设无风险利率3%
            sharpe_ratio = (float(annual_return) - risk_free_rate) / volatility

        # 索提诺比率
        sortino_ratio = self._calculate_sortino_ratio(returns_array, annual_return)

        # 交易统计
        win_rate, avg_win, avg_loss, profit_loss_ratio = self._calculate_trade_stats()

        # VaR
        var_95 = self._calculate_var(returns_array, 0.95) if len(returns_array) > 0 else None

        return PerformanceMetrics(
            total_return=float(total_return),
            annual_return=float(annual_return),
            max_drawdown=float(max_drawdown),
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=float(sortino_ratio) if sortino_ratio is not None else None,
            win_rate=float(win_rate),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            profit_loss_ratio=float(profit_loss_ratio),
            trade_count=len(self.trade_records),
            volatility=volatility,
            var_95=float(var_95) if var_95 is not None else None
        )

    def _calculate_max_drawdown(self) -> Decimal:
        """计算最大回撤"""
        if len(self.daily_values) < 2:
            return Decimal('0')

        values = [float(v) for v in self.daily_values]
        peak = values[0]
        max_dd = 0.0

        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)

        return Decimal(str(max_dd))

    def _calculate_sortino_ratio(
        self,
        returns_array: np.ndarray,
        annual_return: Decimal
    ) -> Decimal | None:
        """计算索提诺比率"""
        if len(returns_array) == 0:
            return None

        negative_returns = returns_array[returns_array < 0]
        if len(negative_returns) == 0:
            return None

        downside_deviation = np.std(negative_returns) * np.sqrt(252)
        if downside_deviation == 0:
            return None

        risk_free_rate = 0.03
        return Decimal(str((float(annual_return) - risk_free_rate) / downside_deviation))

    def _calculate_trade_stats(self) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """计算交易统计"""
        if not self.trade_records:
            return Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')

        # 简化实现：基于交易记录计算
        # 实际应该基于每笔交易的盈亏计算
        win_trades = 0
        total_trades = len(self.trade_records)

        # 这里简化处理，实际需要跟踪每笔交易的盈亏
        win_rate = Decimal(str(float(win_trades) / float(total_trades))) if total_trades > 0 else Decimal('0')

        return win_rate, Decimal('0'), Decimal('0'), Decimal('0')

    def _calculate_var(self, returns_array: np.ndarray, confidence: float) -> Decimal:
        """计算VaR"""
        if len(returns_array) == 0:
            return Decimal('0')

        var_value = np.percentile(returns_array, (1 - confidence) * 100)
        return Decimal(str(abs(var_value)))

    def _apply_position_control(
        self,
        signal: TradingSignal,
        current_price: Decimal
    ) -> TradingSignal:
        """应用仓位控制"""
        if signal.signal_type != 'BUY':
            return signal

        # 限制单股票最大仓位
        max_position_value = self.current_capital * self.max_position_ratio
        max_position_size = float(max_position_value / self.current_capital)

        if signal.position_size > max_position_size:
            signal.position_size = max_position_size
            logger.info(f"仓位控制: {signal.stock_code} 仓位调整为 {max_position_size}")

        return signal

    def _apply_stop_loss_control(
        self,
        signal: TradingSignal,
        current_price: Decimal
    ) -> TradingSignal:
        """应用止损控制"""
        position = self.positions.get(signal.stock_code)
        if not position or position.shares <= 0:
            return signal

        # 计算止损价格
        stop_loss_price = position.avg_cost * (Decimal('1') - self.stop_loss_ratio)

        # 如果当前价格低于止损价格，强制卖出
        if current_price <= stop_loss_price and signal.signal_type != 'SELL':
            signal.signal_type = 'SELL'
            signal.position_size = 1.0  # 全部卖出
            logger.warning(f"止损触发: {signal.stock_code} 当前价格 {current_price} <= 止损价格 {stop_loss_price}")

        return signal

    def _check_capital_sufficiency(
        self,
        signal: TradingSignal,
        current_price: Decimal
    ) -> TradingSignal:
        """检查资金充足性"""
        if signal.signal_type != 'BUY':
            return signal

        # 计算所需资金
        required_amount = self.current_capital * Decimal(str(signal.position_size))
        estimated_cost = required_amount * (Decimal('1') + self.commission_rate + self.slippage_rate)

        # 如果资金不足，调整仓位大小
        if estimated_cost > self.current_capital:
            denominator = self.current_capital * (Decimal('1') + self.commission_rate + self.slippage_rate)
            max_affordable_size = self.current_capital / denominator
            signal.position_size = max(0.0, float(max_affordable_size))
            logger.warning(f"资金不足: {signal.stock_code} 仓位调整为 {signal.position_size}")

        return signal

    def reset(self) -> None:
        """重置计算器状态"""
        self.current_capital = self.initial_capital
        self.positions.clear()
        self.daily_returns.clear()
        self.daily_values = [self.initial_capital]
        self.trade_records.clear()
        logger.info("收益计算器状态已重置")
