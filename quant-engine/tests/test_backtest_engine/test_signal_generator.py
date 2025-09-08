"""交易信号生成器单元测试

测试SignalGenerator类的各项功能，包括：
- 信号生成逻辑
- 因子综合评分计算
- 信号过滤和优化
- 仓位大小计算
"""

import math
import pytest
from datetime import datetime
from unittest.mock import Mock

from src.backtest_engine.services.signal_generator import SignalGenerator
from src.backtest_engine.models.backtest_models import (
    BacktestFactorConfig,
    FactorItem,
    TradingSignal
)


class TestSignalGenerator:
    """SignalGenerator测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.generator = SignalGenerator()
        
        # 创建测试用的因子组合配置
        self.factor_combination = BacktestFactorConfig(
            combination_id="test_config",
            description="用于测试的因子组合",
            factors=[
                FactorItem(factor_name="RSI", factor_type="technical", weight=0.3),
                FactorItem(factor_name="PE", factor_type="fundamental", weight=0.4),
                FactorItem(factor_name="sentiment_score", factor_type="sentiment", weight=0.3)
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 测试用的因子数据
        self.factor_data = {
            "RSI": 0.7,  # 超买信号
            "PE": -0.5,  # 低估值信号
            "sentiment_score": 0.8  # 积极情绪
        }
        
        self.stock_code = "000001.SZ"
        self.timestamp = "2024-01-01T10:00:00"

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        generator = SignalGenerator()
        
        assert generator.default_threshold_config['buy_threshold'] == 0.6
        assert generator.default_threshold_config['sell_threshold'] == -0.6
        assert generator.default_threshold_config['min_strength'] == 0.1
        assert generator.default_threshold_config['max_position_size'] == 1.0

    def test_init_with_custom_config(self):
        """测试使用自定义配置初始化"""
        custom_config = {
            'buy_threshold': 0.8,
            'sell_threshold': -0.8,
            'min_strength': 0.2,
            'max_position_size': 0.8
        }
        generator = SignalGenerator(custom_config)
        
        assert generator.default_threshold_config == custom_config

    def test_normalize_factor_value(self):
        """测试因子值标准化"""
        # 测试正值
        result = self.generator._normalize_factor_value(1.0)
        expected = math.tanh(1.0)
        assert abs(result - expected) < 1e-6
        
        # 测试负值
        result = self.generator._normalize_factor_value(-1.0)
        expected = math.tanh(-1.0)
        assert abs(result - expected) < 1e-6
        
        # 测试零值
        result = self.generator._normalize_factor_value(0.0)
        assert result == 0.0
        
        # 测试大值（应该接近1）
        result = self.generator._normalize_factor_value(10.0)
        assert result > 0.9
        assert result <= 1.0

    def test_calculate_composite_score(self):
        """测试因子综合评分计算"""
        score = self.generator._calculate_composite_score(
            self.factor_data, 
            self.factor_combination
        )
        
        # 验证评分在合理范围内
        assert -1.0 <= score <= 1.0
        
        # 手动计算期望值进行验证
        expected_rsi = math.tanh(0.7) * 0.3
        expected_pe = math.tanh(-0.5) * 0.4
        expected_sentiment = math.tanh(0.8) * 0.3
        expected_total = (expected_rsi + expected_pe + expected_sentiment) / 1.0
        
        assert abs(score - expected_total) < 1e-6

    def test_calculate_composite_score_missing_factors(self):
        """测试部分因子数据缺失时的综合评分计算"""
        incomplete_data = {
            "RSI": 0.7,
            "PE": -0.5
            # 缺少sentiment_score
        }
        
        score = self.generator._calculate_composite_score(
            incomplete_data, 
            self.factor_combination
        )
        
        # 应该只基于可用的因子计算
        expected_rsi = math.tanh(0.7) * 0.3
        expected_pe = math.tanh(-0.5) * 0.4
        expected_total = (expected_rsi + expected_pe) / 0.7  # 总权重为0.7
        
        assert abs(score - expected_total) < 1e-6

    def test_calculate_composite_score_empty_data(self):
        """测试空因子数据的综合评分计算"""
        score = self.generator._calculate_composite_score(
            {}, 
            self.factor_combination
        )
        
        assert score == 0.0

    def test_calculate_factor_scores(self):
        """测试各因子评分计算"""
        scores = self.generator._calculate_factor_scores(
            self.factor_data, 
            self.factor_combination
        )
        
        assert "RSI" in scores
        assert "PE" in scores
        assert "sentiment_score" in scores
        
        # 验证标准化值
        assert abs(scores["RSI"] - math.tanh(0.7)) < 1e-6
        assert abs(scores["PE"] - math.tanh(-0.5)) < 1e-6
        assert abs(scores["sentiment_score"] - math.tanh(0.8)) < 1e-6

    def test_generate_buy_signal(self):
        """测试买入信号生成"""
        # 构造强烈买入信号的数据
        strong_buy_data = {
            "RSI": 2.0,  # 强烈超买但在这里作为买入信号
            "PE": 2.0,   # 强烈低估值
            "sentiment_score": 2.0  # 强烈积极情绪
        }
        
        signal = self.generator.generate_signals(
            strong_buy_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        assert signal.signal_type == "BUY"
        assert signal.strength > 0.6
        assert signal.position_size > 0
        assert signal.stock_code == self.stock_code
        assert signal.timestamp == self.timestamp
        assert signal.composite_score > 0.6

    def test_generate_sell_signal(self):
        """测试卖出信号生成"""
        # 构造强烈卖出信号的数据
        strong_sell_data = {
            "RSI": -2.0,  # 强烈超卖
            "PE": -2.0,   # 强烈高估值
            "sentiment_score": -2.0  # 强烈消极情绪
        }
        
        signal = self.generator.generate_signals(
            strong_sell_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        assert signal.signal_type == "SELL"
        assert signal.strength > 0.6
        assert signal.position_size > 0
        assert signal.composite_score < -0.6

    def test_generate_hold_signal(self):
        """测试持有信号生成"""
        # 构造中性信号的数据
        neutral_data = {
            "RSI": 0.1,
            "PE": -0.1,
            "sentiment_score": 0.05
        }
        
        signal = self.generator.generate_signals(
            neutral_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        assert signal.signal_type == "HOLD"
        assert signal.strength == 0.0
        assert signal.position_size == 0.0
        assert -0.6 < signal.composite_score < 0.6

    def test_generate_signals_with_custom_thresholds(self):
        """测试使用自定义阈值生成信号"""
        custom_thresholds = {
            'buy_threshold': 0.8,
            'sell_threshold': -0.8,
            'min_strength': 0.2,
            'max_position_size': 0.5
        }
        
        # 使用中等强度的数据，在默认阈值下会产生买入信号，但在高阈值下应该是持有
        moderate_data = {
            "RSI": 1.0,
            "PE": 1.0,
            "sentiment_score": 1.0
        }
        
        signal = self.generator.generate_signals(
            moderate_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp,
            custom_thresholds
        )
        
        # 由于阈值提高，可能变成HOLD信号
        if signal.signal_type == "BUY":
            assert signal.position_size <= 0.5  # 不超过最大仓位

    def test_calculate_confidence(self):
        """测试信号置信度计算"""
        factor_scores = {
            "RSI": 0.8,
            "PE": 0.7,
            "sentiment_score": 0.9
        }
        composite_score = 0.8
        
        confidence = self.generator._calculate_confidence(factor_scores, composite_score)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # 所有因子都是正向的，应该有较高置信度

    def test_calculate_confidence_mixed_signals(self):
        """测试混合信号的置信度计算"""
        factor_scores = {
            "RSI": 0.8,
            "PE": -0.7,  # 相反方向
            "sentiment_score": 0.9
        }
        composite_score = 0.3
        
        confidence = self.generator._calculate_confidence(factor_scores, composite_score)
        
        assert 0.0 <= confidence <= 1.0
        # 由于信号方向不一致，置信度应该较低
        assert confidence < 0.8

    def test_calculate_confidence_empty_scores(self):
        """测试空因子评分的置信度计算"""
        confidence = self.generator._calculate_confidence({}, 0.5)
        assert confidence == 0.0

    def test_apply_filters_low_confidence(self):
        """测试低置信度信号过滤"""
        # 创建一个低置信度的买入信号
        original_signal = TradingSignal(
            signal_type="BUY",
            strength=0.8,
            position_size=0.5,
            confidence=0.2,  # 低置信度
            timestamp=self.timestamp,
            composite_score=0.7,
            stock_code=self.stock_code,
            factor_scores={"RSI": 0.7}
        )
        
        filtered_signal = self.generator.apply_filters(original_signal)
        
        assert filtered_signal.signal_type == "HOLD"
        assert filtered_signal.strength == 0.0
        assert filtered_signal.position_size == 0.0
        assert filtered_signal.confidence == 0.2  # 置信度保持不变

    def test_apply_filters_weak_signal(self):
        """测试弱信号过滤"""
        # 创建一个弱强度的买入信号
        original_signal = TradingSignal(
            signal_type="BUY",
            strength=0.15,  # 弱信号
            position_size=0.1,
            confidence=0.8,
            timestamp=self.timestamp,
            composite_score=0.7,
            stock_code=self.stock_code,
            factor_scores={"RSI": 0.7}
        )
        
        filtered_signal = self.generator.apply_filters(original_signal)
        
        assert filtered_signal.signal_type == "HOLD"
        assert filtered_signal.strength == 0.0
        assert filtered_signal.position_size == 0.0

    def test_apply_filters_strong_signal(self):
        """测试强信号通过过滤"""
        # 创建一个强信号
        original_signal = TradingSignal(
            signal_type="BUY",
            strength=0.8,
            position_size=0.5,
            confidence=0.8,
            timestamp=self.timestamp,
            composite_score=0.7,
            stock_code=self.stock_code,
            factor_scores={"RSI": 0.7}
        )
        
        filtered_signal = self.generator.apply_filters(original_signal)
        
        # 强信号应该保持不变
        assert filtered_signal.signal_type == "BUY"
        assert filtered_signal.strength == 0.8
        assert filtered_signal.position_size == 0.5

    def test_calculate_position_size_hold_signal(self):
        """测试持有信号的仓位计算"""
        hold_signal = TradingSignal(
            signal_type="HOLD",
            strength=0.0,
            position_size=0.0,
            confidence=0.5,
            timestamp=self.timestamp,
            composite_score=0.0,
            stock_code=self.stock_code,
            factor_scores={}
        )
        
        position = self.generator.calculate_position_size(hold_signal)
        assert position == 0.0

    def test_calculate_position_size_with_risk_config(self):
        """测试带风险配置的仓位计算"""
        buy_signal = TradingSignal(
            signal_type="BUY",
            strength=0.8,
            position_size=0.8,
            confidence=0.9,
            timestamp=self.timestamp,
            composite_score=0.7,
            stock_code=self.stock_code,
            factor_scores={"RSI": 0.7}
        )
        
        risk_config = {
            'max_position': 0.5,
            'min_confidence': 0.3,
            'risk_multiplier': 0.8
        }
        
        position = self.generator.calculate_position_size(buy_signal, risk_config)
        
        # 应该受到最大仓位限制
        assert position <= 0.5
        assert position > 0

    def test_calculate_position_size_low_confidence_adjustment(self):
        """测试低置信度的仓位调整"""
        buy_signal = TradingSignal(
            signal_type="BUY",
            strength=0.8,
            position_size=0.8,
            confidence=0.2,  # 低置信度
            timestamp=self.timestamp,
            composite_score=0.7,
            stock_code=self.stock_code,
            factor_scores={"RSI": 0.7}
        )
        
        risk_config = {
            'max_position': 1.0,
            'min_confidence': 0.3,
            'risk_multiplier': 1.0
        }
        
        position = self.generator.calculate_position_size(buy_signal, risk_config)
        
        # 低置信度应该使用最小置信度进行调整
        expected_position = 0.8 * 0.3 * 1.0  # base_position * min_confidence * risk_multiplier
        assert abs(position - expected_position) < 1e-6

    def test_end_to_end_signal_generation(self):
        """测试端到端信号生成流程"""
        # 完整的信号生成流程测试
        signal = self.generator.generate_signals(
            self.factor_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        # 验证信号的完整性
        assert signal.signal_type in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= signal.strength <= 1.0
        assert 0.0 <= signal.position_size <= 1.0
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.stock_code == self.stock_code
        assert signal.timestamp == self.timestamp
        assert signal.factor_scores is not None
        assert isinstance(signal.composite_score, float)
        
        # 应用过滤器
        filtered_signal = self.generator.apply_filters(signal)
        
        # 计算最终仓位
        final_position = self.generator.calculate_position_size(filtered_signal)
        
        assert isinstance(final_position, float)
        assert final_position >= 0.0

    def test_signal_consistency(self):
        """测试信号生成的一致性"""
        # 相同输入应该产生相同输出
        signal1 = self.generator.generate_signals(
            self.factor_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        signal2 = self.generator.generate_signals(
            self.factor_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        assert signal1.signal_type == signal2.signal_type
        assert abs(signal1.strength - signal2.strength) < 1e-6
        assert abs(signal1.composite_score - signal2.composite_score) < 1e-6
        assert abs(signal1.confidence - signal2.confidence) < 1e-6

    @pytest.mark.parametrize("factor_data,expected_type", [
        ({"RSI": 3.0, "PE": 3.0, "sentiment_score": 3.0}, "BUY"),
        ({"RSI": -3.0, "PE": -3.0, "sentiment_score": -3.0}, "SELL"),
        ({"RSI": 0.0, "PE": 0.0, "sentiment_score": 0.0}, "HOLD"),
        ({"RSI": 0.3, "PE": -0.2, "sentiment_score": 0.1}, "HOLD"),
    ])
    def test_signal_generation_scenarios(self, factor_data, expected_type):
        """测试不同场景下的信号生成"""
        signal = self.generator.generate_signals(
            factor_data,
            self.factor_combination,
            self.stock_code,
            self.timestamp
        )
        
        assert signal.signal_type == expected_type