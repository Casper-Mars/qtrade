"""收益计算器测试模块

测试收益计算器的各项功能：
- 投资组合收益计算
- 交易成本计算
- 绩效指标计算
- 风险控制应用
"""

from datetime import datetime
from decimal import Decimal

from src.backtest_engine.models.backtest_models import TradingSignal
from src.backtest_engine.services.return_calculator import (
    PerformanceMetrics,
    PortfolioPosition,
    ReturnCalculator,
    TransactionCost,
)


class TestReturnCalculator:
    """收益计算器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.calculator = ReturnCalculator(initial_capital=Decimal('1000000'))
        self.test_signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.1'),
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )

    def test_init(self):
        """测试初始化"""
        assert self.calculator.initial_capital == Decimal('1000000')
        assert self.calculator.current_capital == Decimal('1000000')
        assert len(self.calculator.positions) == 0
        assert len(self.calculator.daily_returns) == 0
        assert len(self.calculator.daily_values) == 1
        assert self.calculator.daily_values[0] == Decimal('1000000')

    def test_calculate_transaction_costs_buy(self):
        """测试买入交易成本计算"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.1'),
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        price = Decimal('10.00')
        shares = 1000

        cost = self.calculator.calculate_transaction_costs(signal, price, shares)

        assert isinstance(cost, TransactionCost)
        assert cost.commission >= Decimal('5')  # 最低佣金5元
        assert cost.stamp_tax == Decimal('0')   # 买入无印花税
        assert cost.transfer_fee >= Decimal('1')  # 最低过户费1元
        assert cost.slippage > Decimal('0')
        assert cost.total_cost > Decimal('0')

    def test_calculate_transaction_costs_sell(self):
        """测试卖出交易成本计算"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="SELL",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('1.0'),
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        price = Decimal('10.00')
        shares = 1000

        cost = self.calculator.calculate_transaction_costs(signal, price, shares)

        assert isinstance(cost, TransactionCost)
        assert cost.commission >= Decimal('5')
        assert cost.stamp_tax > Decimal('0')  # 卖出有印花税
        assert cost.transfer_fee >= Decimal('1')
        assert cost.slippage > Decimal('0')
        assert cost.total_cost > Decimal('0')

    def test_calculate_portfolio_returns(self):
        """测试投资组合收益计算"""
        current_price = Decimal('10.00')
        timestamp = datetime.now()

        current_return, metrics = self.calculator.calculate_portfolio_returns(
            self.test_signal, current_price, timestamp
        )

        assert isinstance(current_return, Decimal)
        assert isinstance(metrics, PerformanceMetrics)
        assert len(self.calculator.daily_returns) == 1
        assert len(self.calculator.daily_values) == 2

    def test_apply_risk_controls_position_limit(self):
        """测试仓位控制"""
        # 创建超过最大仓位的信号
        signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.2'),  # 20%，超过10%限制
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        current_price = Decimal('10.00')

        controlled_signal = self.calculator.apply_risk_controls(signal, current_price)

        assert controlled_signal.position_size <= self.calculator.max_position_ratio

    def test_apply_risk_controls_capital_sufficiency(self):
        """测试资金充足性检查"""
        # 设置较小的资金
        self.calculator.current_capital = Decimal('1000')

        signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.5'),  # 50%仓位
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        current_price = Decimal('1000.00')  # 高价格

        controlled_signal = self.calculator.apply_risk_controls(signal, current_price)

        # 仓位应该被调整
        assert controlled_signal.position_size <= signal.position_size

    def test_calculate_performance_metrics_empty(self):
        """测试空数据的绩效指标计算"""
        metrics = self.calculator._calculate_performance_metrics()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_return == Decimal('0')
        assert metrics.annual_return == Decimal('0')
        assert metrics.max_drawdown == Decimal('0')
        assert metrics.trade_count == 0

    def test_calculate_max_drawdown(self):
        """测试最大回撤计算"""
        # 模拟一些净值数据
        self.calculator.daily_values = [
            Decimal('1000000'),
            Decimal('1100000'),  # +10%
            Decimal('1050000'),  # -4.5%
            Decimal('900000'),   # -14.3%
            Decimal('950000'),   # +5.6%
        ]

        max_drawdown = self.calculator._calculate_max_drawdown()

        assert max_drawdown > Decimal('0')
        assert max_drawdown <= Decimal('1')  # 回撤不应超过100%

    def test_update_positions(self):
        """测试持仓更新"""
        stock_code = "000001"
        current_price = Decimal('10.00')

        # 初始化持仓
        self.calculator.positions[stock_code] = PortfolioPosition(
            stock_code=stock_code,
            shares=1000,
            avg_cost=Decimal('9.00')
        )

        self.calculator._update_positions(stock_code, current_price)

        position = self.calculator.positions[stock_code]
        assert position.market_value == Decimal('10000')  # 1000 * 10.00
        assert position.unrealized_pnl == Decimal('1000')  # (10.00 - 9.00) * 1000

    def test_calculate_trade_shares_buy(self):
        """测试买入股数计算"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.1'),  # 10%仓位
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        price = Decimal('10.00')

        shares = self.calculator._calculate_trade_shares(signal, price)

        assert shares >= 0
        assert shares % 100 == 0  # 应该是100的整数倍（手数）

    def test_calculate_trade_shares_sell(self):
        """测试卖出股数计算"""
        stock_code = "000001"

        # 设置持仓
        self.calculator.positions[stock_code] = PortfolioPosition(
            stock_code=stock_code,
            shares=1000
        )

        signal = TradingSignal(
            stock_code=stock_code,
            signal_type="SELL",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('1.0'),
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        price = Decimal('10.00')

        shares = self.calculator._calculate_trade_shares(signal, price)

        assert shares == 1000  # 应该卖出全部持仓

    def test_calculate_trade_shares_hold(self):
        """测试持有信号的股数计算"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="HOLD",
            signal_strength=Decimal('0.5'),
            position_size=Decimal('0.0'),
            timestamp=datetime.now(),
            confidence=Decimal('0.5')
        )
        price = Decimal('10.00')

        shares = self.calculator._calculate_trade_shares(signal, price)

        assert shares == 0

    def test_reset(self):
        """测试重置功能"""
        # 先进行一些操作
        self.calculator.current_capital = Decimal('900000')
        self.calculator.positions["000001"] = PortfolioPosition(stock_code="000001")
        self.calculator.daily_returns.append(Decimal('0.1'))
        self.calculator.trade_records.append({"test": "data"})

        # 重置
        self.calculator.reset()

        # 验证重置结果
        assert self.calculator.current_capital == self.calculator.initial_capital
        assert len(self.calculator.positions) == 0
        assert len(self.calculator.daily_returns) == 0
        assert len(self.calculator.daily_values) == 1
        assert self.calculator.daily_values[0] == self.calculator.initial_capital
        assert len(self.calculator.trade_records) == 0

    def test_execute_trade_buy(self):
        """测试买入交易执行"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="BUY",
            signal_strength=Decimal('0.8'),
            position_size=Decimal('0.1'),
            timestamp=datetime.now(),
            confidence=Decimal('0.9')
        )
        price = Decimal('10.00')
        timestamp = datetime.now()

        initial_capital = self.calculator.current_capital
        cost = self.calculator._execute_trade(signal, price, timestamp)

        assert isinstance(cost, TransactionCost)
        assert self.calculator.current_capital < initial_capital  # 资金应该减少
        assert len(self.calculator.trade_records) == 1

    def test_execute_trade_hold(self):
        """测试持有信号的交易执行"""
        signal = TradingSignal(
            stock_code="000001",
            signal_type="HOLD",
            signal_strength=Decimal('0.5'),
            position_size=Decimal('0.0'),
            timestamp=datetime.now(),
            confidence=Decimal('0.5')
        )
        price = Decimal('10.00')
        timestamp = datetime.now()

        initial_capital = self.calculator.current_capital
        cost = self.calculator._execute_trade(signal, price, timestamp)

        assert cost.total_cost == Decimal('0')
        assert self.calculator.current_capital == initial_capital  # 资金不变
        assert len(self.calculator.trade_records) == 0


class TestPerformanceMetrics:
    """绩效指标测试类"""

    def test_performance_metrics_creation(self):
        """测试绩效指标创建"""
        metrics = PerformanceMetrics(
            total_return=Decimal('0.15'),
            annual_return=Decimal('0.12'),
            max_drawdown=Decimal('0.08'),
            sharpe_ratio=Decimal('1.5'),
            win_rate=Decimal('0.6'),
            trade_count=100
        )

        assert metrics.total_return == Decimal('0.15')
        assert metrics.annual_return == Decimal('0.12')
        assert metrics.max_drawdown == Decimal('0.08')
        assert metrics.sharpe_ratio == Decimal('1.5')
        assert metrics.win_rate == Decimal('0.6')
        assert metrics.trade_count == 100

    def test_performance_metrics_defaults(self):
        """测试绩效指标默认值"""
        metrics = PerformanceMetrics()

        assert metrics.total_return == Decimal('0')
        assert metrics.annual_return == Decimal('0')
        assert metrics.max_drawdown == Decimal('0')
        assert metrics.win_rate == Decimal('0')
        assert metrics.trade_count == 0
        assert metrics.sharpe_ratio is None
        assert metrics.sortino_ratio is None


class TestTransactionCost:
    """交易成本测试类"""

    def test_transaction_cost_creation(self):
        """测试交易成本创建"""
        cost = TransactionCost(
            commission=Decimal('30.0'),
            stamp_tax=Decimal('10.0'),
            transfer_fee=Decimal('2.0'),
            slippage=Decimal('5.0'),
            total_cost=Decimal('47.0')
        )

        assert cost.commission == Decimal('30.0')
        assert cost.stamp_tax == Decimal('10.0')
        assert cost.transfer_fee == Decimal('2.0')
        assert cost.slippage == Decimal('5.0')
        assert cost.total_cost == Decimal('47.0')

    def test_transaction_cost_defaults(self):
        """测试交易成本默认值"""
        cost = TransactionCost()

        assert cost.commission == Decimal('0')
        assert cost.stamp_tax == Decimal('0')
        assert cost.transfer_fee == Decimal('0')
        assert cost.slippage == Decimal('0')
        assert cost.total_cost == Decimal('0')


class TestPortfolioPosition:
    """投资组合持仓测试类"""

    def test_portfolio_position_creation(self):
        """测试持仓创建"""
        position = PortfolioPosition(
            stock_code="000001",
            shares=1000,
            avg_cost=Decimal('10.50'),
            market_value=Decimal('11000'),
            unrealized_pnl=Decimal('500')
        )

        assert position.stock_code == "000001"
        assert position.shares == 1000
        assert position.avg_cost == Decimal('10.50')
        assert position.market_value == Decimal('11000')
        assert position.unrealized_pnl == Decimal('500')

    def test_portfolio_position_defaults(self):
        """测试持仓默认值"""
        position = PortfolioPosition(stock_code="000001")

        assert position.stock_code == "000001"
        assert position.shares == 0
        assert position.avg_cost == Decimal('0')
        assert position.market_value == Decimal('0')
        assert position.unrealized_pnl == Decimal('0')
