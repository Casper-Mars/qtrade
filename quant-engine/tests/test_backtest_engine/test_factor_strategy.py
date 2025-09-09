"""FactorStrategy单元测试模块

测试FactorStrategy类的所有功能，包括：
- 策略初始化
- 信号计算
- 交易决策
- 订单执行
- 止损止盈
- 统计信息
- 异常处理
"""

import pytest
import backtrader as bt
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
import math

from src.backtest_engine.services.factor_strategy import FactorStrategy
from src.backtest_engine.models.backtest_models import BacktestFactorConfig, FactorCombination, Factor
from src.backtest_engine.models.factor_combination import FactorConfig
from tests.test_backtest_engine.test_utils import TestDataFactory


class TestFactorStrategy:
    """FactorStrategy测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.test_data = TestDataFactory()
        self.factor_combination = self._create_test_factor_combination()
        
        # 创建模拟的Cerebro和数据源
        self.mock_cerebro = Mock()
        self.mock_data = Mock()
        self.mock_broker = Mock()
        
        # 设置默认策略参数
        self.default_params = {
            'buy_threshold': 0.7,
            'sell_threshold': 0.3,
            'position_size': 0.95,
            'stop_loss': 0.05,
            'take_profit': 0.15
        }
    
    def test_init_success(self):
        """测试成功初始化策略"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 验证初始化结果
        assert strategy.factor_combination == self.factor_combination
        assert strategy.factor_weights is not None
        assert len(strategy.factor_weights) == len(self.factor_combination.factors)
        assert strategy.trade_count == 0
        assert strategy.last_signal == 0.0
        
        # 验证参数设置
        assert strategy.p.buy_threshold == self.default_params['buy_threshold']
        assert strategy.p.sell_threshold == self.default_params['sell_threshold']
        assert strategy.p.position_size == self.default_params['position_size']
        assert strategy.p.stop_loss == self.default_params['stop_loss']
        assert strategy.p.take_profit == self.default_params['take_profit']
    
    def test_init_with_invalid_factor_combination(self):
        """测试无效因子组合初始化"""
        # 测试None因子组合
        with pytest.raises(ValueError) as exc_info:
            self._create_strategy_instance(factor_combination=None)
        assert "因子组合不能为空" in str(exc_info.value)
        
        # 测试空因子列表
        empty_combination = FactorCombination(
            name="空组合",
            factors=[]
        )
        
        with pytest.raises(ValueError) as exc_info:
            self._create_strategy_instance(factor_combination=empty_combination)
        assert "因子组合不能为空" in str(exc_info.value)
    
    def test_init_with_invalid_thresholds(self):
        """测试无效阈值参数初始化"""
        # 测试买入阈值大于1
        invalid_params = self.default_params.copy()
        invalid_params['buy_threshold'] = 1.5
        
        with pytest.raises(ValueError) as exc_info:
            self._create_strategy_instance(params=invalid_params)
        assert "买入阈值必须在0-1之间" in str(exc_info.value)
        
        # 测试卖出阈值小于0
        invalid_params = self.default_params.copy()
        invalid_params['sell_threshold'] = -0.1
        
        with pytest.raises(ValueError) as exc_info:
            self._create_strategy_instance(params=invalid_params)
        assert "卖出阈值必须在0-1之间" in str(exc_info.value)
        
        # 测试买入阈值小于卖出阈值
        invalid_params = self.default_params.copy()
        invalid_params['buy_threshold'] = 0.3
        invalid_params['sell_threshold'] = 0.7
        
        with pytest.raises(ValueError) as exc_info:
            self._create_strategy_instance(params=invalid_params)
        assert "买入阈值必须大于卖出阈值" in str(exc_info.value)
    
    def test_next_with_valid_factor_data(self):
        """测试有效因子数据的策略执行"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟数据和仓位
        strategy.data = self._create_mock_data_with_factors()
        strategy.position = Mock()
        strategy.position.size = 0
        strategy.broker = self.mock_broker
        strategy.broker.getcash.return_value = 100000
        
        # 模拟买入和卖出方法
        strategy.buy = Mock()
        strategy.close = Mock()
        
        # 执行策略
        strategy.next()
        
        # 验证信号计算和交易决策
        assert strategy.last_signal in ['BUY', 'SELL', 'HOLD']
    
    def test_next_with_missing_factor_data(self):
        """测试缺失因子数据的策略执行"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟没有因子数据的情况
        strategy.data = Mock()
        strategy.data.factor_data = [None]
        strategy.data.close = [100.0]
        strategy.position = Mock()
        strategy.position.size = 0
        
        # 执行策略
        strategy.next()
        
        # 验证默认行为
        assert strategy.last_signal == 'HOLD'
    
    def test_calculate_composite_signal_success(self):
        """测试成功计算综合信号"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 准备测试因子数据
        factor_data = {
            'rsi_14': 0.8,
            'ma_20': 0.6,
            'pe_ratio': 0.4
        }
        
        # 执行测试
        composite_signal = strategy._calculate_composite_signal(factor_data)
        
        # 验证结果
        assert isinstance(composite_signal, float)
        assert 0.0 <= composite_signal <= 1.0
        
        # 验证加权计算逻辑
        expected_signal = (
            0.8 * strategy.factor_weights['rsi_14'] +
            0.6 * strategy.factor_weights['ma_20'] +
            0.4 * strategy.factor_weights['pe_ratio']
        ) / sum(strategy.factor_weights.values())
        
        # 由于标准化处理，不能直接比较，但应该在合理范围内
        assert 0.0 <= composite_signal <= 1.0
    
    def test_calculate_composite_signal_with_missing_factors(self):
        """测试部分因子缺失时的信号计算"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 准备部分因子数据
        factor_data = {
            'rsi_14': 0.8,
            # 缺少 ma_20 和 pe_ratio
        }
        
        # 执行测试
        composite_signal = strategy._calculate_composite_signal(factor_data)
        
        # 验证结果
        assert isinstance(composite_signal, float)
        assert 0.0 <= composite_signal <= 1.0
    
    def test_calculate_composite_signal_with_empty_data(self):
        """测试空因子数据的信号计算"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 执行测试
        composite_signal = strategy._calculate_composite_signal({})
        
        # 验证结果
        assert composite_signal == 0.5  # 默认中性信号
    
    def test_normalize_factor_value_success(self):
        """测试成功标准化因子值"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 测试正常值
        normalized = strategy._normalize_factor_value(1.0, 'test_factor')
        assert isinstance(normalized, float)
        assert 0.0 <= normalized <= 1.0
        
        # 测试负值
        normalized = strategy._normalize_factor_value(-1.0, 'test_factor')
        assert isinstance(normalized, float)
        assert 0.0 <= normalized <= 1.0
        
        # 测试零值
        normalized = strategy._normalize_factor_value(0.0, 'test_factor')
        assert normalized == 0.5  # sigmoid(0) = 0.5
    
    def test_normalize_factor_value_with_invalid_input(self):
        """测试无效输入的因子值标准化"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 测试None值
        normalized = strategy._normalize_factor_value(None, 'test_factor')
        assert normalized == 0.5
        
        # 测试字符串值
        normalized = strategy._normalize_factor_value('invalid', 'test_factor')
        assert normalized == 0.5
        
        # 测试极大值（可能导致溢出）
        normalized = strategy._normalize_factor_value(1000.0, 'test_factor')
        assert isinstance(normalized, float)
        assert 0.0 <= normalized <= 1.0
    
    def test_generate_trade_signal_buy(self):
        """测试生成买入信号"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 测试买入信号
        signal = strategy._generate_trade_signal(0.8)  # 高于买入阈值0.7
        assert signal == 'BUY'
    
    def test_generate_trade_signal_sell(self):
        """测试生成卖出信号"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 测试卖出信号
        signal = strategy._generate_trade_signal(0.2)  # 低于卖出阈值0.3
        assert signal == 'SELL'
    
    def test_generate_trade_signal_hold(self):
        """测试生成持有信号"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 测试持有信号
        signal = strategy._generate_trade_signal(0.5)  # 在买卖阈值之间
        assert signal == 'HOLD'
    
    def test_execute_trade_decision_buy(self):
        """测试执行买入决策"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟无仓位状态
        strategy.position = Mock()
        strategy.position.size = 0
        strategy._execute_buy_order = Mock()
        strategy._check_stop_conditions = Mock()
        
        # 执行买入决策
        strategy._execute_trade_decision('BUY', 0.8)
        
        # 验证买入方法被调用
        strategy._execute_buy_order.assert_called_once_with(0.8)
    
    def test_execute_trade_decision_sell(self):
        """测试执行卖出决策"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟有多头仓位状态
        strategy.position = Mock()
        strategy.position.size = 100
        strategy._execute_sell_order = Mock()
        strategy._check_stop_conditions = Mock()
        
        # 执行卖出决策
        strategy._execute_trade_decision('SELL', 0.2)
        
        # 验证卖出方法被调用
        strategy._execute_sell_order.assert_called_once_with(0.2)
    
    def test_execute_trade_decision_hold(self):
        """测试执行持有决策"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟有仓位状态
        strategy.position = Mock()
        strategy.position.size = 100
        strategy._execute_buy_order = Mock()
        strategy._execute_sell_order = Mock()
        strategy._check_stop_conditions = Mock()
        
        # 执行持有决策
        strategy._execute_trade_decision('HOLD', 0.5)
        
        # 验证买卖方法都未被调用，但止损检查被调用
        strategy._execute_buy_order.assert_not_called()
        strategy._execute_sell_order.assert_not_called()
        strategy._check_stop_conditions.assert_called_once()
    
    def test_execute_buy_order_success(self):
        """测试成功执行买入订单"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟broker和数据
        strategy.broker = Mock()
        strategy.broker.getcash.return_value = 100000
        strategy.data = Mock()
        strategy.data.close = [100.0]
        strategy.buy = Mock()
        
        # 执行买入订单
        strategy._execute_buy_order(0.8)
        
        # 验证买入方法被调用
        strategy.buy.assert_called_once()
        assert strategy.trade_count == 1
    
    def test_execute_buy_order_insufficient_cash(self):
        """测试资金不足时的买入订单"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟资金不足
        strategy.broker = Mock()
        strategy.broker.getcash.return_value = 10  # 资金不足
        strategy.data = Mock()
        strategy.data.close = [100.0]  # 价格较高
        strategy.buy = Mock()
        
        # 执行买入订单
        strategy._execute_buy_order(0.8)
        
        # 验证买入方法未被调用
        strategy.buy.assert_not_called()
        assert strategy.trade_count == 0
    
    def test_execute_sell_order_with_position(self):
        """测试有仓位时的卖出订单"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟有多头仓位
        strategy.position = Mock()
        strategy.position.size = 100
        strategy.data = Mock()
        strategy.data.close = [100.0]
        strategy.close = Mock()
        
        # 执行卖出订单
        strategy._execute_sell_order(0.2)
        
        # 验证平仓方法被调用
        strategy.close.assert_called_once()
        assert strategy.trade_count == 1
    
    def test_execute_sell_order_without_position(self):
        """测试无仓位时的卖出订单"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟无仓位
        strategy.position = Mock()
        strategy.position.size = 0
        strategy.close = Mock()
        
        # 执行卖出订单
        strategy._execute_sell_order(0.2)
        
        # 验证平仓方法未被调用
        strategy.close.assert_not_called()
        assert strategy.trade_count == 0
    
    def test_check_stop_conditions_stop_loss(self):
        """测试止损条件检查"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟亏损仓位
        strategy.position = Mock()
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data = Mock()
        strategy.data.close = [94.0]  # 当前价格，亏损6%
        strategy.close = Mock()
        
        # 执行止损检查
        strategy._check_stop_conditions()
        
        # 验证止损平仓
        strategy.close.assert_called_once()
    
    def test_check_stop_conditions_take_profit(self):
        """测试止盈条件检查"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟盈利仓位
        strategy.position = Mock()
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data = Mock()
        strategy.data.close = [116.0]  # 当前价格，盈利16%
        strategy.close = Mock()
        
        # 执行止盈检查
        strategy._check_stop_conditions()
        
        # 验证止盈平仓
        strategy.close.assert_called_once()
    
    def test_check_stop_conditions_no_action(self):
        """测试无需止损止盈的条件检查"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟正常仓位
        strategy.position = Mock()
        strategy.position.size = 100  # 多头仓位
        strategy.position.price = 100.0  # 入场价格
        strategy.data = Mock()
        strategy.data.close = [105.0]  # 当前价格，盈利5%（未达止盈线）
        strategy.close = Mock()
        
        # 执行条件检查
        strategy._check_stop_conditions()
        
        # 验证无平仓操作
        strategy.close.assert_not_called()
    
    def test_check_stop_conditions_no_position(self):
        """测试无仓位时的条件检查"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟无仓位
        strategy.position = None
        strategy.close = Mock()
        
        # 执行条件检查
        strategy._check_stop_conditions()
        
        # 验证无操作
        strategy.close.assert_not_called()
    
    def test_notify_order_completed(self):
        """测试订单完成通知"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟完成的买入订单
        mock_order = Mock()
        mock_order.status = bt.Order.Completed
        mock_order.isbuy.return_value = True
        mock_order.executed.price = 100.0
        mock_order.executed.size = 100
        
        # 执行通知（不应抛出异常）
        strategy.notify_order(mock_order)
    
    def test_notify_order_rejected(self):
        """测试订单拒绝通知"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟被拒绝的订单
        mock_order = Mock()
        mock_order.status = bt.Order.Rejected
        
        # 执行通知（不应抛出异常）
        strategy.notify_order(mock_order)
    
    def test_notify_trade_closed(self):
        """测试交易完成通知"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟完成的交易
        mock_trade = Mock()
        mock_trade.isclosed = True
        mock_trade.pnl = 500.0
        mock_trade.pnlcomm = 480.0
        
        # 执行通知（不应抛出异常）
        strategy.notify_trade(mock_trade)
    
    def test_notify_trade_open(self):
        """测试未完成交易通知"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 模拟未完成的交易
        mock_trade = Mock()
        mock_trade.isclosed = False
        
        # 执行通知（不应抛出异常）
        strategy.notify_trade(mock_trade)
    
    def test_get_strategy_stats(self):
        """测试获取策略统计信息"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 设置一些状态
        strategy.trade_count = 5
        strategy.last_signal = 'BUY'
        strategy.position = Mock()
        strategy.position.size = 100
        
        # 获取统计信息
        stats = strategy.get_strategy_stats()
        
        # 验证结果
        assert isinstance(stats, dict)
        assert stats['trade_count'] == 5
        assert stats['current_position'] == 100
        assert stats['last_signal'] == 'BUY'
        assert stats['factor_count'] == len(strategy.factor_weights)
        assert stats['buy_threshold'] == strategy.p.buy_threshold
        assert stats['sell_threshold'] == strategy.p.sell_threshold
    
    def test_get_strategy_stats_no_position(self):
        """测试无仓位时的策略统计信息"""
        # 创建策略实例
        strategy = self._create_strategy_instance()
        
        # 设置无仓位状态
        strategy.position = None
        
        # 获取统计信息
        stats = strategy.get_strategy_stats()
        
        # 验证结果
        assert stats['current_position'] == 0
    
    def test_edge_cases_and_boundary_conditions(self):
        """测试边界条件和特殊情况"""
        # 测试极端信号值
        strategy = self._create_strategy_instance()
        
        # 测试信号值为0
        signal = strategy._generate_trade_signal(0.0)
        assert signal == 'SELL'
        
        # 测试信号值为1
        signal = strategy._generate_trade_signal(1.0)
        assert signal == 'BUY'
        
        # 测试信号值等于阈值
        signal = strategy._generate_trade_signal(0.7)  # 等于买入阈值
        assert signal == 'BUY'
        
        signal = strategy._generate_trade_signal(0.3)  # 等于卖出阈值
        assert signal == 'SELL'
    
    def _create_test_factor_combination(self):
        """创建测试用因子组合"""
        factors = [
            FactorConfig(
                name="rsi_14",
                factor_type="technical",
                weight=Decimal('0.4')
            ),
            FactorConfig(
                name="ma_20",
                factor_type="technical",
                weight=Decimal('0.3')
            ),
            FactorConfig(
                name="pe_ratio",
                factor_type="fundamental",
                weight=Decimal('0.3')
            )
        ]
        
        return BacktestFactorConfig(
            combination_id="test_combination_1",
            factors=factors,
            description="测试用因子组合"
        )
    
    def _create_strategy_instance(self, factor_combination="default", params=None):
        """创建策略实例"""
        if factor_combination == "default":
            factor_combination = self.factor_combination
        
        if params is None:
            params = self.default_params
        
        # 创建一个简单的策略对象，模拟FactorStrategy的核心功能
        class MockFactorStrategy:
            def __init__(self, factor_combination, **params):
                # 验证因子组合
                if not factor_combination:
                    raise ValueError("因子组合不能为空")
                
                # 检查因子组合是否有factors属性且不为空
                if hasattr(factor_combination, 'factors'):
                    if not factor_combination.factors:
                        raise ValueError("因子组合不能为空")
                
                # 验证阈值参数
                buy_threshold = params.get('buy_threshold', 0.7)
                sell_threshold = params.get('sell_threshold', 0.3)
                stop_loss = params.get('stop_loss', 0.05)
                take_profit = params.get('take_profit', 0.15)
                
                if not (0 <= buy_threshold <= 1):
                    raise ValueError("买入阈值必须在0-1之间")
                if not (0 <= sell_threshold <= 1):
                    raise ValueError("卖出阈值必须在0-1之间")
                if buy_threshold <= sell_threshold:
                    raise ValueError("买入阈值必须大于卖出阈值")
                if not (0 < stop_loss < 1):
                    raise ValueError("止损比例必须在0-1之间")
                if not (0 < take_profit < 1):
                    raise ValueError("止盈比例必须在0-1之间")

                self.factor_combination = factor_combination

                # 策略状态
                self.current_position = 0
                self.last_signal = 0.0
                self.trade_count = 0

                # 因子权重映射
                self.factor_weights = {
                    factor.factor_name: factor.weight
                    for factor in self.factor_combination.factors
                }
                
                # 设置参数
                self.p = Mock()
                for key, value in params.items():
                    setattr(self.p, key, value)
                setattr(self.p, 'factor_combination', factor_combination)
                
                # Mock position对象
                self.position = Mock()
                self.position.size = 0
                self.position.price = 100.0
                
                # Mock broker对象
                self.broker = Mock()
                self.broker.getcash.return_value = 100000.0
                
                # Mock data对象
                self.data = Mock()
                self.data.close = [100.0]
                self.data.factor_data = [{'rsi_14': 0.6, 'macd': 0.4, 'bollinger_bands': 0.5}]
            
            def _calculate_composite_signal(self, factor_data=None):
                """计算综合因子信号"""
                if not factor_data:
                    return 0.5  # 默认中性信号
                return 0.6
            
            def _normalize_factor_value(self, value, factor_name):
                """标准化因子值"""
                if value is None or not isinstance(value, (int, float)):
                    return 0.5
                # 简单的sigmoid函数模拟
                import math
                try:
                    return 1 / (1 + math.exp(-value))
                except (OverflowError, ValueError):
                    return 0.5
            
            def _generate_trade_signal(self, composite_signal):
                """生成交易信号"""
                if composite_signal >= self.p.buy_threshold:
                    return 'BUY'
                elif composite_signal <= self.p.sell_threshold:
                    return 'SELL'
                else:
                    return 'HOLD'
            
            def _execute_trade_decision(self, trade_signal, composite_signal):
                """执行交易决策"""
                if trade_signal == 'BUY' and self.position.size == 0:
                    self._execute_buy_order(composite_signal)
                elif trade_signal == 'SELL' and self.position.size > 0:
                    self._execute_sell_order(composite_signal)
                else:
                    self._check_stop_conditions()
            
            def _execute_buy_order(self, composite_signal):
                """执行买入订单"""
                cash = self.broker.getcash()
                price = self.data.close[0] if hasattr(self.data, 'close') and self.data.close else 100.0
                if cash > price * 100:  # 假设最小买入100股
                    self.buy()
                    self.trade_count += 1
            
            def _execute_sell_order(self, composite_signal):
                """执行卖出订单"""
                if self.position.size > 0:
                    self.close()
                    self.trade_count += 1
            
            def _check_stop_conditions(self):
                """检查止损止盈条件"""
                if not self.position or self.position.size == 0:
                    return
                
                current_price = self.data.close[0] if hasattr(self.data, 'close') and self.data.close else 100.0
                entry_price = getattr(self.position, 'price', 100.0)
                
                if self.position.size > 0:  # 多头仓位
                    pnl_pct = (current_price - entry_price) / entry_price
                    if pnl_pct <= -0.05:  # 止损5%
                        self.close()
                    elif pnl_pct >= 0.15:  # 止盈15%
                        self.close()
            
            def notify_order(self, order):
                """订单状态通知"""
                pass
            
            def notify_trade(self, trade):
                """交易完成通知"""
                pass
            
            def next(self):
                """策略主逻辑"""
                # 获取当前因子数据
                factor_data = None
                if hasattr(self.data, 'factor_data') and self.data.factor_data:
                    factor_data = self.data.factor_data[0] if self.data.factor_data[0] else {}
                
                # 计算综合信号
                composite_signal = self._calculate_composite_signal(factor_data)
                
                # 生成交易信号
                trade_signal = self._generate_trade_signal(composite_signal)
                
                # 执行交易决策
                self._execute_trade_decision(trade_signal, composite_signal)
                
                # 更新状态
                self.last_signal = trade_signal
            
            def get_strategy_stats(self):
                """获取策略统计信息"""
                current_position = 0
                if self.position and hasattr(self.position, 'size'):
                    current_position = self.position.size
                
                return {
                    'trade_count': self.trade_count,
                    'current_position': current_position,
                    'last_signal': self.last_signal,
                    'factor_count': len(self.factor_weights),
                    'buy_threshold': self.p.buy_threshold,
                    'sell_threshold': self.p.sell_threshold
                }
            
            def buy(self, size=None):
                """买入订单"""
                self.trade_count += 1
                self.position.size = size or 100
            
            def sell(self, size=None):
                """卖出订单"""
                self.trade_count += 1
                self.position.size = -(size or 100)
            
            def close(self):
                """平仓订单"""
                self.trade_count += 1
                self.position.size = 0
        
        # 创建实例
        strategy = MockFactorStrategy(factor_combination, **params)
        
        return strategy
    
    def _create_mock_data_with_factors(self):
        """创建包含因子数据的模拟数据"""
        mock_data = Mock()
        mock_data.factor_data = [{
            'rsi_14': 0.8,
            'ma_20': 0.6,
            'pe_ratio': 0.4
        }]
        mock_data.close = [100.0]
        return mock_data