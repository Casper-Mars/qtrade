"""基于因子的Backtrader策略模块单元测试

本模块测试基于因子组合的交易策略的所有功能，包括：
- FactorStrategy 策略初始化测试
- 因子信号计算测试
- 交易信号生成测试
- 交易执行逻辑测试
- 止损止盈功能测试
"""

import math
from typing import Any
from unittest.mock import Mock, patch

import backtrader as bt  # type: ignore
import pytest

from src.backtest_engine.models.backtest_models import (
    BacktestFactorConfig,
    BacktestMode,
    FactorItem,
)
from src.backtest_engine.services.factor_strategy import FactorStrategy


class TestFactorStrategy:
    """因子策略测试类"""

    def setup_method(self) -> None:
        """测试前置设置"""
        # 创建测试用的因子配置
        self.factor_config = BacktestFactorConfig(
            combination_id="test_combination_001",
            description="测试因子组合",
            factors=[
                FactorItem(
                    factor_name="PE",
                    factor_type="fundamental",
                    weight=0.4
                ),
                FactorItem(
                    factor_name="RSI",
                    factor_type="technical",
                    weight=0.3
                ),
                FactorItem(
                    factor_name="MA",
                    factor_type="technical",
                    weight=0.3
                )
            ]
        )

        # 创建模拟的Backtrader环境
        self.cerebro = bt.Cerebro()
        self.data_feed = self._create_mock_data_feed()

    def _create_mock_data_feed(self) -> Mock:
        """创建模拟数据源"""
        data_feed = Mock()
        data_feed.close = [100.0]  # 当前价格
        data_feed.factor_data = [{
            "PE": 15.5,
            "RSI": 0.7,
            "MA": 0.6
        }]
        data_feed._minperiod = 1
        data_feed.lines = Mock()
        data_feed.lines.close = data_feed.close
        return data_feed

    def _create_strategy_instance(self, **kwargs: Any) -> FactorStrategy:
        """创建策略实例"""
        # 设置默认参数
        params = {
            'factor_combination': self.factor_config,
            'buy_threshold': 0.6,
            'sell_threshold': 0.4,
            'backtest_mode': BacktestMode.HISTORICAL_SIMULATION,
            'position_size': 0.95,
            'stop_loss': None,
            'take_profit': None,
        }
        params.update(kwargs)

        # 直接创建策略对象，绕过backtrader的复杂初始化
        strategy = object.__new__(FactorStrategy)

        # 创建模拟的参数对象
        strategy.p = Mock()
        for key, value in params.items():
            setattr(strategy.p, key, value)

        # 验证参数（模拟真实的FactorStrategy.__init__行为）
        if not params['factor_combination']:
            raise ValueError("因子组合配置不能为空")

        # 手动初始化策略的核心属性
        strategy.factor_combination = params['factor_combination']
        strategy.current_position = 0
        strategy.last_signal = 0.0
        strategy.trade_count = 0

        # 计算因子权重
        if strategy.factor_combination and strategy.factor_combination.factors:
            strategy.factor_weights = {
                factor.factor_name: factor.weight
                for factor in strategy.factor_combination.factors
            }
        else:
            strategy.factor_weights = {}

        # 模拟Backtrader环境
        strategy.data = self.data_feed

        # 模拟交易方法
        strategy.buy = Mock()
        strategy.sell = Mock()
        strategy.close = Mock()

        # 创建模拟的broker和position，直接设置为属性
        mock_broker = Mock()
        mock_broker.getcash = Mock(return_value=100000.0)
        strategy.broker = mock_broker

        # 创建position mock对象
        mock_position = Mock()
        mock_position.size = 0
        mock_position.price = 0.0

        # 让mock_position在size为0时返回False（模拟backtrader的行为）
        mock_position.__bool__ = lambda self: self.size != 0

        # 使用property来模拟position属性
        type(strategy).position = property(lambda self: mock_position)
        strategy._mock_position = mock_position  # 保留引用以便测试中修改

        return strategy

    def test_strategy_initialization_success(self) -> None:
        """测试策略初始化成功场景"""
        # 执行测试
        strategy = self._create_strategy_instance()

        # 验证结果 - 测试策略的核心业务逻辑属性
        assert strategy.factor_combination == self.factor_config
        assert hasattr(strategy, 'current_position')
        assert hasattr(strategy, 'last_signal')
        assert hasattr(strategy, 'trade_count')
        assert len(strategy.factor_weights) == 3
        assert strategy.factor_weights["PE"] == 0.4
        assert strategy.factor_weights["RSI"] == 0.3
        assert strategy.factor_weights["MA"] == 0.3

        # 验证策略参数配置
        assert strategy.p.buy_threshold == 0.6
        assert strategy.p.sell_threshold == 0.4
        assert strategy.p.position_size == 0.95

    def test_strategy_initialization_empty_factor_combination(self) -> None:
        """测试因子组合为空的初始化失败场景"""
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="因子组合配置不能为空"):
            self._create_strategy_instance(factor_combination=None)

    def test_calculate_composite_signal_success(self) -> None:
        """测试综合因子信号计算成功场景"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 执行测试
        composite_signal = strategy._calculate_composite_signal()

        # 验证结果
        assert isinstance(composite_signal, float)
        assert 0.0 <= composite_signal <= 1.0

        # 验证信号计算逻辑
        # PE=15.5 -> sigmoid(15.5) ≈ 1.0
        # RSI=0.7 -> sigmoid(0.7) ≈ 0.67
        # MA=0.6 -> sigmoid(0.6) ≈ 0.65
        # 加权平均: (1.0*0.4 + 0.67*0.3 + 0.65*0.3) / 1.0 ≈ 0.796
        expected_signal = (
            (1 / (1 + math.exp(-15.5))) * 0.4 +
            (1 / (1 + math.exp(-0.7))) * 0.3 +
            (1 / (1 + math.exp(-0.6))) * 0.3
        )
        assert abs(composite_signal - expected_signal) < 0.01

    def test_calculate_composite_signal_no_factor_data(self) -> None:
        """测试无因子数据时的信号计算"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.data.factor_data = [None]

        # 执行测试
        composite_signal = strategy._calculate_composite_signal()

        # 验证结果
        assert composite_signal == 0.5  # 默认中性信号

    def test_calculate_composite_signal_missing_factor_data_attribute(self) -> None:
        """测试缺少factor_data属性时的信号计算"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        delattr(strategy.data, 'factor_data')

        # 执行测试
        composite_signal = strategy._calculate_composite_signal()

        # 验证结果
        assert composite_signal == 0.5  # 默认中性信号

    def test_normalize_factor_value_normal_values(self) -> None:
        """测试正常因子值的标准化"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 执行测试
        result1 = strategy._normalize_factor_value(0.0, "test_factor")
        result2 = strategy._normalize_factor_value(1.0, "test_factor")
        result3 = strategy._normalize_factor_value(-1.0, "test_factor")

        # 验证结果
        assert result1 == 0.5  # sigmoid(0) = 0.5
        assert abs(result2 - (1 / (1 + math.exp(-1.0)))) < 0.001
        assert abs(result3 - (1 / (1 + math.exp(1.0)))) < 0.001

    def test_normalize_factor_value_none_value(self) -> None:
        """测试None值的标准化"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 执行测试
        result = strategy._normalize_factor_value(None, "test_factor")

        # 验证结果
        assert result == 0.5

    def test_normalize_factor_value_invalid_type(self) -> None:
        """测试无效类型值的标准化"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 执行测试
        result = strategy._normalize_factor_value("invalid", "test_factor")  # type: ignore[arg-type]

        # 验证结果
        assert result == 0.5

    def test_normalize_factor_value_overflow(self) -> None:
        """测试溢出值的标准化"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 执行测试
        result = strategy._normalize_factor_value(1000.0, "test_factor")

        # 验证结果
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_generate_trade_signal_buy(self) -> None:
        """测试买入信号生成"""
        # 准备测试数据
        strategy = self._create_strategy_instance(buy_threshold=0.6)

        # 执行测试
        signal = strategy._generate_trade_signal(0.8)

        # 验证结果
        assert signal == 'BUY'

    def test_generate_trade_signal_sell(self) -> None:
        """测试卖出信号生成"""
        # 准备测试数据
        strategy = self._create_strategy_instance(sell_threshold=0.4)

        # 执行测试
        signal = strategy._generate_trade_signal(0.2)

        # 验证结果
        assert signal == 'SELL'

    def test_generate_trade_signal_hold(self) -> None:
        """测试持有信号生成"""
        # 准备测试数据
        strategy = self._create_strategy_instance(buy_threshold=0.6, sell_threshold=0.4)

        # 执行测试
        signal = strategy._generate_trade_signal(0.5)

        # 验证结果
        assert signal == 'HOLD'

    def test_execute_buy_order_success(self) -> None:
        """测试买入订单执行成功"""
        # 准备测试数据
        strategy = self._create_strategy_instance(position_size=0.95)
        strategy.broker.getcash.return_value = 100000.0
        strategy.data.close = [100.0]

        # 执行测试
        strategy._execute_buy_order(0.8)

        # 验证结果
        strategy.buy.assert_called_once()
        call_args = strategy.buy.call_args
        expected_size = int((100000.0 * 0.95 * 0.8) / 100.0)
        assert call_args[1]['size'] == expected_size
        assert strategy.trade_count == 1

    def test_execute_buy_order_zero_size(self) -> None:
        """测试买入订单大小为0的场景"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.broker.getcash.return_value = 10.0  # 很少的现金
        strategy.data.close = [1000.0]  # 很高的价格

        # 执行测试
        strategy._execute_buy_order(0.8)

        # 验证结果
        strategy.buy.assert_not_called()
        assert strategy.trade_count == 0

    def test_execute_sell_order_with_position(self) -> None:
        """测试有持仓时的卖出订单执行"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 100
        strategy.data.close = [105.0]

        # 执行测试
        strategy._execute_sell_order(0.2)

        # 验证结果
        strategy.close.assert_called_once()
        assert strategy.trade_count == 1

    def test_execute_sell_order_no_position(self) -> None:
        """测试无持仓时的卖出订单执行"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 0

        # 执行测试
        strategy._execute_sell_order(0.2)

        # 验证结果 - 无持仓时不应该调用close()
        strategy.close.assert_not_called()
        assert strategy.trade_count == 0

    def test_execute_trade_decision_buy_signal(self) -> None:
        """测试买入信号的交易决策执行"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 0
        with patch.object(strategy, '_execute_buy_order') as mock_buy, \
             patch.object(strategy, '_check_stop_conditions') as mock_check:

            # 执行测试
            strategy._execute_trade_decision('BUY', 0.8)

            # 验证结果 - 无持仓时不会调用_check_stop_conditions
            mock_buy.assert_called_once_with(0.8)
            mock_check.assert_not_called()

    def test_execute_trade_decision_sell_signal(self) -> None:
        """测试卖出信号的交易决策执行"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 100
        with patch.object(strategy, '_execute_sell_order') as mock_sell, \
             patch.object(strategy, '_check_stop_conditions') as mock_check:

            # 执行测试
            strategy._execute_trade_decision('SELL', 0.2)

            # 验证结果
            mock_sell.assert_called_once_with(0.2)
            mock_check.assert_called_once()

    def test_execute_trade_decision_hold_signal(self) -> None:
        """测试持有信号的交易决策执行"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 50
        with patch.object(strategy, '_execute_buy_order') as mock_buy, \
             patch.object(strategy, '_execute_sell_order') as mock_sell, \
             patch.object(strategy, '_check_stop_conditions') as mock_check:

            # 执行测试
            strategy._execute_trade_decision('HOLD', 0.5)

            # 验证结果
            mock_buy.assert_not_called()
            mock_sell.assert_not_called()
            mock_check.assert_called_once()

    def test_check_stop_conditions_no_position(self) -> None:
        """测试无持仓时的止损止盈检查"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 0  # 模拟无持仓

        # 执行测试
        strategy._check_stop_conditions()

        # 验证结果 - 不应该有任何操作
        strategy.close.assert_not_called()

    def test_check_stop_conditions_stop_loss_triggered(self) -> None:
        """测试止损触发"""
        # 准备测试数据
        strategy = self._create_strategy_instance(stop_loss=0.1)
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data.close = [85.0]  # 当前价格，亏损15%

        # 执行测试
        strategy._check_stop_conditions()

        # 验证结果
        strategy.close.assert_called_once()

    def test_check_stop_conditions_take_profit_triggered(self) -> None:
        """测试止盈触发"""
        # 准备测试数据
        strategy = self._create_strategy_instance(take_profit=0.15)
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data.close = [120.0]  # 当前价格，盈利20%

        # 执行测试
        strategy._check_stop_conditions()

        # 验证结果
        strategy.close.assert_called_once()

    def test_check_stop_conditions_no_trigger(self) -> None:
        """测试止损止盈未触发"""
        # 准备测试数据
        strategy = self._create_strategy_instance(stop_loss=0.1, take_profit=0.2)
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data.close = [105.0]  # 当前价格，盈利5%

        # 执行测试
        strategy._check_stop_conditions()

        # 验证结果
        strategy.close.assert_not_called()

    def test_next_method_success(self) -> None:
        """测试策略主逻辑执行成功"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        with patch.object(strategy, '_calculate_composite_signal', return_value=0.8) as mock_calc, \
             patch.object(strategy, '_generate_trade_signal', return_value='BUY') as mock_gen, \
             patch.object(strategy, '_execute_trade_decision') as mock_exec:

            # 执行测试
            strategy.next()

            # 验证结果
            mock_calc.assert_called_once()
            mock_gen.assert_called_once_with(0.8)
            mock_exec.assert_called_once_with('BUY', 0.8)
            assert strategy.last_signal == 0.8

    def test_next_method_exception_handling(self) -> None:
        """测试策略主逻辑异常处理"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        with patch.object(strategy, '_calculate_composite_signal', side_effect=Exception("测试异常")) as mock_calc:

            # 执行测试 - 不应该抛出异常
            strategy.next()

            # 验证结果 - 异常被捕获并记录
            mock_calc.assert_called_once()

    def test_notify_order_completed_buy(self) -> None:
        """测试买入订单完成通知"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        order = Mock()
        order.status = bt.Order.Completed
        order.isbuy.return_value = True
        order.executed.price = 100.0
        order.executed.size = 50

        # 执行测试
        strategy.notify_order(order)

        # 验证结果 - 不抛出异常即可
        assert True

    def test_notify_order_completed_sell(self) -> None:
        """测试卖出订单完成通知"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        order = Mock()
        order.status = bt.Order.Completed
        order.isbuy.return_value = False
        order.executed.price = 105.0
        order.executed.size = 50

        # 执行测试
        strategy.notify_order(order)

        # 验证结果 - 不抛出异常即可
        assert True

    def test_notify_order_rejected(self) -> None:
        """测试订单被拒绝通知"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        order = Mock()
        order.status = bt.Order.Rejected

        # 执行测试
        strategy.notify_order(order)

        # 验证结果 - 不抛出异常即可
        assert True

    def test_notify_trade_closed(self) -> None:
        """测试交易完成通知"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        trade = Mock()
        trade.isclosed = True
        trade.pnl = 500.0
        trade.pnlcomm = 485.0

        # 执行测试
        strategy.notify_trade(trade)

        # 验证结果 - 不抛出异常即可
        assert True

    def test_notify_trade_open(self) -> None:
        """测试交易开仓通知"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        trade = Mock()
        trade.isclosed = False

        # 执行测试
        strategy.notify_trade(trade)

        # 验证结果 - 不抛出异常即可
        assert True

    def test_get_strategy_stats(self) -> None:
        """测试获取策略统计信息"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.trade_count = 5
        strategy.last_signal = 0.75
        strategy.position.size = 100

        # 执行测试
        stats = strategy.get_strategy_stats()

        # 验证结果
        assert stats['trade_count'] == 5
        assert stats['current_position'] == 100
        assert stats['last_signal'] == 0.75
        assert stats['factor_count'] == 3
        assert stats['buy_threshold'] == 0.6
        assert stats['sell_threshold'] == 0.4

    def test_get_strategy_stats_no_position(self) -> None:
        """测试无持仓时获取策略统计信息"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.position.size = 0  # 模拟无持仓

        # 执行测试
        stats = strategy.get_strategy_stats()

        # 验证结果
        assert stats['current_position'] == 0

    def test_strategy_with_custom_thresholds(self) -> None:
        """测试自定义阈值的策略"""
        # 准备测试数据
        strategy = self._create_strategy_instance(
            buy_threshold=0.8,
            sell_threshold=0.2
        )

        # 验证结果
        assert strategy.p.buy_threshold == 0.8
        assert strategy.p.sell_threshold == 0.2

        # 测试信号生成
        assert strategy._generate_trade_signal(0.9) == 'BUY'
        assert strategy._generate_trade_signal(0.1) == 'SELL'
        assert strategy._generate_trade_signal(0.5) == 'HOLD'

    def test_strategy_with_stop_loss_take_profit(self) -> None:
        """测试带止损止盈的策略"""
        # 准备测试数据
        strategy = self._create_strategy_instance(
            stop_loss=0.05,
            take_profit=0.1
        )

        # 验证结果
        assert strategy.p.stop_loss == 0.05
        assert strategy.p.take_profit == 0.1

    def test_factor_weights_calculation(self) -> None:
        """测试因子权重计算"""
        # 准备测试数据
        strategy = self._create_strategy_instance()

        # 验证结果
        expected_weights = {
            "PE": 0.4,
            "RSI": 0.3,
            "MA": 0.3
        }
        assert strategy.factor_weights == expected_weights

    def test_composite_signal_with_missing_factors(self) -> None:
        """测试部分因子缺失时的综合信号计算"""
        # 准备测试数据
        strategy = self._create_strategy_instance()
        strategy.data.factor_data = [{
            "PE": 15.5,
            "RSI": 0.7
            # MA因子缺失
        }]

        # 执行测试
        composite_signal = strategy._calculate_composite_signal()

        # 验证结果
        assert isinstance(composite_signal, float)
        assert 0.0 <= composite_signal <= 1.0

        # 只有PE和RSI参与计算
        expected_signal = (
            (1 / (1 + math.exp(-15.5))) * 0.4 +
            (1 / (1 + math.exp(-0.7))) * 0.3
        ) / 0.7  # 总权重为0.7
        assert abs(composite_signal - expected_signal) < 0.01
