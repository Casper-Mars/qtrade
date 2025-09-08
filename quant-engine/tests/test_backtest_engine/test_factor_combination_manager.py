"""因子组合管理器测试模块

测试因子组合管理器的核心功能，包括：
- 配置创建、更新、删除、查询
- 配置验证
- 权重管理
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.backtest_engine.dao.factor_combination_dao import FactorCombinationDAO
from src.backtest_engine.models.factor_combination import (
    FactorCombination,
    FactorConfig,
    FactorType,
    ValidationResult,
)
from src.backtest_engine.services.factor_combination_manager import (
    ConfigValidator,
    FactorCombinationManager,
)


class TestConfigValidator:
    """配置验证器测试类"""

    @pytest.fixture
    def validator(self):
        """创建配置验证器实例"""
        return ConfigValidator()

    @pytest.fixture
    def valid_factor_config(self):
        """创建有效的因子配置"""
        return FactorConfig(
            name="rsi",
            factor_type=FactorType.TECHNICAL,
            weight=0.5,
            is_active=True
        )

    @pytest.fixture
    def valid_combination(self, valid_factor_config):
        """创建有效的因子组合"""
        factor1 = FactorConfig(
            name="rsi",
            factor_type=FactorType.TECHNICAL,
            weight=0.6,
            is_active=True
        )
        factor2 = FactorConfig(
            name="pe_ratio",
            factor_type=FactorType.FUNDAMENTAL,
            weight=0.4,
            is_active=True
        )
        return FactorCombination(
            name="测试组合",
            description="测试用的因子组合",
            factors=[factor1, factor2]
        )

    @pytest.mark.asyncio
    async def test_validate_config_success(self, validator, valid_factor_config):
        """测试因子配置验证成功"""
        result = await validator.validate_config(valid_factor_config)
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_config_empty_name(self, validator):
        """测试因子名称为空的验证"""
        # Pydantic会在创建时验证，所以我们期望抛出ValidationError
        with pytest.raises(ValidationError):
            FactorConfig(
                name="",
                factor_type=FactorType.TECHNICAL,
                weight=0.5,
                is_active=True
            )

    @pytest.mark.asyncio
    async def test_validate_config_invalid_weight(self, validator):
        """测试无效权重的验证"""
        # Pydantic会在创建时验证，所以我们期望抛出ValidationError
        with pytest.raises(ValidationError):
            FactorConfig(
                name="rsi",
                factor_type=FactorType.TECHNICAL,
                weight=1.5,  # 超出范围
                is_active=True
            )

    @pytest.mark.asyncio
    async def test_validate_weights_success(self, validator):
        """测试权重验证成功"""
        weights = {"rsi": 0.6, "macd": 0.4}
        result = await validator.validate_weights(weights)
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_weights_sum_not_one(self, validator):
        """测试权重总和不为1的验证"""
        weights = {"rsi": 0.6, "macd": 0.5}  # 总和为1.1
        result = await validator.validate_weights(weights)
        assert not result.is_valid
        assert "权重总和必须等于1.0" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_weights_empty(self, validator):
        """测试空权重配置的验证"""
        weights = {}
        result = await validator.validate_weights(weights)
        assert not result.is_valid
        assert "权重配置不能为空" in result.errors

    @pytest.mark.asyncio
    async def test_validate_combination_success(self, validator, valid_combination):
        """测试因子组合验证成功"""
        result = await validator.validate_combination(valid_combination)
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_combination_empty_name(self, validator, valid_combination):
        """测试组合名称为空的验证"""
        valid_combination.name = ""
        result = await validator.validate_combination(valid_combination)
        assert not result.is_valid
        assert "组合名称不能为空" in result.errors

    @pytest.mark.asyncio
    async def test_validate_combination_no_factors(self, validator):
        """测试无因子的组合验证"""
        # Pydantic会在创建时验证，所以我们期望抛出ValidationError
        with pytest.raises(ValidationError):
            FactorCombination(
                name="空组合",
                description="无因子的组合",
                factors=[]
            )

    @pytest.mark.asyncio
    async def test_validate_combination_duplicate_factors(self, validator):
        """测试重复因子名称的验证"""
        factor1 = FactorConfig(
            name="rsi",
            factor_type=FactorType.TECHNICAL,
            weight=0.5,
            is_active=True
        )
        factor2 = FactorConfig(
            name="rsi",  # 重复名称
            factor_type=FactorType.TECHNICAL,
            weight=0.5,
            is_active=True
        )
        # Pydantic会在创建时验证，所以我们期望抛出ValidationError
        with pytest.raises(ValidationError):
            FactorCombination(
                name="重复因子组合",
                description="包含重复因子的组合",
                factors=[factor1, factor2]
            )

    def test_normalize_weights_success(self, validator):
        """测试权重标准化成功"""
        weights = {"rsi": 0.6, "macd": 0.8}  # 总和为1.4
        normalized = validator.normalize_weights(weights)
        assert abs(sum(normalized.values()) - 1.0) < 0.001
        assert abs(normalized["rsi"] - 0.6/1.4) < 0.001
        assert abs(normalized["macd"] - 0.8/1.4) < 0.001

    def test_normalize_weights_zero_total(self, validator):
        """测试总权重为0的标准化"""
        weights = {"rsi": 0.0, "macd": 0.0}
        normalized = validator.normalize_weights(weights)
        assert abs(sum(normalized.values()) - 1.0) < 0.001
        assert normalized["rsi"] == 0.5
        assert normalized["macd"] == 0.5


class TestFactorCombinationManager:
    """因子组合管理器测试类"""

    @pytest.fixture
    def mock_validator(self):
        """创建模拟的配置验证器"""
        validator = MagicMock(spec=ConfigValidator)
        validator.validate_combination = AsyncMock(return_value=ValidationResult(is_valid=True))
        validator.validate_weights = AsyncMock(return_value=ValidationResult(is_valid=True))
        validator.normalize_weights = MagicMock(return_value={"rsi": 0.5, "macd": 0.5})
        return validator

    @pytest.fixture
    def mock_dao(self):
        """创建模拟的数据访问对象"""
        dao = MagicMock(spec=FactorCombinationDAO)
        dao.save_config = AsyncMock(return_value="test_config_id")
        dao.get_config = AsyncMock(return_value=None)
        dao.update_config = AsyncMock(return_value=True)
        dao.delete_config = AsyncMock(return_value=True)
        return dao

    @pytest.fixture
    def manager(self, mock_validator, mock_dao):
        """创建因子组合管理器实例"""
        return FactorCombinationManager(validator=mock_validator, dao=mock_dao)

    @pytest.fixture
    def valid_combination(self):
        """创建有效的因子组合"""
        factor1 = FactorConfig(
            name="rsi",
            factor_type=FactorType.TECHNICAL,
            weight=0.6,
            is_active=True
        )
        factor2 = FactorConfig(
            name="pe_ratio",
            factor_type=FactorType.FUNDAMENTAL,
            weight=0.4,
            is_active=True
        )
        return FactorCombination(
            name="测试组合",
            description="测试用的因子组合",
            factors=[factor1, factor2]
        )

    @pytest.mark.asyncio
    async def test_create_combination_success(self, manager, mock_validator, mock_dao, valid_combination):
        """测试创建因子组合成功"""
        config_id = await manager.create_combination(valid_combination)

        assert config_id == "test_config_id"
        mock_validator.validate_combination.assert_called_once_with(valid_combination)
        mock_dao.save_config.assert_called_once_with(valid_combination)

    @pytest.mark.asyncio
    async def test_create_combination_validation_failed(self, manager, mock_validator, valid_combination):
        """测试创建因子组合验证失败"""
        # 设置验证失败
        validation_result = ValidationResult(is_valid=False)
        validation_result.add_error("测试错误")
        mock_validator.validate_combination.return_value = validation_result

        with pytest.raises(ValueError, match="配置验证失败"):
            await manager.create_combination(valid_combination)

    @pytest.mark.asyncio
    async def test_get_combination_success(self, manager, mock_dao, valid_combination):
        """测试获取因子组合成功"""
        mock_dao.get_config.return_value = valid_combination

        result = await manager.get_combination("test_config_id")

        assert result == valid_combination
        mock_dao.get_config.assert_called_once_with("test_config_id")

    @pytest.mark.asyncio
    async def test_get_combination_not_found(self, manager, mock_dao):
        """测试获取不存在的因子组合"""
        mock_dao.get_config.return_value = None

        result = await manager.get_combination("nonexistent_id")

        assert result is None
        mock_dao.get_config.assert_called_once_with("nonexistent_id")

    @pytest.mark.asyncio
    async def test_update_combination_success(self, manager, mock_validator, mock_dao, valid_combination):
        """测试更新因子组合成功"""
        result = await manager.update_combination("test_config_id", valid_combination)

        assert result is True
        mock_validator.validate_combination.assert_called_once_with(valid_combination)
        mock_dao.update_config.assert_called_once_with("test_config_id", valid_combination)

    @pytest.mark.asyncio
    async def test_update_combination_validation_failed(self, manager, mock_validator, valid_combination):
        """测试更新因子组合验证失败"""
        # 设置验证失败
        validation_result = ValidationResult(is_valid=False)
        validation_result.add_error("测试错误")
        mock_validator.validate_combination.return_value = validation_result

        with pytest.raises(ValueError, match="配置验证失败"):
            await manager.update_combination("test_config_id", valid_combination)

    @pytest.mark.asyncio
    async def test_delete_combination_success(self, manager, mock_dao):
        """测试删除因子组合成功"""
        result = await manager.delete_combination("test_config_id")

        assert result is True
        mock_dao.delete_config.assert_called_once_with("test_config_id")

    @pytest.mark.asyncio
    async def test_validate_combination_config(self, manager, mock_validator, valid_combination):
        """测试验证因子组合配置"""
        result = await manager.validate_combination_config(valid_combination)

        assert result.is_valid
        mock_validator.validate_combination.assert_called_once_with(valid_combination)

    @pytest.mark.asyncio
    async def test_validate_weights_config(self, manager, mock_validator):
        """测试验证权重配置"""
        weights = {"rsi": 0.6, "macd": 0.4}
        result = await manager.validate_weights_config(weights)

        assert result.is_valid
        mock_validator.validate_weights.assert_called_once_with(weights)

    def test_normalize_weights(self, manager, mock_validator):
        """测试标准化权重"""
        weights = {"rsi": 0.6, "macd": 0.8}
        result = manager.normalize_weights(weights)

        assert result == {"rsi": 0.5, "macd": 0.5}
        mock_validator.normalize_weights.assert_called_once_with(weights)
