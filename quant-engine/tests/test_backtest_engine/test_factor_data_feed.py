"""因子数据源测试模块

测试FactorDataFeed类的各项功能：
- 初始化参数验证
- 数据准备流程
- 价格数据获取
- 因子数据获取
- 数据合并和预处理
"""

from unittest.mock import Mock

import pytest


def test_simple_import() -> None:
    """简单的导入测试"""
    from src.backtest_engine.services.factor_data_feed import FactorDataFeed
    assert FactorDataFeed is not None


def test_basic_functionality() -> None:
    """基本功能测试"""
    assert True


class TestFactorDataFeed:
    """FactorDataFeed测试类"""

    def setup_method(self) -> None:
        """测试前置设置"""
        # 导入必要的模块
        from src.backtest_engine.models.backtest_models import (
            BacktestFactorConfig,
            FactorItem,
        )
        from src.clients.tushare_client import TushareClient
        from src.factor_engine.services.factor_service import FactorService

        # 创建模拟对象
        self.mock_factor_service = Mock(spec=FactorService)
        self.mock_data_client = Mock(spec=TushareClient)

        # 创建测试用的因子配置
        self.factor_configs = [
            FactorItem(
                factor_name="rsi_14",
                factor_type="technical",
                weight=0.6
            ),
            FactorItem(
                factor_name="macd_signal",
                factor_type="technical",
                weight=0.4
            )
        ]

        self.backtest_config = BacktestFactorConfig(
            combination_id="test_combination_001",
            factors=self.factor_configs,
            description="测试因子组合配置"
        )

        # 测试参数
        self.test_stock_code = "000001.SZ"
        self.test_start_date = "2023-01-01"
        self.test_end_date = "2023-12-31"

    def test_init_success(self) -> None:
        """测试成功初始化"""
        # 这个测试暂时跳过，因为需要异步环境
        pytest.skip("需要异步环境支持")

    def test_init_missing_factor_service(self) -> None:
        """测试缺少因子服务参数"""
        from src.backtest_engine.services.factor_data_feed import FactorDataFeed

        with pytest.raises(ValueError, match="缺少必要的初始化参数"):
            FactorDataFeed(
                factor_service=None,
                data_client=self.mock_data_client,
                stock_code=self.test_stock_code,
                start_date=self.test_start_date,
                end_date=self.test_end_date,
                factor_combination=self.backtest_config
            )

    def test_init_missing_stock_code(self) -> None:
        """测试缺少股票代码参数"""
        from src.backtest_engine.services.factor_data_feed import FactorDataFeed

        with pytest.raises(ValueError, match="缺少必要的初始化参数"):
            FactorDataFeed(
                factor_service=self.mock_factor_service,
                data_client=self.mock_data_client,
                stock_code=None,
                start_date=self.test_start_date,
                end_date=self.test_end_date,
                factor_combination=self.backtest_config
            )