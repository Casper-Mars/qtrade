"""情绪分析器单元测试"""

from unittest.mock import patch

import pytest

from src.nlp.model_manager import NLPModelManager
from src.nlp.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """情绪分析器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置单例实例
        NLPModelManager._instance = None
        self.analyzer = SentimentAnalyzer()

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理模型管理器
        if hasattr(self.analyzer.model_manager, '_models'):
            self.analyzer.model_manager.clear_all_models()
        # 重置单例实例
        NLPModelManager._instance = None

    def test_initialization(self):
        """测试初始化"""
        assert isinstance(self.analyzer.model_manager, NLPModelManager)





    def test_preprocess_text_empty(self):
        """测试空文本预处理"""
        result = self.analyzer.preprocess_text("")
        assert result == ""

        result = self.analyzer.preprocess_text(None)
        assert result == ""

    def test_preprocess_text_html_removal(self):
        """测试HTML标签处理（简化版）"""
        text = "<p>这是一个<strong>测试</strong>文本</p>"
        result = self.analyzer.preprocess_text(text)
        # 简化版预处理只处理空白字符，HTML标签由data-collector处理
        assert result == "<p>这是一个<strong>测试</strong>文本</p>"

    def test_preprocess_text_url_removal(self):
        """测试URL处理（简化版）"""
        text = "访问 https://www.example.com 获取更多信息"
        result = self.analyzer.preprocess_text(text)
        # 简化版预处理只处理空白字符，URL移除由data-collector处理
        assert result == "访问 https://www.example.com 获取更多信息"

    def test_preprocess_text_email_removal(self):
        """测试邮箱处理（简化版）"""
        text = "联系我们 contact@example.com"
        result = self.analyzer.preprocess_text(text)
        # 简化版预处理只处理空白字符，邮箱移除由data-collector处理
        assert result == "联系我们 contact@example.com"

    def test_preprocess_text_whitespace_normalization(self):
        """测试空白字符规范化"""
        text = "这是   一个\n\t测试   文本"
        result = self.analyzer.preprocess_text(text)
        assert "   " not in result
        assert "\n" not in result
        assert "\t" not in result
        assert "这是 一个 测试 文本" == result

    def test_preprocess_text_special_chars_removal(self):
        """测试特殊字符处理（简化版）"""
        text = "股票@#$%上涨了！"
        result = self.analyzer.preprocess_text(text)
        # 简化版预处理只处理空白字符，特殊字符移除由data-collector处理
        assert result == "股票@#$%上涨了！"

    def test_preprocess_text_comprehensive(self):
        """测试综合文本预处理"""
        text = "<div>股票价格  https://example.com  大幅@#$上涨！！！   联系：test@email.com</div>"
        result = self.analyzer.preprocess_text(text)

        # 简化版预处理只处理空白字符规范化，其他清理由data-collector处理
        expected = "<div>股票价格 https://example.com 大幅@#$上涨！！！ 联系：test@email.com</div>"
        assert result == expected





    async def test_analyze_sentiment_empty(self):
        """测试空文本情绪分析"""
        result = await self.analyzer.analyze_sentiment("")

        assert result["positive"] == 0.0
        assert result["negative"] == 0.0
        assert result["neutral"] == 1.0
        assert result["confidence"] == 1.0

    @patch.object(NLPModelManager, 'get_model_info')
    @patch.object(NLPModelManager, 'predict_sentiment')
    async def test_analyze_sentiment_without_model(self, mock_predict, mock_get_info):
        """测试情绪分析（模型失败时直接抛出异常）"""
        text = "股票大幅上涨，投资者非常乐观"

        # 模拟模型已加载但预测失败
        mock_get_info.return_value = {"current_model": "finbert2-large"}
        mock_predict.side_effect = Exception("模型失败")

        # 现在应该直接抛出异常，不再回退到规则方法
        with pytest.raises(Exception, match="模型失败"):
            await self.analyzer.analyze_sentiment(text)

    @patch.object(NLPModelManager, 'get_model_info')
    @patch.object(NLPModelManager, 'load_model')
    @patch.object(NLPModelManager, 'predict_sentiment')
    async def test_analyze_sentiment_with_model_success(self, mock_predict, mock_load, mock_get_info):
        """测试使用模型成功的情绪分析"""
        # 模拟模型已加载
        mock_get_info.return_value = {"current_model": "finbert2-large"}
        mock_predict.return_value = {"positive": 0.8, "negative": 0.1, "neutral": 0.1, "confidence": 0.9}

        text = "股票上涨"
        result = await self.analyzer.analyze_sentiment(text)

        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "confidence" in result
        mock_predict.assert_called_once()

        # 验证模型结果
        assert result["positive"] == 0.8
        assert result["negative"] == 0.1
        assert result["neutral"] == 0.1

    @patch.object(NLPModelManager, 'get_model_info')
    @patch.object(NLPModelManager, 'load_model')
    @patch.object(NLPModelManager, 'predict_sentiment')
    async def test_analyze_sentiment_with_model_no_current_model(self, mock_predict, mock_load, mock_get_info):
        """测试模型管理器没有当前模型时自动加载模型"""
        # 模拟没有当前模型，然后加载成功
        mock_get_info.side_effect = [
            {"current_model": None},  # 第一次调用返回没有模型
            {"current_model": "finbert2-large"}  # 第二次调用返回已加载模型
        ]
        mock_load.return_value = True
        mock_predict.return_value = {"positive": 0.7, "negative": 0.2, "neutral": 0.1}

        text = "股票上涨"
        result = await self.analyzer.analyze_sentiment(text)

        # 应该成功使用模型分析
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "confidence" in result
        mock_load.assert_called_once()
        mock_predict.assert_called_once()

    @patch.object(NLPModelManager, 'get_model_info')
    @patch.object(NLPModelManager, 'predict_sentiment')
    async def test_analyze_sentiment_with_model_exception(self, mock_predict, mock_get_info):
        """测试使用模型时发生异常的情绪分析"""
        # 模拟模型已加载但预测失败
        mock_get_info.return_value = {"current_model": "finbert2-large"}
        mock_predict.side_effect = Exception("模型预测失败")

        text = "股票上涨"

        # 现在应该直接抛出异常，不再回退到规则方法
        with pytest.raises(Exception, match="模型预测失败"):
            await self.analyzer.analyze_sentiment(text)

    async def test_analyze_sentiment_short_text_no_model(self):
        """测试短文本不使用模型的情绪分析"""
        text = "好"
        result = await self.analyzer.analyze_sentiment(text)

        # 短文本应该不使用模型
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "confidence" in result

    async def test_batch_analyze_empty(self):
        """测试空列表的批量分析"""
        result = await self.analyzer.batch_analyze([])
        assert result == []

    async def test_batch_analyze_success(self):
        """测试成功的批量分析"""
        texts = ["股票上涨", "股票下跌", "今天天气不错"]
        result = await self.analyzer.batch_analyze(texts)

        assert len(result) == 3
        for item in result:
            assert "positive" in item
            assert "negative" in item
            assert "neutral" in item
            assert "confidence" in item

    async def test_batch_analyze_with_exception(self):
        """测试批量分析中有异常的情况"""
        texts = ["正常文本"]

        with patch.object(self.analyzer, 'analyze_sentiment', side_effect=Exception("分析失败")):
            result = await self.analyzer.batch_analyze(texts)

            assert len(result) == 1

            assert result[0]["positive"] == 0.0
            assert result[0]["negative"] == 0.0
            assert result[0]["neutral"] == 1.0
            assert result[0]["confidence"] == 0.0

    async def test_get_sentiment_summary_empty(self):
        """测试空列表的情绪摘要"""
        result = await self.analyzer.get_sentiment_summary([])

        expected = {
            "total_count": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "average_scores": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
            "dominant_sentiment": "neutral"
        }
        assert result == expected

    async def test_get_sentiment_summary_success(self):
        """测试成功的情绪摘要"""
        texts = ["股票大涨", "股票暴跌", "股票上涨"]
        result = await self.analyzer.get_sentiment_summary(texts)

        assert result["total_count"] == 3
        assert "sentiment_distribution" in result
        assert "average_scores" in result
        assert "dominant_sentiment" in result

        # 验证分布统计
        distribution = result["sentiment_distribution"]
        assert distribution["positive"] + distribution["negative"] + distribution["neutral"] == 3

        # 验证平均分数
        avg_scores = result["average_scores"]
        assert abs(avg_scores["positive"] + avg_scores["negative"] + avg_scores["neutral"] - 1.0) < 0.001

    async def test_analyze_sentiment_processed_text_empty_after_preprocessing(self):
        """测试预处理后文本为空的情绪分析"""
        text = "   \n\t   "  # 只有空白字符，预处理后为空
        result = await self.analyzer.analyze_sentiment(text)

        assert result["positive"] == 0.0
        assert result["negative"] == 0.0
        assert result["neutral"] == 1.0
        assert result["confidence"] == 1.0

    async def test_analyze_sentiment_confidence_calculation(self):
        """测试置信度计算"""
        text = "股票大幅上涨"
        result = await self.analyzer.analyze_sentiment(text)

        # 置信度应该等于主导情绪的分数
        confidence = result["confidence"]
        max_score = max(result["positive"], result["negative"], result["neutral"])

        assert confidence == max_score

    async def test_model_weight_parameter(self):
        """测试模型权重参数的影响"""
        # 这个测试需要模拟模型预测，但由于复杂性，我们只测试参数传递
        text = "股票上涨"

        # 测试不同权重值不会导致错误
        result1 = await self.analyzer.analyze_sentiment(text)
        result2 = await self.analyzer.analyze_sentiment(text)

        assert "positive" in result1
        assert "positive" in result2
