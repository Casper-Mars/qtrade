"""数据回放器测试模块

测试数据回放器的核心功能，包括：
- 数据回放功能
- 数据快照获取
- 交易日历获取
- 价格数据获取
- 因子数据获取
- 数据验证
- 缓存管理
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from pydantic import ValidationError

from src.backtest_engine.models.backtest_models import (
    BacktestFactorConfig,
    BacktestMode,
)
from src.backtest_engine.services.data_replayer import DataReplayer, DataSnapshot
from src.clients.tushare_client import TushareClient
from src.factor_engine.services.factor_service import FactorService
from src.utils.exceptions import ValidationException


class TestDataSnapshot:
    """数据快照测试类"""

    def test_data_snapshot_creation(self):
        """测试数据快照创建"""
        snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5},
            factor_data={"rsi": 65.5, "macd": 0.15},
            volume=1000000,
            market_cap=50000000000
        )

        assert snapshot.timestamp == "2024-01-15"
        assert snapshot.stock_code == "000001.SZ"
        assert snapshot.price_data["close"] == 10.5
        assert snapshot.factor_data["rsi"] == 65.5
        assert snapshot.volume == 1000000
        assert snapshot.market_cap == 50000000000

    def test_data_snapshot_validation(self):
        """测试数据快照验证"""
        # 测试缺少必填字段 - Pydantic 会抛出 ValidationError
        with pytest.raises(ValidationError):
            DataSnapshot(
                # 缺少 timestamp 字段
                stock_code="000001.SZ",
                price_data={},
                factor_data={}
            )


class TestDataReplayer:
    """数据回放器测试类"""

    @pytest.fixture
    def mock_factor_service(self):
        """创建模拟因子服务"""
        service = MagicMock(spec=FactorService)
        service.calculate_unified_factors = AsyncMock()
        return service

    @pytest.fixture
    def mock_tushare_client(self):
        """创建模拟Tushare客户端"""
        client = MagicMock(spec=TushareClient)
        client._api = MagicMock()
        return client

    @pytest.fixture
    def mock_factor_config(self):
        """创建模拟因子配置"""
        config = MagicMock(spec=BacktestFactorConfig)
        config.get_technical_factors.return_value = ["rsi", "macd"]
        config.get_fundamental_factors.return_value = ["pe_ratio", "pb_ratio"]
        config.get_market_factors.return_value = ["market_cap", "turnover"]
        config.get_sentiment_factors.return_value = ["news_sentiment", "social_sentiment"]
        return config

    @pytest.fixture
    def data_replayer(self, mock_factor_service, mock_tushare_client):
        """创建数据回放器实例"""
        return DataReplayer(
            factor_service=mock_factor_service,
            data_client=mock_tushare_client
        )

    def test_data_replayer_initialization(self, data_replayer, mock_factor_service, mock_tushare_client):
        """测试数据回放器初始化"""
        assert data_replayer.factor_service == mock_factor_service
        assert data_replayer.data_client == mock_tushare_client
        assert isinstance(data_replayer._cache, dict)
        assert len(data_replayer._cache) == 0

    @pytest.mark.asyncio
    async def test_get_trading_calendar_success(self, data_replayer):
        """测试成功获取交易日历"""
        # 模拟API返回数据
        mock_cal_data = pd.DataFrame({
            'cal_date': ['20240115', '20240116', '20240117'],
            'is_open': [1, 1, 1]
        })

        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_cal_data
            mock_loop.return_value.run_in_executor = mock_executor

            result = await data_replayer._get_trading_dates("2024-01-15", "2024-01-17")

            assert result == ['20240115', '20240116', '20240117']

    @pytest.mark.asyncio
    async def test_get_trading_calendar_api_not_initialized(self, data_replayer):
        """测试API未初始化时获取交易日历"""
        data_replayer.data_client._api = None

        # API未初始化时会回退到生成工作日序列，不会抛出异常
        result = await data_replayer._get_trading_dates("2024-01-15", "2024-01-17")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_trading_calendar_empty_result(self, data_replayer):
        """测试获取交易日历返回空结果"""
        mock_cal_data = pd.DataFrame()

        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_cal_data
            mock_loop.return_value.run_in_executor = mock_executor

            # 空结果时会回退到生成工作日序列
            result = await data_replayer._get_trading_dates("2024-01-15", "2024-01-17")
            assert isinstance(result, list)

    def test_generate_business_days(self, data_replayer):
        """测试生成工作日序列"""
        result = data_replayer._generate_business_days("2024-01-15", "2024-01-19")
        expected = ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
        assert result == expected

    def test_generate_business_days_single_day(self, data_replayer):
        """测试生成单日工作日序列"""
        result = data_replayer._generate_business_days("2024-01-15", "2024-01-15")
        assert result == ['2024-01-15']

    def test_generate_business_days_invalid_range(self, data_replayer):
        """测试无效日期范围"""
        # 无效日期范围会返回空列表而不是抛出异常
        result = data_replayer._generate_business_days("2024-01-17", "2024-01-15")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_price_data_success(self, data_replayer):
        """测试成功获取价格数据"""
        mock_daily_data = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20240115'],
            'open': [10.0],
            'high': [11.0],
            'low': [9.5],
            'close': [10.5],
            'vol': [1000000],
            'amount': [10500000],
            'pct_chg': [5.0]
        })

        with patch.object(data_replayer.data_client, 'get_daily_data', new_callable=AsyncMock) as mock_get_daily:
            mock_get_daily.return_value = mock_daily_data

            result = await data_replayer._get_price_data("000001.SZ", "2024-01-15")

            expected = {
                'open': 10.0,
                'high': 11.0,
                'low': 9.5,
                'close': 10.5,
                'volume': 1000000,
                'amount': 10500000,
                'pct_chg': 5.0
            }
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_price_data_empty_result(self, data_replayer):
        """测试获取价格数据返回空结果"""
        with patch.object(data_replayer.data_client, 'get_daily_data', new_callable=AsyncMock) as mock_get_daily:
            mock_get_daily.return_value = pd.DataFrame()

            with pytest.raises(ValidationException, match="无法获取.*的价格数据"):
                await data_replayer._get_price_data("000001.SZ", "2024-01-15")

    @pytest.mark.asyncio
    async def test_get_factor_data_success(self, data_replayer, mock_factor_config):
        """测试成功获取因子数据"""
        # 创建模拟响应对象
        mock_response = MagicMock()
        mock_response.technical_factors = {'rsi': 65.5, 'macd': 0.15}
        mock_response.fundamental_factors = {'pe_ratio': 15.2}
        mock_response.market_factors = {'market_cap': 50000000000}

        data_replayer.factor_service.calculate_all_factors = AsyncMock(return_value=mock_response)

        result = await data_replayer._get_factor_data(
            "000001.SZ", "2024-01-15", mock_factor_config, BacktestMode.HISTORICAL_SIMULATION
        )

        expected = {
            'rsi': 65.5,
            'macd': 0.15,
            'pe_ratio': 15.2,
            'market_cap': 50000000000
        }
        assert result == expected
        data_replayer.factor_service.calculate_all_factors.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_factor_data_exception(self, data_replayer, mock_factor_config):
        """测试获取因子数据异常"""
        data_replayer.factor_service.calculate_all_factors = AsyncMock(side_effect=Exception("计算失败"))

        result = await data_replayer._get_factor_data(
            "000001.SZ", "2024-01-15", mock_factor_config, BacktestMode.HISTORICAL_SIMULATION
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_snapshot_success(self, data_replayer, mock_factor_config):
        """测试成功获取数据快照"""
        # 模拟价格数据
        mock_price_data = {
            'open': 10.0,
            'high': 11.0,
            'low': 9.5,
            'close': 10.5,
            'volume': 1000000,
            'amount': 10500000
        }

        # 模拟因子数据
        mock_factor_data = {
            'rsi': 65.5,
            'macd': 0.15,
            'total_market_cap': 50000000000
        }

        with patch.object(data_replayer, '_get_price_data', new_callable=AsyncMock) as mock_get_price, \
             patch.object(data_replayer, '_get_factor_data', new_callable=AsyncMock) as mock_get_factor:

            mock_get_price.return_value = mock_price_data
            mock_get_factor.return_value = mock_factor_data

            result = await data_replayer.get_snapshot(
                "000001.SZ", "2024-01-15", mock_factor_config
            )

            assert isinstance(result, DataSnapshot)
            assert result.timestamp == "2024-01-15"
            assert result.stock_code == "000001.SZ"
            assert result.price_data == mock_price_data
            assert result.factor_data == mock_factor_data
            assert result.volume == 1000000
            assert result.market_cap == 50000000000

    @pytest.mark.asyncio
    async def test_get_snapshot_with_cache(self, data_replayer, mock_factor_config):
        """测试使用缓存获取数据快照"""
        # 预设缓存数据
        cached_snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"close": 10.5},
            factor_data={"rsi": 65.5}
        )

        cache_key = "000001.SZ_2024-01-15_historical_simulation"
        data_replayer._cache[cache_key] = cached_snapshot

        result = await data_replayer.get_snapshot(
            "000001.SZ", "2024-01-15", mock_factor_config
        )

        assert result == cached_snapshot

    @pytest.mark.asyncio
    async def test_replay_data_success(self, data_replayer, mock_factor_config):
        """测试成功回放数据"""
        # 模拟交易日历
        trading_dates = ['2024-01-15', '2024-01-16']

        # 模拟数据快照
        mock_snapshots = [
            DataSnapshot(
                timestamp="2024-01-15",
                stock_code="000001.SZ",
                price_data={"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5},
                factor_data={"rsi": 65.5}
            ),
            DataSnapshot(
                timestamp="2024-01-16",
                stock_code="000001.SZ",
                price_data={"open": 10.5, "high": 11.2, "low": 10.0, "close": 10.8},
                factor_data={"rsi": 67.2}
            )
        ]

        with patch.object(data_replayer, '_get_trading_dates', new_callable=AsyncMock) as mock_get_calendar, \
             patch.object(data_replayer, 'get_snapshot', new_callable=AsyncMock) as mock_get_snapshot:

            mock_get_calendar.return_value = trading_dates
            mock_get_snapshot.side_effect = mock_snapshots

            snapshots = []
            async for snapshot in data_replayer.replay_data(
                "000001.SZ", "2024-01-15", "2024-01-16", mock_factor_config
            ):
                snapshots.append(snapshot)

            assert len(snapshots) == 2
            assert snapshots[0].timestamp == "2024-01-15"
            assert snapshots[1].timestamp == "2024-01-16"

    @pytest.mark.asyncio
    async def test_replay_data_no_trading_dates(self, data_replayer, mock_factor_config):
        """测试无交易日时回放数据"""
        with patch.object(data_replayer, '_get_trading_dates', new_callable=AsyncMock) as mock_get_calendar:
            mock_get_calendar.return_value = []

            with pytest.raises(ValidationException, match="指定时间范围内无交易日"):
                async for _ in data_replayer.replay_data(
                    "000001.SZ", "2024-01-15", "2024-01-16", mock_factor_config
                ):
                    pass

    def test_validate_snapshot_valid(self, data_replayer):
        """测试有效数据快照验证"""
        snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5},
            factor_data={"rsi": 65.5, "macd": 0.15}
        )

        result = data_replayer._validate_snapshot(snapshot)
        assert result is True

    def test_validate_snapshot_invalid_price(self, data_replayer):
        """测试验证包含无效价格的数据快照"""
        snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"open": -1.0, "high": 11.0, "low": 9.5, "close": 10.5},  # 负价格
            factor_data={"rsi": 65.5}
        )

        result = data_replayer._validate_snapshot(snapshot)
        assert result is False

    def test_validate_snapshot_invalid_factor(self, data_replayer):
        """测试验证包含无效因子的数据快照"""
        snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5},
            factor_data={"rsi": float('nan'), "macd": 0.15}  # NaN因子
        )

        result = data_replayer._validate_snapshot(snapshot)
        assert result is True  # 允许部分因子缺失

    def test_validate_timeline_success(self, data_replayer):
        """测试成功验证时间序列"""
        timestamps = ['2024-01-15', '2024-01-16', '2024-01-17']
        result = data_replayer.validate_timeline(timestamps)
        assert result is True

    def test_validate_timeline_wrong_order(self, data_replayer):
        """测试验证错误顺序的时间序列"""
        timestamps = ['2024-01-17', '2024-01-15', '2024-01-16']  # 错误顺序
        with pytest.raises(ValidationException):
            data_replayer.validate_timeline(timestamps)

    def test_validate_timeline_single_timestamp(self, data_replayer):
        """测试验证单个时间戳"""
        timestamps = ['2024-01-15']
        result = data_replayer.validate_timeline(timestamps)
        assert result is True

    def test_prevent_lookahead_bias_success(self, data_replayer):
        """测试成功防止未来函数泄露"""
        result = data_replayer._prevent_lookahead_bias("2024-01-15", {"price": 10.5})
        assert result is True

    def test_prevent_lookahead_bias_invalid_timestamp(self, data_replayer):
        """测试无效时间戳的未来函数泄露检查"""
        result = data_replayer._prevent_lookahead_bias("invalid-date", {"price": 10.5})
        assert result is False

    def test_clear_cache(self, data_replayer):
        """测试清空缓存"""
        # 添加一些缓存数据
        data_replayer._cache["test_key"] = "test_value"
        assert len(data_replayer._cache) == 1

        # 清空缓存
        data_replayer.clear_cache()
        assert len(data_replayer._cache) == 0

    @pytest.mark.asyncio
    async def test_replay_data_with_validation(self, data_replayer, mock_factor_config):
        """测试带验证的数据回放"""
        trading_dates = ['2024-01-15', '2024-01-16']

        # 创建一个有效快照和一个无效快照
        valid_snapshot = DataSnapshot(
            timestamp="2024-01-15",
            stock_code="000001.SZ",
            price_data={"close": 10.5},
            factor_data={"rsi": 65.5}
        )

        invalid_snapshot = DataSnapshot(
            timestamp="2024-01-16",
            stock_code="000001.SZ",
            price_data={"close": -1.0},  # 无效价格
            factor_data={"rsi": 67.2}
        )

        with patch.object(data_replayer, '_get_trading_dates', new_callable=AsyncMock) as mock_get_calendar, \
             patch.object(data_replayer, 'get_snapshot', new_callable=AsyncMock) as mock_get_snapshot, \
             patch.object(data_replayer, '_validate_snapshot') as mock_validate:

            mock_get_calendar.return_value = trading_dates
            mock_get_snapshot.side_effect = [valid_snapshot, invalid_snapshot]
            mock_validate.side_effect = [True, False]  # 第一个有效，第二个无效

            snapshots = []
            async for snapshot in data_replayer.replay_data(
                "000001.SZ", "2024-01-15", "2024-01-16", mock_factor_config
            ):
                snapshots.append(snapshot)

            # 只应该返回有效的快照
            assert len(snapshots) == 1
            assert snapshots[0].timestamp == "2024-01-15"
