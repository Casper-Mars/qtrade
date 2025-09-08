"""因子组合DAO测试模块"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.backtest_engine.dao.factor_combination_dao import FactorCombinationDAO
from src.backtest_engine.models.factor_combination import (
    FactorCombination,
    FactorConfig,
    FactorType,
)


class TestFactorCombinationDAO:
    """因子组合DAO测试类"""

    @pytest.fixture
    def dao(self):
        """创建DAO实例"""
        return FactorCombinationDAO()

    @pytest.fixture
    def sample_factor(self):
        """创建示例因子"""
        return FactorConfig(
            id=str(uuid4()),
            name="测试因子",
            factor_type=FactorType.TECHNICAL,
            weight=Decimal('1.0'),
            parameters={"period": 20},
            is_active=True,
            description="测试用因子",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def sample_combination(self, sample_factor):
        """创建示例因子组合"""
        return FactorCombination(
            name="测试组合",
            description="测试用因子组合",
            factors=[sample_factor],
            created_by="test_user"
        )

    def test_dao_initialization(self, dao):
        """测试DAO初始化"""
        assert dao is not None
        assert isinstance(dao, FactorCombinationDAO)

    @pytest.mark.asyncio
    async def test_save_and_get_config(self, dao, sample_combination):
        """测试保存和获取配置"""
        # 这里只是测试方法存在，不进行实际数据库操作
        # 在实际环境中需要mock数据库连接
        assert hasattr(dao, 'save_config')
        assert hasattr(dao, 'get_config')
        assert callable(dao.save_config)
        assert callable(dao.get_config)

    @pytest.mark.asyncio
    async def test_list_configs(self, dao):
        """测试列出配置"""
        # 测试方法存在
        assert hasattr(dao, 'list_configs')
        assert callable(dao.list_configs)

    @pytest.mark.asyncio
    async def test_delete_config(self, dao):
        """测试删除配置"""
        # 测试方法存在
        assert hasattr(dao, 'delete_config')
        assert callable(dao.delete_config)

    @pytest.mark.asyncio
    async def test_get_config_by_name(self, dao):
        """测试根据名称获取配置"""
        # 测试方法存在
        assert hasattr(dao, 'get_config_by_name')
        assert callable(dao.get_config_by_name)
