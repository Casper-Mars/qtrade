"""情绪因子计算器测试模块

测试 SentimentFactorCalculator 类的各种功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.factor_engine.calculators.sentiment import SentimentFactorCalculator
from src.clients.data_collector_client import DataCollectorClient


class TestSentimentFactorCalculator:
    """情绪因子计算器测试类"""

    @pytest.fixture
    def mock_data_client(self):
        """创建模拟数据客户端"""
        client = AsyncMock(spec=DataCollectorClient)
        
        # 模拟新闻数据
        news_data = [
            {
                "title": "公司业绩大幅增长，前景看好",
                "content": "该公司本季度营收同比增长30%，净利润大幅提升，市场前景非常乐观。",
                "publish_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "source": "财经日报",
                "sentiment_score": 0.8,
                "confidence": 0.9
            },
            {
                "title": "行业竞争加剧，公司面临挑战",
                "content": "由于行业竞争激烈，公司市场份额有所下降，未来发展存在不确定性。",
                "publish_time": (datetime.now() - timedelta(hours=5)).isoformat(),
                "source": "商业周刊",
                "sentiment_score": -0.6,
                "confidence": 0.8
            },
            {
                "title": "公司发布新产品，轻微提升市场预期",
                "content": "公司今日发布新产品，功能有所改进，市场反应平淡。",
                "publish_time": (datetime.now() - timedelta(hours=8)).isoformat(),
                "source": "科技资讯",
                "sentiment_score": 0.2,
                "confidence": 0.7
            }
        ]
        
        client.get_news_data.return_value = news_data
        
        return client

    @pytest.fixture
    def calculator(self, mock_data_client):
        """创建情绪因子计算器实例"""
        calc = SentimentFactorCalculator()
        calc.data_client = mock_data_client
        return calc

    @pytest.fixture
    def mock_sentiment_analyzer(self):
        """创建模拟情绪分析器"""
        analyzer = MagicMock()
        analyzer.analyze_sentiment.return_value = {
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "positive_score": 0.7,
            "negative_score": 0.2,
            "neutral_score": 0.1
        }
        return analyzer

    # 程度修饰词测试
    def test_get_degree_modifier_strong_positive(self, calculator):
        """测试强烈正面程度修饰词"""
        text = "公司业绩大幅增长"
        result = calculator._get_degree_modifier(text)
        assert result > 1.0  # 应该有放大效果

    def test_get_degree_modifier_strong_negative(self, calculator):
        """测试强烈负面程度修饰词"""
        text = "股价暴跌，投资者恐慌"
        result = calculator._get_degree_modifier(text)
        assert result > 1.0  # 应该有放大效果

    def test_get_degree_modifier_mild(self, calculator):
        """测试轻微程度修饰词"""
        text = "股价轻微上涨"
        result = calculator._get_degree_modifier(text)
        assert result == 1.0  # _get_degree_modifier返回最大权重，轻微时仍为默认1.0

    def test_get_degree_modifier_no_modifier(self, calculator):
        """测试无程度修饰词"""
        text = "公司发布财报"
        result = calculator._get_degree_modifier(text)
        assert result == 1.0  # 应该无影响

    # 新闻情绪分数计算测试
    @pytest.mark.asyncio
    async def test_calculate_news_sentiment_score_normal(self, calculator, mock_data_client):
        """测试正常情况下的新闻情绪分数计算"""
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_score": 0.6,
                "confidence": 0.8,
                "positive_score": 0.7,
                "negative_score": 0.2,
                "neutral_score": 0.1
            }
            
            # 使用模拟的新闻数据
            news_data = await mock_data_client.get_news_data("000001", "2023-12-01", "2023-12-01")
            result = calculator.calculate_news_sentiment_score(news_data)
            
            assert result is not None
            assert "sentiment_score" in result
            assert "confidence" in result
            assert "positive_score" in result
            assert "negative_score" in result
            assert "news_count" in result
            assert isinstance(result["sentiment_score"], float)
            assert isinstance(result["confidence"], float)

    @pytest.mark.asyncio
    async def test_calculate_news_sentiment_score_no_news(self, calculator, mock_data_client):
        """测试无新闻数据的情况"""
        mock_data_client.get_news_data.return_value = []
        
        # 使用空的新闻数据
        news_data = await mock_data_client.get_news_data("000001", "2023-12-01", "2023-12-01")
        result = calculator.calculate_news_sentiment_score(news_data)
        
        assert result is not None
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.0
        assert result["news_count"] == 0

    @pytest.mark.asyncio
    async def test_calculate_news_sentiment_score_with_time_decay(self, calculator, mock_data_client):
        """测试带时间衰减的情绪分数计算"""
        # 创建不同时间的新闻数据
        old_news = [
            {
                "title": "旧新闻",
                "content": "这是一条旧新闻",
                "publish_time": (datetime.now() - timedelta(days=2)).isoformat(),
                "source": "测试源",
                "sentiment_score": 0.8,
                "confidence": 0.9
            }
        ]
        
        recent_news = [
            {
                "title": "新新闻",
                "content": "这是一条新新闻",
                "publish_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "source": "测试源",
                "sentiment_score": 0.8,
                "confidence": 0.9
            }
        ]
        
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "positive_score": 0.8,
                "negative_score": 0.1,
                "neutral_score": 0.1
            }
            
            # 测试旧新闻
            old_result = calculator.calculate_news_sentiment_score(old_news)
            
            # 测试新新闻
            recent_result = calculator.calculate_news_sentiment_score(recent_news)
            
            # 新新闻的权重应该更高
            assert recent_result["sentiment_score"] >= old_result["sentiment_score"]

    # 股票情绪因子计算测试
    @pytest.mark.asyncio
    async def test_calculate_stock_sentiment_factor_normal(self, calculator, mock_data_client):
        """测试正常情况下的股票情绪因子计算"""
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_score": 0.6,
                "confidence": 0.8,
                "positive_score": 0.7,
                "negative_score": 0.2,
                "neutral_score": 0.1
            }
            
            start_date = datetime(2023, 11, 24)
            end_date = datetime(2023, 12, 1)
            result = await calculator.calculate_stock_sentiment_factor("000001", start_date, end_date)
            
            assert result is not None
            assert isinstance(result, dict)
            assert "sentiment_factor" in result
            assert "sentiment_details" in result
            assert "volume_adjustment" in result

    @pytest.mark.asyncio
    async def test_calculate_stock_sentiment_factor_no_news(self, calculator, mock_data_client):
        """测试无新闻时的股票情绪因子计算"""
        mock_data_client.get_news_data.return_value = []
        
        start_date = datetime(2023, 11, 24)
        end_date = datetime(2023, 12, 1)
        result = await calculator.calculate_stock_sentiment_factor("000001", start_date, end_date)
        
        assert result is not None
        assert result["sentiment_factor"] == 0.0
        assert result["sentiment_details"]["confidence"] == 0.0
        # 无新闻时没有volume_adjustment字段

    # 批量情绪因子计算测试
    @pytest.mark.asyncio
    async def test_calculate_batch_sentiment_factors_normal(self, calculator, mock_data_client):
        """测试正常情况下的批量情绪因子计算"""
        stock_codes = ["000001", "000002", "000003"]
        
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_scores": {
                    "positive": 0.6,
                    "negative": 0.3,
                    "neutral": 0.1
                },
                "confidence": 0.8
            }
            
            date = datetime(2023, 12, 1)
            result = await calculator.calculate_batch_sentiment_factors(stock_codes, date)
            
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == len(stock_codes)
            
            for item in result:
                assert isinstance(item, dict)
                assert "sentiment_factor" in item

    @pytest.mark.asyncio
    async def test_calculate_batch_sentiment_factors_empty_list(self, calculator, mock_data_client):
        """测试空股票列表的批量计算"""
        date = datetime(2023, 12, 1)
        result = await calculator.calculate_batch_sentiment_factors([], date)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0

    # 情绪趋势计算测试
    @pytest.mark.asyncio
    async def test_get_sentiment_trend_normal(self, calculator, mock_data_client):
        """测试正常情况下的情绪趋势计算"""
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_scores": {
                    "positive": 0.7,
                    "negative": 0.2,
                    "neutral": 0.1
                },
                "confidence": 0.8
            }
            
            result = await calculator.get_sentiment_trend("000001", days=7)
            
            assert result is not None
            assert isinstance(result, dict)
            assert "statistics" in result
            assert "trend_direction" in result["statistics"]
            assert "daily_factors" in result
            assert isinstance(result["daily_factors"], list)

    @pytest.mark.asyncio
    async def test_get_sentiment_trend_insufficient_data(self, calculator, mock_data_client):
        """测试数据不足时的情绪趋势计算"""
        # 只返回少量新闻
        limited_news = [
            {
                "title": "测试新闻",
                "content": "测试内容",
                "publish_time": datetime.now().isoformat(),
                "source": "测试源",
                "sentiment_score": 0.5,
                "confidence": 0.8
            }
        ]
        
        mock_data_client.get_news_data.return_value = limited_news
        
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_scores": {
                    "positive": 0.6,
                    "negative": 0.3,
                    "neutral": 0.1
                },
                "confidence": 0.8
            }
            
            result = await calculator.get_sentiment_trend("000001", days=7)
            
            assert result is not None
            # 数据不足时应该有合理的默认值
            assert "statistics" in result
            assert "trend_direction" in result["statistics"]

    # 综合因子计算测试（注：SentimentFactorCalculator没有calculate_factors方法，这里测试主要方法）
    @pytest.mark.asyncio
    async def test_sentiment_factor_integration(self, calculator, mock_data_client):
        """测试情绪因子计算的集成功能"""
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_score": 0.6,
                "confidence": 0.8,
                "positive_score": 0.7,
                "negative_score": 0.2,
                "neutral_score": 0.1
            }
            
            start_date = datetime(2023, 11, 24)
            end_date = datetime(2023, 12, 1)
            
            # 测试股票情绪因子计算
            sentiment_result = await calculator.calculate_stock_sentiment_factor("000001", start_date, end_date)
            assert sentiment_result is not None
            assert "sentiment_factor" in sentiment_result
            
            # 测试情绪趋势计算
            trend_result = await calculator.get_sentiment_trend("000001", days=7)
            assert trend_result is not None
            assert "statistics" in trend_result
            assert "trend_direction" in trend_result["statistics"]

    # 边界条件测试
    @pytest.mark.asyncio
    async def test_edge_case_extreme_sentiment(self, calculator, mock_data_client):
        """测试极端情绪值的边界情况"""
        extreme_news = [
            {
                "title": "极度乐观的新闻",
                "content": "非常非常好的消息",
                "publish_time": datetime.now().isoformat(),
                "source": "测试源",
                "sentiment_score": 1.0,  # 极端正面
                "confidence": 1.0
            },
            {
                "title": "极度悲观的新闻",
                "content": "非常非常坏的消息",
                "publish_time": datetime.now().isoformat(),
                "source": "测试源",
                "sentiment_score": -1.0,  # 极端负面
                "confidence": 1.0
            }
        ]
        
        mock_data_client.get_news_data.return_value = extreme_news
        
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.side_effect = [
                {
                    "sentiment_score": 1.0,
                    "confidence": 1.0,
                    "positive_score": 1.0,
                    "negative_score": 0.0,
                    "neutral_score": 0.0
                },
                {
                    "sentiment_score": -1.0,
                    "confidence": 1.0,
                    "positive_score": 0.0,
                    "negative_score": 1.0,
                    "neutral_score": 0.0
                }
            ]
            
            result = calculator.calculate_news_sentiment_score(extreme_news)
            
            assert result is not None
            # 极端值应该被合理处理
            assert -1.0 <= result["sentiment_score"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_edge_case_malformed_news_data(self, calculator, mock_data_client):
        """测试格式错误的新闻数据"""
        malformed_news = [
            {
                "title": "正常新闻",
                "content": "正常内容",
                "publish_time": datetime.now().isoformat(),
                "source": "测试源"
                # 缺少 sentiment_score 和 confidence
            },
            {
                # 缺少必要字段
                "title": "不完整新闻"
            },
            {
                "title": "",  # 空标题
                "content": "",  # 空内容
                "publish_time": "invalid_date",  # 无效日期
                "source": "测试源",
                "sentiment_score": "invalid",  # 无效分数
                "confidence": None
            }
        ]
        
        mock_data_client.get_news_data.return_value = malformed_news
        
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.return_value = {
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "positive_score": 0.6,
                "negative_score": 0.3,
                "neutral_score": 0.1
            }
            
            # 应该能处理格式错误的数据而不崩溃
            result = calculator.calculate_news_sentiment_score(malformed_news)
            
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_edge_case_data_client_exception(self, calculator, mock_data_client):
        """测试数据客户端异常"""
        mock_data_client.get_news_data.side_effect = Exception("数据获取失败")
        
        start_date = datetime(2023, 11, 24)
        end_date = datetime(2023, 12, 1)
        
        # 数据客户端异常时应该抛出异常
        with pytest.raises(Exception):
            await calculator.calculate_stock_sentiment_factor("000001", start_date, end_date)

    @pytest.mark.asyncio
    async def test_edge_case_sentiment_analyzer_exception(self, calculator, mock_data_client):
        """测试情绪分析器异常的边界情况"""
        with patch.object(calculator, 'sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment.side_effect = Exception("分析器异常")
            
            start_date = datetime(2023, 11, 24)
            end_date = datetime(2023, 12, 1)
            result = await calculator.calculate_stock_sentiment_factor("000001", start_date, end_date)
            
            # 分析器异常时应该有合理的降级处理
            assert result is not None
            assert isinstance(result, dict)
            assert result["sentiment_factor"] == 0.0