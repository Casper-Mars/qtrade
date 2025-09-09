"""因子组合管理服务单元测试

本模块测试因子组合管理服务的所有功能，包括：
- ConfigValidator 配置验证器测试
- FactorCombinationManager 因子组合管理器测试
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from src.backtest_engine.models.factor_combination import (
    FactorCombination,
    FactorCombinationData,
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

    def setup_method(self) -> None:
        """测试前置设置"""
        self.validator = ConfigValidator()

    @pytest.mark.asyncio
    async def test_validate_config_success(self) -> None:
        """测试因子配置验证成功场景"""
        # 准备测试数据
        config = FactorConfig(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('0.5'),
            parameters={"period": 20},
            is_active=True,
            description="测试因子"
        )

        # 执行测试
        result = await self.validator.validate_config(config)

        # 验证结果
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_empty_name(self) -> None:
        """测试因子名称为空的验证"""
        # 准备测试数据 - 使用model_construct绕过Pydantic验证
        config = FactorConfig.model_construct(
            name="",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('0.5'),
            parameters={},
            is_active=True
        )

        # 执行测试
        result = await self.validator.validate_config(config)

        # 验证结果
        assert result.is_valid is False
        assert "因子名称不能为空" in result.errors

    @pytest.mark.asyncio
    async def test_validate_config_invalid_weight(self) -> None:
        """测试权重超出范围的验证"""
        # 准备测试数据 - 使用model_construct绕过Pydantic验证
        config = FactorConfig.model_construct(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('1.5'),  # 超出范围
            parameters={},
            is_active=True
        )

        # 执行测试
        result = await self.validator.validate_config(config)

        # 验证结果
        assert result.is_valid is False
        assert "因子权重必须在0-1之间" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_config_zero_weight_warning(self) -> None:
        """测试权重为0的警告"""
        # 准备测试数据
        config = FactorConfig(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('0'),
            parameters={},
            is_active=True
        )

        # 执行测试
        result = await self.validator.validate_config(config)

        # 验证结果
        assert result.is_valid is True
        assert "因子权重为0，该因子将不会对组合产生影响" in result.warnings

    @pytest.mark.asyncio
    async def test_validate_weights_success(self) -> None:
        """测试权重配置验证成功场景"""
        # 准备测试数据
        weights = {
            "factor1": 0.4,
            "factor2": 0.3,
            "factor3": 0.3
        }

        # 执行测试
        result = await self.validator.validate_weights(weights)

        # 验证结果
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_weights_empty(self) -> None:
        """测试空权重配置验证"""
        # 准备测试数据
        weights = {}

        # 执行测试
        result = await self.validator.validate_weights(weights)

        # 验证结果
        assert result.is_valid is False
        assert "权重配置不能为空" in result.errors

    @pytest.mark.asyncio
    async def test_validate_weights_sum_not_one(self) -> None:
        """测试权重总和不等于1的验证"""
        # 准备测试数据
        weights = {
            "factor1": 0.4,
            "factor2": 0.3,
            "factor3": 0.2  # 总和为0.9
        }

        # 执行测试
        result = await self.validator.validate_weights(weights)

        # 验证结果
        assert result.is_valid is False
        assert "权重总和必须等于1.0" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_weights_high_concentration(self) -> None:
        """测试权重高度集中的警告"""
        # 准备测试数据
        weights = {
            "factor1": 0.9,
            "factor2": 0.1
        }

        # 执行测试
        result = await self.validator.validate_weights(weights)

        # 验证结果
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert "存在权重过高的因子" in result.warnings[0]
        if len(result.warnings) > 1:
            assert "权重高度集中的因子" in result.warnings[1]

    @pytest.mark.asyncio
    async def test_validate_combination_success(self) -> None:
        """测试因子组合验证成功场景"""
        # 准备测试数据
        factors = [
            FactorConfig(
                name="factor1",
                factor_type=FactorType.TECHNICAL,
                weight=Decimal('0.5'),
                parameters={},
                is_active=True
            ),
            FactorConfig(
                name="factor2",
                factor_type=FactorType.FUNDAMENTAL,
                weight=Decimal('0.5'),
                parameters={},
                is_active=True
            )
        ]

        combination = FactorCombination(
            id=uuid4(),
            name="test_combination",
            description="测试组合",
            factors=factors,
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 执行测试
        result = await self.validator.validate_combination(combination)

        # 验证结果
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_combination_empty_name(self) -> None:
        """测试组合名称为空的验证"""
        # 准备测试数据 -# 使用model_construct绕过Pydantic验证
        combination = FactorCombination.model_construct(
            id=uuid4(),
            name="",  # 空名称
            description="测试组合",
            factors=[],
            total_weight=Decimal('0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 执行测试
        result = await self.validator.validate_combination(combination)

        # 验证结果
        assert result.is_valid is False
        assert "组合名称不能为空" in result.errors

    @pytest.mark.asyncio
    async def test_validate_combination_no_factors(self) -> None:
        """测试无因子的组合验证"""
        # 准备测试数据 -# 使用model_construct绕过Pydantic验证
        combination = FactorCombination.model_construct(
            id=uuid4(),
            name="test_combination",
            description="测试组合",
            factors=[],  # 无因子
            total_weight=Decimal('0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 执行测试
        result = await self.validator.validate_combination(combination)

        # 验证结果
        assert result.is_valid is False
        assert "因子组合至少需要包含一个因子" in result.errors

    @pytest.mark.asyncio
    async def test_validate_combination_duplicate_names(self) -> None:
        """测试重复因子名称的验证"""
        # 准备测试数据
        factors = [
            FactorConfig(
                name="factor1",  # 重复名称
                factor_type=FactorType.TECHNICAL,
                weight=Decimal('0.5'),
                parameters={},
                is_active=True
            ),
            FactorConfig(
                name="factor1",  # 重复名称
                factor_type=FactorType.FUNDAMENTAL,
                weight=Decimal('0.5'),
                parameters={},
                is_active=True
            )
        ]

        combination = FactorCombination.model_construct(
            id=uuid4(),
            name="test_combination",
            description="测试组合",
            factors=factors,
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 执行测试
        result = await self.validator.validate_combination(combination)

        # 验证结果
        assert result.is_valid is False
        assert "因子组合中不能包含重复的因子名称" in result.errors

    def test_normalize_weights_success(self) -> None:
        """测试权重标准化成功场景"""
        # 准备测试数据
        weights = {
            "factor1": 0.4,
            "factor2": 0.6
        }

        # 执行测试
        normalized = self.validator.normalize_weights(weights)

        # 验证结果
        assert normalized == weights  # 已经标准化
        assert sum(normalized.values()) == 1.0

    def test_normalize_weights_need_normalization(self) -> None:
        """测试需要标准化的权重"""
        # 准备测试数据
        weights = {
            "factor1": 0.8,
            "factor2": 1.2  # 总和为2.0
        }

        # 执行测试
        normalized = self.validator.normalize_weights(weights)

        # 验证结果
        assert normalized["factor1"] == 0.4
        assert normalized["factor2"] == 0.6
        assert sum(normalized.values()) == 1.0

    def test_normalize_weights_zero_total(self) -> None:
        """测试总权重为0的标准化"""
        # 准备测试数据
        weights = {
            "factor1": 0.0,
            "factor2": 0.0
        }

        # 执行测试
        normalized = self.validator.normalize_weights(weights)

        # 验证结果
        assert normalized["factor1"] == 0.5
        assert normalized["factor2"] == 0.5
        assert sum(normalized.values()) == 1.0


class TestFactorCombinationManager:
    """因子组合管理器测试类"""

    def setup_method(self) -> None:
        """测试前置设置"""
        self.mock_validator = Mock(spec=ConfigValidator)
        self.mock_dao = AsyncMock()
        self.manager = FactorCombinationManager(
            validator=self.mock_validator,
            dao=self.mock_dao
        )

    @pytest.mark.asyncio
    async def test_create_combination_success(self) -> None:
        """测试创建因子组合成功场景"""
        # 准备测试数据
        stock_code = "000001"
        description = "测试组合"
        technical_factors = ["ma_5", "rsi_14"]
        fundamental_factors = ["pe_ratio"]
        sentiment_factors = ["news_sentiment"]
        factor_weights = {
            "ma_5": 0.3,
            "rsi_14": 0.2,
            "pe_ratio": 0.3,
            "news_sentiment": 0.2
        }

        # 设置mock返回值
        validation_result = ValidationResult(is_valid=True)
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)
        self.mock_dao.save_config = AsyncMock(return_value="test_config_id")

        # 执行测试
        result = await self.manager.create_combination(
            stock_code=stock_code,
            description=description,
            technical_factors=technical_factors,
            fundamental_factors=fundamental_factors,
            sentiment_factors=sentiment_factors,
            factor_weights=factor_weights
        )

        # 验证结果
        assert isinstance(result, FactorCombinationData)
        assert result.stock_code == stock_code
        assert result.description == description
        assert result.technical_factors == technical_factors
        assert result.fundamental_factors == fundamental_factors
        assert result.sentiment_factors == sentiment_factors
        assert result.factor_weights == factor_weights
        assert result.factor_count == 4
        assert result.config_id == "test_config_id"

        # 验证mock调用
        self.mock_validator.validate_weights.assert_called_once_with(factor_weights)
        self.mock_dao.save_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_combination_validation_failed(self) -> None:
        """测试创建因子组合验证失败场景"""
        # 准备测试数据
        factor_weights = {
            "factor1": 0.6,
            "factor2": 0.6  # 总和超过1
        }

        # 设置mock返回值
        validation_result = ValidationResult(is_valid=False)
        validation_result.add_error("权重总和超过1.0")
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="权重配置验证失败"):
            await self.manager.create_combination(
                stock_code="000001",
                factor_weights=factor_weights
            )

        # 验证mock调用
        self.mock_validator.validate_weights.assert_called_once_with(factor_weights)
        self.mock_dao.save_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_combination_dao_error(self) -> None:
        """测试创建因子组合DAO错误场景"""
        # 准备测试数据
        factor_weights = {"factor1": 1.0}

        # 设置mock返回值
        validation_result = ValidationResult(is_valid=True)
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)
        self.mock_dao.save_config = AsyncMock(side_effect=Exception("数据库错误"))

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="保存配置失败"):
            await self.manager.create_combination(
                stock_code="000001",
                factor_weights=factor_weights
            )

    @pytest.mark.asyncio
    async def test_get_combination_success(self) -> None:
        """测试获取因子组合成功场景"""
        # 准备测试数据
        config_id = "test_config_id"
        mock_combination = FactorCombination(
            id=uuid4(),
            name="000001",
            description="测试组合",
            factors=[
                FactorConfig(
                    name="ma_5",
                    factor_type=FactorType.TECHNICAL,
                    weight=Decimal('0.5'),
                    parameters={},
                    is_active=True
                ),
                FactorConfig(
                    name="pe_ratio",
                    factor_type=FactorType.FUNDAMENTAL,
                    weight=Decimal('0.5'),
                    parameters={},
                    is_active=True
                )
            ],
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 设置mock返回值
        self.mock_dao.get_config = AsyncMock(return_value=mock_combination)

        # 执行测试
        result = await self.manager.get_combination(config_id)

        # 验证结果
        assert result is not None
        assert isinstance(result, FactorCombinationData)
        assert result.config_id == config_id
        assert result.stock_code == "000001"
        assert result.technical_factors == ["ma_5"]
        assert result.fundamental_factors == ["pe_ratio"]
        assert result.factor_count == 2

        # 验证mock调用
        self.mock_dao.get_config.assert_called_once_with(config_id)

    @pytest.mark.asyncio
    async def test_get_combination_not_found(self) -> None:
        """测试获取不存在的因子组合"""
        # 准备测试数据
        config_id = "non_existent_id"

        # 设置mock返回值
        self.mock_dao.get_config = AsyncMock(return_value=None)

        # 执行测试
        result = await self.manager.get_combination(config_id)

        # 验证结果
        assert result is None

        # 验证mock调用
        self.mock_dao.get_config.assert_called_once_with(config_id)

    @pytest.mark.asyncio
    async def test_get_combination_dao_error(self) -> None:
        """测试获取因子组合DAO错误场景"""
        # 准备测试数据
        config_id = "test_config_id"

        # 设置mock返回值
        self.mock_dao.get_config = AsyncMock(side_effect=Exception("数据库错误"))

        # 执行测试
        result = await self.manager.get_combination(config_id)

        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_update_combination_success(self) -> None:
        """测试更新因子组合成功场景"""
        # 准备测试数据
        config_id = "test_config_id"
        update_data = {
            "description": "更新后的描述",
            "technical_factors": ["ma_10"],
            "fundamental_factors": ["pb_ratio"],
            "sentiment_factors": [],
            "factor_weights": {
                "ma_10": 0.6,
                "pb_ratio": 0.4
            }
        }

        # 创建有效的因子配置
        factor_config = FactorConfig(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('1.0'),
            parameters={},
            is_active=True
        )
        
        existing_combination = FactorCombination(
            id=uuid4(),
            name="000001",
            description="原始描述",
            factors=[factor_config],
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 设置mock返回值
        validation_result = ValidationResult(is_valid=True)
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)
        self.mock_dao.get_config = AsyncMock(return_value=existing_combination)
        self.mock_dao.update_config = AsyncMock(return_value=True)

        # 执行测试
        result = await self.manager.update_combination(config_id, update_data)

        # 验证结果
        assert result is not None
        assert isinstance(result, FactorCombinationData)
        assert result.config_id == config_id
        assert result.description == "更新后的描述"
        assert result.technical_factors == ["ma_10"]
        assert result.fundamental_factors == ["pb_ratio"]
        assert result.sentiment_factors == []
        assert result.factor_count == 2

        # 验证mock调用
        self.mock_validator.validate_weights.assert_called_once()
        self.mock_dao.get_config.assert_called_once_with(config_id)
        self.mock_dao.update_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_combination_not_found(self) -> None:
        """测试更新不存在的因子组合"""
        # 准备测试数据
        config_id = "non_existent_id"
        update_data = {"description": "新描述"}

        # 设置mock返回值
        self.mock_dao.get_config = AsyncMock(return_value=None)

        # 执行测试
        result = await self.manager.update_combination(config_id, update_data)

        # 验证结果
        assert result is None

        # 验证mock调用
        self.mock_dao.get_config.assert_called_once_with(config_id)
        self.mock_dao.update_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_combination_validation_failed(self) -> None:
        """测试更新因子组合验证失败场景"""
        # 准备测试数据
        config_id = "test_config_id"
        update_data = {
            "factor_weights": {
                "factor1": 0.8,
                "factor2": 0.8  # 总和超过1
            }
        }

        # 创建有效的因子配置
        factor_config = FactorConfig(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('1.0'),
            parameters={},
            is_active=True
        )
        
        existing_combination = FactorCombination(
            id=uuid4(),
            name="000001",
            description="原始描述",
            factors=[factor_config],
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 设置mock返回值
        validation_result = ValidationResult(is_valid=False)
        validation_result.add_error("权重总和超过1.0")
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)
        self.mock_dao.get_config = AsyncMock(return_value=existing_combination)

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="权重配置验证失败"):
            await self.manager.update_combination(config_id, update_data)

        # 验证mock调用
        self.mock_dao.update_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_combination_success(self) -> None:
        """测试删除因子组合成功场景"""
        # 准备测试数据
        config_id = "test_config_id"

        # 设置mock返回值
        self.mock_dao.delete_config = AsyncMock(return_value=True)

        # 执行测试
        result = await self.manager.delete_combination(config_id)

        # 验证结果
        assert result is True

        # 验证mock调用
        self.mock_dao.delete_config.assert_called_once_with(config_id)

    @pytest.mark.asyncio
    async def test_delete_combination_failed(self) -> None:
        """测试删除因子组合失败场景"""
        # 准备测试数据
        config_id = "test_config_id"

        # 设置mock返回值
        self.mock_dao.delete_config = AsyncMock(return_value=False)

        # 执行测试
        result = await self.manager.delete_combination(config_id)

        # 验证结果
        assert result is False

        # 验证mock调用
        self.mock_dao.delete_config.assert_called_once_with(config_id)

    @pytest.mark.asyncio
    async def test_validate_combination_config(self) -> None:
        """测试验证因子组合配置"""
        # 准备测试数据
        # 创建有效的因子配置
        factor_config = FactorConfig(
            name="test_factor",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('1.0'),
            parameters={},
            is_active=True
        )
        
        combination = FactorCombination(
            id=uuid4(),
            name="test_combination",
            description="测试组合",
            factors=[factor_config],
            total_weight=Decimal('1.0'),
            is_active=True,
            created_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        validation_result = ValidationResult(is_valid=True)
        self.mock_validator.validate_combination = AsyncMock(return_value=validation_result)

        # 执行测试
        result = await self.manager.validate_combination_config(combination)

        # 验证结果
        assert result == validation_result

        # 验证mock调用
        self.mock_validator.validate_combination.assert_called_once_with(combination)

    @pytest.mark.asyncio
    async def test_validate_weights_config(self) -> None:
        """测试验证权重配置"""
        # 准备测试数据
        weights = {"factor1": 0.5, "factor2": 0.5}
        validation_result = ValidationResult(is_valid=True)
        self.mock_validator.validate_weights = AsyncMock(return_value=validation_result)

        # 执行测试
        result = await self.manager.validate_weights_config(weights)

        # 验证结果
        assert result == validation_result

        # 验证mock调用
        self.mock_validator.validate_weights.assert_called_once_with(weights)

    def test_normalize_weights(self) -> None:
        """测试权重标准化"""
        # 准备测试数据
        weights = {"factor1": 0.8, "factor2": 1.2}
        expected_result = {"factor1": 0.4, "factor2": 0.6}
        self.mock_validator.normalize_weights = Mock(return_value=expected_result)

        # 执行测试
        result = self.manager.normalize_weights(weights)

        # 验证结果
        assert result == expected_result

        # 验证mock调用
        self.mock_validator.normalize_weights.assert_called_once_with(weights)

    def test_manager_with_default_dependencies(self) -> None:
        """测试使用默认依赖的管理器"""
        # 创建使用默认依赖的管理器
        manager = FactorCombinationManager()

        # 验证依赖注入
        assert manager.validator is not None
        assert isinstance(manager.validator, ConfigValidator)
        assert manager.dao is not None


if __name__ == "__main__":
    pytest.main([__file__])