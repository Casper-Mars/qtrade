"""因子组合管理服务

本模块提供因子组合管理的完整功能，包括：
- 因子组合配置管理
- 配置验证器
- 配置存储管理器
- 权重配置管理
"""

from decimal import Decimal

from ...dao.factor_combination_dao import FactorCombinationDAO
from ..models.factor_combination import (
    FactorCombination,
    FactorConfig,
    ValidationResult,
)


class ConfigValidator:
    """配置验证器

    负责验证因子组合配置的有效性，包括权重验证、因子配置验证等。
    """

    def __init__(self) -> None:
        """初始化配置验证器"""
        self.weight_tolerance = Decimal('0.001')  # 权重误差容忍度

    async def validate_config(self, config: FactorConfig) -> ValidationResult:
        """验证单个因子配置

        Args:
            config: 因子配置对象

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)

        # 验证因子名称
        if not config.name or not config.name.strip():
            result.add_error("因子名称不能为空")

        # 验证权重范围
        if config.weight < 0 or config.weight > 1:
            result.add_error(f"因子权重必须在0-1之间，当前值：{config.weight}")

        # 验证因子类型
        if not config.factor_type:
            result.add_error("因子类型不能为空")

        # 检查权重精度
        if config.weight == 0:
            result.add_warning("因子权重为0，该因子将不会对组合产生影响")

        return result

    async def validate_weights(self, weights: dict[str, float]) -> ValidationResult:
        """验证权重配置

        Args:
            weights: 权重字典，key为因子名称，value为权重值

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)

        if not weights:
            result.add_error("权重配置不能为空")
            return result

        # 验证单个权重范围
        for factor_name, weight in weights.items():
            if weight < 0 or weight > 1:
                result.add_error(f"因子 '{factor_name}' 的权重必须在0-1之间，当前值：{weight}")

            if weight == 0:
                result.add_warning(f"因子 '{factor_name}' 的权重为0，将不会对组合产生影响")

        # 验证权重总和
        total_weight = Decimal(str(sum(weights.values())))
        if abs(total_weight - 1) > self.weight_tolerance:
            result.add_error(f"权重总和必须等于1.0，当前总和：{total_weight}")

        # 检查权重分布
        max_weight = max(weights.values())
        if max_weight > 0.8:
            result.add_warning(f"存在权重过高的因子（{max_weight}），可能影响组合分散性")

        # 检查权重分布均匀性
        if len(weights) > 1:
            avg_weight = 1.0 / len(weights)
            highly_concentrated = [name for name, weight in weights.items()
                                 if weight > avg_weight * 2]
            if highly_concentrated:
                result.add_warning(f"权重高度集中的因子：{', '.join(highly_concentrated)}")

        return result

    async def validate_combination(self, combination: FactorCombination) -> ValidationResult:
        """验证因子组合配置

        Args:
            combination: 因子组合对象

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)

        # 验证组合名称
        if not combination.name or not combination.name.strip():
            result.add_error("组合名称不能为空")

        # 验证因子数量
        if not combination.factors:
            result.add_error("因子组合至少需要包含一个因子")
            return result

        # 验证每个因子配置
        for factor in combination.factors:
            factor_result = await self.validate_config(factor)
            if not factor_result.is_valid:
                result.errors.extend([f"因子 '{factor.name}': {error}"
                                    for error in factor_result.errors])
                result.is_valid = False
            result.warnings.extend([f"因子 '{factor.name}': {warning}"
                                  for warning in factor_result.warnings])

        # 验证因子名称唯一性
        factor_names = [factor.name for factor in combination.factors]
        if len(factor_names) != len(set(factor_names)):
            result.add_error("因子组合中不能包含重复的因子名称")

        # 验证权重总和
        total_weight = sum(factor.weight for factor in combination.factors)
        if abs(float(total_weight) - 1) > float(self.weight_tolerance):
            result.add_error(f"因子权重总和必须等于1.0，当前总和：{total_weight}")

        # 检查非活跃因子
        inactive_factors = [f.name for f in combination.factors if not f.is_active]
        if inactive_factors:
            result.add_warning(f"包含非活跃因子：{', '.join(inactive_factors)}")

        # 检查因子类型分布
        factor_types = [f.factor_type for f in combination.factors]
        unique_types = set(factor_types)
        if len(unique_types) == 1:
            result.add_warning("组合中所有因子类型相同，建议增加因子类型多样性")

        return result

    def normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        """标准化权重配置

        将权重总和标准化为1.0

        Args:
            weights: 原始权重字典

        Returns:
            Dict[str, float]: 标准化后的权重字典
        """
        if not weights:
            return weights

        total_weight = sum(weights.values())
        if total_weight == 0:
            # 如果总权重为0，则平均分配
            equal_weight = 1.0 / len(weights)
            return dict.fromkeys(weights.keys(), equal_weight)

        # 按比例标准化
        return {name: weight / total_weight for name, weight in weights.items()}





class FactorCombinationManager:
    """因子组合管理器

    提供因子组合管理的完整功能，包括配置创建、更新、删除、查询等操作。
    集成配置验证器和存储管理器。
    """

    def __init__(self, validator: ConfigValidator | None = None,
                 dao: FactorCombinationDAO | None = None):
        """初始化因子组合管理器

        Args:
            validator: 配置验证器，如果为None则创建默认实例
            dao: 因子组合数据访问对象，如果为None则创建默认实例
        """
        self.validator = validator or ConfigValidator()
        self.dao = dao or FactorCombinationDAO()

    async def create_combination(self, combination: FactorCombination) -> str:
        """创建因子组合配置

        Args:
            combination: 因子组合配置对象

        Returns:
            str: 配置ID

        Raises:
            ValueError: 当配置验证失败时
        """
        # 验证配置
        validation_result = await self.validator.validate_combination(combination)
        if not validation_result.is_valid:
            raise ValueError(f"配置验证失败: {'; '.join(validation_result.errors)}")

        # 保存配置
        config_id = await self.dao.save_config(combination)
        return config_id

    async def get_combination(self, config_id: str) -> FactorCombination | None:
        """获取因子组合配置

        Args:
            config_id: 配置ID

        Returns:
            Optional[FactorCombination]: 因子组合配置对象
        """
        return await self.dao.get_config(config_id)

    async def update_combination(self, config_id: str,
                               combination: FactorCombination) -> bool:
        """更新因子组合配置

        Args:
            config_id: 配置ID
            combination: 新的因子组合配置对象

        Returns:
            bool: 更新是否成功

        Raises:
            ValueError: 当配置验证失败时
        """
        # 验证配置
        validation_result = await self.validator.validate_combination(combination)
        if not validation_result.is_valid:
            raise ValueError(f"配置验证失败: {'; '.join(validation_result.errors)}")

        # 更新配置
        return await self.dao.update_config(config_id, combination)

    async def delete_combination(self, config_id: str) -> bool:
        """删除因子组合配置

        Args:
            config_id: 配置ID

        Returns:
            bool: 删除是否成功
        """
        return await self.dao.delete_config(config_id)

    async def validate_combination_config(self,
                                        combination: FactorCombination) -> ValidationResult:
        """验证因子组合配置

        Args:
            combination: 因子组合配置对象

        Returns:
            ValidationResult: 验证结果
        """
        return await self.validator.validate_combination(combination)

    async def validate_weights_config(self, weights: dict[str, float]) -> ValidationResult:
        """验证权重配置

        Args:
            weights: 权重字典

        Returns:
            ValidationResult: 验证结果
        """
        return await self.validator.validate_weights(weights)

    def normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        """标准化权重配置

        Args:
            weights: 原始权重字典

        Returns:
            Dict[str, float]: 标准化后的权重字典
        """
        return self.validator.normalize_weights(weights)
