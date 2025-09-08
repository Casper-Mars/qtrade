"""交易信号生成器

本模块实现交易信号生成器，基于因子组合生成交易信号。
主要功能：
- 基于因子数据和权重配置生成交易信号
- 计算因子综合评分
- 根据评分阈值生成买卖信号
- 支持信号过滤和优化
"""


from ..models.backtest_models import BacktestFactorConfig, TradingSignal


class SignalGenerator:
    """交易信号生成器"""

    def __init__(self, default_threshold_config: dict | None = None):
        """初始化信号生成器

        Args:
            default_threshold_config: 默认信号阈值配置
        """
        self.default_threshold_config = default_threshold_config or {
            'buy_threshold': 0.6,    # 买入信号阈值
            'sell_threshold': -0.6,  # 卖出信号阈值
            'min_strength': 0.1,     # 最小信号强度
            'max_position_size': 1.0  # 最大仓位大小
        }

    def generate_signals(
        self,
        factor_data: dict,
        factor_combination: BacktestFactorConfig,
        stock_code: str,
        timestamp: str,
        threshold_config: dict | None = None
    ) -> TradingSignal:
        """生成交易信号，基于动态因子组合权重

        Args:
            factor_data: 因子数据字典，包含各个因子的值
            factor_combination: 因子组合配置，包含因子权重
            stock_code: 股票代码
            timestamp: 时间戳
            threshold_config: 信号阈值配置

        Returns:
            交易信号对象
        """
        # 使用传入的阈值配置或默认配置
        thresholds = threshold_config or self.default_threshold_config

        # 1. 计算因子综合评分
        composite_score = self._calculate_composite_score(factor_data, factor_combination)

        # 2. 计算各因子评分（用于记录和分析）
        factor_scores = self._calculate_factor_scores(factor_data, factor_combination)

        # 3. 根据评分生成交易信号
        signal = self._generate_signal_from_score(
            composite_score,
            factor_scores,
            stock_code,
            timestamp,
            thresholds
        )

        return signal

    def _calculate_composite_score(
        self,
        factor_data: dict,
        factor_combination: BacktestFactorConfig
    ) -> float:
        """计算因子综合评分

        根据因子组合中的权重配置，计算加权综合评分

        Args:
            factor_data: 因子数据字典
            factor_combination: 因子组合配置

        Returns:
            综合评分
        """
        composite_score = 0.0
        total_weight = 0.0

        # 遍历因子组合中的所有因子
        for factor_item in factor_combination.factors:
            factor_name = factor_item.factor_name
            factor_weight = factor_item.weight

            if factor_name in factor_data:
                factor_value = factor_data[factor_name]
                # 标准化因子值到[-1, 1]范围
                normalized_value = self._normalize_factor_value(factor_value)
                composite_score += normalized_value * factor_weight
                total_weight += factor_weight

        # 如果有有效权重，则按权重归一化
        if total_weight > 0:
            composite_score = composite_score / total_weight

        return composite_score

    def _calculate_factor_scores(
        self,
        factor_data: dict,
        factor_combination: BacktestFactorConfig
    ) -> dict[str, float]:
        """计算各因子评分

        Args:
            factor_data: 因子数据字典
            factor_combination: 因子组合配置

        Returns:
            各因子评分字典
        """
        factor_scores = {}

        for factor_item in factor_combination.factors:
            factor_name = factor_item.factor_name
            if factor_name in factor_data:
                factor_value = factor_data[factor_name]
                # 标准化因子值
                normalized_value = self._normalize_factor_value(factor_value)
                factor_scores[factor_name] = normalized_value

        return factor_scores

    def _normalize_factor_value(self, factor_value: float) -> float:
        """标准化因子值到[-1, 1]范围

        使用tanh函数进行标准化，保持数值的相对关系

        Args:
            factor_value: 原始因子值

        Returns:
            标准化后的因子值
        """
        import math

        # 使用tanh函数将值映射到[-1, 1]范围
        # 对于大部分因子值，这能提供良好的标准化效果
        return math.tanh(factor_value)

    def _generate_signal_from_score(
        self,
        composite_score: float,
        factor_scores: dict[str, float],
        stock_code: str,
        timestamp: str,
        threshold_config: dict
    ) -> TradingSignal:
        """根据综合评分生成交易信号

        Args:
            composite_score: 因子综合评分
            factor_scores: 各因子评分
            stock_code: 股票代码
            timestamp: 时间戳
            threshold_config: 阈值配置

        Returns:
            交易信号对象
        """
        buy_threshold = threshold_config.get('buy_threshold', 0.6)
        sell_threshold = threshold_config.get('sell_threshold', -0.6)
        min_strength = threshold_config.get('min_strength', 0.1)
        max_position_size = threshold_config.get('max_position_size', 1.0)

        # 根据综合评分确定信号类型
        if composite_score >= buy_threshold:
            signal_type = 'BUY'
            # 信号强度基于评分超过阈值的程度
            strength = min(abs(composite_score), 1.0)
        elif composite_score <= sell_threshold:
            signal_type = 'SELL'
            # 信号强度基于评分超过阈值的程度
            strength = min(abs(composite_score), 1.0)
        else:
            signal_type = 'HOLD'
            strength = 0.0

        # 确保信号强度不低于最小值
        if signal_type != 'HOLD' and strength < min_strength:
            signal_type = 'HOLD'
            strength = 0.0

        # 计算建议仓位大小
        if signal_type == 'HOLD':
            position_size = 0.0
        else:
            # 仓位大小基于信号强度，但不超过最大仓位
            position_size = min(strength * max_position_size, max_position_size)

        # 计算信号置信度（基于因子数据的完整性和评分的一致性）
        confidence = self._calculate_confidence(factor_scores, composite_score)

        return TradingSignal(
            signal_type=signal_type,
            strength=strength,
            position_size=position_size,
            confidence=confidence,
            timestamp=timestamp,
            composite_score=composite_score,
            stock_code=stock_code,
            factor_scores=factor_scores
        )

    def _calculate_confidence(
        self,
        factor_scores: dict[str, float],
        composite_score: float
    ) -> float:
        """计算信号置信度

        基于因子数据的完整性和评分的一致性计算置信度

        Args:
            factor_scores: 各因子评分
            composite_score: 综合评分

        Returns:
            信号置信度 [0, 1]
        """
        if not factor_scores:
            return 0.0

        # 基础置信度：基于因子数据的完整性
        base_confidence = min(len(factor_scores) / 10.0, 1.0)  # 假设10个因子为满分

        # 一致性置信度：评分方向的一致性
        positive_scores = sum(1 for score in factor_scores.values() if score > 0)
        negative_scores = sum(1 for score in factor_scores.values() if score < 0)
        total_scores = len(factor_scores)

        if total_scores > 0:
            # 计算评分方向的一致性
            consistency = max(positive_scores, negative_scores) / total_scores
        else:
            consistency = 0.0

        # 强度置信度：基于综合评分的绝对值
        strength_confidence = min(abs(composite_score), 1.0)

        # 综合置信度
        confidence = (base_confidence * 0.3 + consistency * 0.4 + strength_confidence * 0.3)

        return min(confidence, 1.0)

    def apply_filters(self, signal: TradingSignal) -> TradingSignal:
        """应用信号过滤器

        实现基于阈值的信号过滤机制

        Args:
            signal: 原始交易信号

        Returns:
            过滤后的交易信号
        """
        # 低置信度过滤
        if signal.confidence < 0.3:
            return TradingSignal(
                signal_type='HOLD',
                strength=0.0,
                position_size=0.0,
                confidence=signal.confidence,
                timestamp=signal.timestamp,
                composite_score=signal.composite_score,
                stock_code=signal.stock_code,
                factor_scores=signal.factor_scores
            )

        # 弱信号过滤
        if signal.strength < 0.2 and signal.signal_type != 'HOLD':
            return TradingSignal(
                signal_type='HOLD',
                strength=0.0,
                position_size=0.0,
                confidence=signal.confidence,
                timestamp=signal.timestamp,
                composite_score=signal.composite_score,
                stock_code=signal.stock_code,
                factor_scores=signal.factor_scores
            )

        return signal

    def calculate_position_size(
        self,
        signal: TradingSignal,
        risk_config: dict | None = None
    ) -> float:
        """计算仓位大小

        实现仓位大小计算逻辑，考虑风险控制

        Args:
            signal: 交易信号
            risk_config: 风险控制配置

        Returns:
            调整后的仓位大小
        """
        if signal.signal_type == 'HOLD':
            return 0.0

        risk_config = risk_config or {
            'max_position': 1.0,
            'min_confidence': 0.3,
            'risk_multiplier': 1.0
        }

        # 基础仓位大小
        base_position = signal.position_size

        # 置信度调整
        confidence_multiplier = max(signal.confidence, risk_config['min_confidence'])

        # 风险调整
        risk_multiplier = risk_config.get('risk_multiplier', 1.0)

        # 计算最终仓位
        final_position = base_position * confidence_multiplier * risk_multiplier

        # 确保不超过最大仓位
        max_position = float(risk_config.get('max_position', 1.0))
        final_position = min(final_position, max_position)

        return float(final_position)
