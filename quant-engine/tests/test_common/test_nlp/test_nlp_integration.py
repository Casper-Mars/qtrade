"""NLP模块集成测试"""

from unittest.mock import Mock, patch

from src.nlp.model_manager import NLPModelManager
from src.nlp.sentiment_analyzer import SentimentAnalyzer


class TestNLPIntegration:
    """NLP模块集成测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置单例实例
        NLPModelManager._instance = None
        self.analyzer = SentimentAnalyzer()
        self.model_manager = self.analyzer.model_manager

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理模型管理器
        if hasattr(self.model_manager, '_models'):
            self.model_manager.clear_all_models()
        # 重置单例实例
        NLPModelManager._instance = None

    def test_analyzer_model_manager_integration(self):
        """测试分析器与模型管理器的集成"""
        # 验证分析器使用的是同一个模型管理器实例
        manager1 = NLPModelManager()
        manager2 = self.analyzer.model_manager

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    async def test_end_to_end_sentiment_analysis_without_model(self, mock_model_class, mock_tokenizer_class):
        """测试端到端情绪分析（不使用深度学习模型）"""
        # 测试文本
        test_texts = [
            "股票大幅上涨，投资者非常乐观",
            "股票暴跌，投资者恐慌抛售",
            "今天天气不错"
        ]

        results = []
        for text in test_texts:
            result = await self.analyzer.analyze_sentiment(text)
            results.append(result)

        # 验证结果结构
        for result in results:
            assert "positive" in result
            assert "negative" in result
            assert "neutral" in result
            assert "confidence" in result
            assert isinstance(result["positive"], float)
            assert isinstance(result["negative"], float)
            assert isinstance(result["neutral"], float)
            assert isinstance(result["confidence"], float)

        # 验证分数范围
        for result in results:
            assert 0.0 <= result["positive"] <= 1.0
            assert 0.0 <= result["negative"] <= 1.0
            assert 0.0 <= result["neutral"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0

    @patch('src.nlp.model_manager.torch')
    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    async def test_end_to_end_sentiment_analysis_with_model(self, mock_model_class, mock_tokenizer_class, mock_torch):
        """测试端到端情绪分析（使用深度学习模型）"""
        # 模拟tokenizer和model
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # 模拟tokenizer输出
        mock_inputs = {
            'input_ids': Mock(),
            'attention_mask': Mock()
        }
        mock_tokenizer.return_value = mock_inputs

        # 模拟设备转换
        for key in mock_inputs:
            mock_inputs[key].to.return_value = mock_inputs[key]

        # 模拟模型输出
        mock_outputs = Mock()
        mock_outputs.logits = Mock()
        mock_model.return_value = mock_outputs

        # 模拟softmax和numpy转换
        mock_predictions = Mock()
        mock_torch.nn.functional.softmax.return_value = mock_predictions
        mock_predictions.cpu.return_value.numpy.return_value = [[0.1, 0.2, 0.7]]  # 积极情绪

        # 测试文本
        text = "股票大幅上涨，投资者非常乐观"
        result = await self.analyzer.analyze_sentiment(text)

        # 验证模型被加载
        assert "finbert2-large" in self.model_manager._models
        assert self.model_manager._current_model_key == "finbert2-large"

        # 验证结果
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "confidence" in result

        # 验证模型被调用
        mock_tokenizer.assert_called()
        mock_model.assert_called()

    async def test_batch_analysis_integration(self):
        """测试批量分析集成"""
        test_texts = [
            "股票大幅上涨，投资者非常乐观",
            "股票暴跌，投资者恐慌抛售",
            "今天天气不错",
            "虽然股票上涨，但仍有下跌风险"
        ]

        results = await self.analyzer.batch_analyze(test_texts)

        assert len(results) == len(test_texts)

        # 验证每个结果的结构
        for result in results:
            assert "positive" in result
            assert "negative" in result
            assert "neutral" in result
            assert "confidence" in result

    async def test_sentiment_summary_integration(self):
        """测试情绪摘要集成"""
        test_texts = [
            "股票大涨", "股票大涨", "股票大涨",  # 3个积极
            "股票暴跌", "股票暴跌",              # 2个消极
            "今天天气不错"                      # 1个中性
        ]

        # 使用 patch 来模拟 batch_analyze，避免实际调用模型
        with patch.object(self.analyzer, 'batch_analyze') as mock_batch_analyze:
            # 模拟批量分析结果
            mock_results = [
                {"positive": 0.8, "negative": 0.1, "neutral": 0.1, "confidence": 0.8},
                {"positive": 0.8, "negative": 0.1, "neutral": 0.1, "confidence": 0.8},
                {"positive": 0.8, "negative": 0.1, "neutral": 0.1, "confidence": 0.8},
                {"positive": 0.1, "negative": 0.8, "neutral": 0.1, "confidence": 0.8},
                {"positive": 0.1, "negative": 0.8, "neutral": 0.1, "confidence": 0.8},
                {"positive": 0.2, "negative": 0.2, "neutral": 0.6, "confidence": 0.6}
            ]
            mock_batch_analyze.return_value = mock_results

            summary = await self.analyzer.get_sentiment_summary(test_texts)

        assert summary["total_count"] == 6
        assert "sentiment_distribution" in summary
        assert "average_scores" in summary
        assert "dominant_sentiment" in summary

        # 验证分布统计
        distribution = summary["sentiment_distribution"]
        total_classified = sum(distribution.values())
        assert total_classified == 6

        # 由于积极文本较多，主导情绪应该是积极的
        assert summary["dominant_sentiment"] == "positive"

    async def test_text_preprocessing_integration(self):
        """测试文本预处理集成（简化版）"""
        # 包含各种需要预处理的文本
        dirty_text = "<p>股票价格  https://example.com  大幅@#$上涨！！！   联系：test@email.com</p>"

        result = await self.analyzer.analyze_sentiment(dirty_text)

        # 验证返回结构
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert "confidence" in result

        # 测试预处理功能
        processed = self.analyzer.preprocess_text(dirty_text)
        expected = "<p>股票价格 https://example.com 大幅@#$上涨！！！ 联系：test@email.com</p>"
        assert processed == expected

    def test_model_manager_state_persistence(self):
        """测试模型管理器状态持久性"""
        # 获取模型信息（无模型状态）
        info1 = self.model_manager.get_model_info()
        assert info1["current_model"] is None
        assert len(info1["loaded_models"]) == 0

        # 通过分析器触发模型加载（模拟）
        with patch('src.nlp.model_manager.AutoTokenizer') as mock_tokenizer_class, \
             patch('src.nlp.model_manager.AutoModelForSequenceClassification') as mock_model_class:

            mock_tokenizer = Mock()
            mock_model = Mock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
            mock_model_class.from_pretrained.return_value = mock_model

            # 加载模型
            success = self.model_manager.load_model("finbert2-large")
            assert success is True

            # 验证状态变化
            info2 = self.model_manager.get_model_info()
            assert info2["current_model"] == "finbert2-large"
            assert "finbert2-large" in info2["loaded_models"]

            # 切换模型（到同一个模型）
            switch_success = self.model_manager.switch_model("finbert2-large")
            assert switch_success is True

            # 卸载模型
            unload_success = self.model_manager.unload_model("finbert2-large")
            assert unload_success is True

            # 验证状态恢复
            info3 = self.model_manager.get_model_info()
            assert info3["current_model"] is None
            assert len(info3["loaded_models"]) == 0

    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试分析器在模型加载失败时的行为
        with patch.object(self.model_manager, 'load_model', return_value=False):
            with patch.object(self.model_manager, 'predict_sentiment', side_effect=RuntimeError("无法加载模型")):
                # 应该抛出异常
                try:
                    await self.analyzer.analyze_sentiment("股票上涨")
                    assert False, "应该抛出RuntimeError"
                except RuntimeError as e:
                    assert "无法加载模型" in str(e)

    def test_concurrent_access_simulation(self):
        """测试并发访问模拟（单例模式）"""
        # 模拟多个分析器实例
        analyzer1 = SentimentAnalyzer()
        analyzer2 = SentimentAnalyzer()

        # 验证它们使用同一个模型管理器
        assert analyzer1.model_manager is analyzer2.model_manager

        # 在一个分析器中加载模型
        with patch('src.nlp.model_manager.AutoTokenizer') as mock_tokenizer_class, \
             patch('src.nlp.model_manager.AutoModelForSequenceClassification') as mock_model_class:

            mock_tokenizer = Mock()
            mock_model = Mock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
            mock_model_class.from_pretrained.return_value = mock_model

            analyzer1.model_manager.load_model("finbert2-large")

            # 另一个分析器应该能看到已加载的模型
            info = analyzer2.model_manager.get_model_info()
            assert info["current_model"] == "finbert2-large"

    def test_memory_cleanup_integration(self):
        """测试内存清理集成"""
        with patch('src.nlp.model_manager.AutoTokenizer') as mock_tokenizer_class, \
             patch('src.nlp.model_manager.AutoModelForSequenceClassification') as mock_model_class, \
             patch('src.nlp.model_manager.torch') as mock_torch:

            mock_tokenizer = Mock()
            mock_model = Mock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
            mock_model_class.from_pretrained.return_value = mock_model

            # 加载模型
            self.model_manager.load_model("finbert2-large")
            assert len(self.model_manager._models) == 1

            # 清理所有模型
            self.model_manager.clear_all_models()
            assert len(self.model_manager._models) == 0
            assert self.model_manager._current_model_key is None

            # 验证GPU缓存清理被调用（如果可用）
            if mock_torch.cuda.is_available.return_value:
                mock_torch.cuda.empty_cache.assert_called()

    def test_configuration_integration(self):
        """测试配置集成"""
        # 验证支持的模型配置
        supported_models = NLPModelManager.SUPPORTED_MODELS
        assert "finbert2-large" in supported_models

        config = supported_models["finbert2-large"]
        assert "model_name" in config
        assert "description" in config
        assert "max_length" in config

        # 验证配置在分析器中的使用
        assert config["max_length"] == 512

        # 验证模型管理器能正确使用配置
        info = self.model_manager.get_model_info()
        # 当没有加载模型时，info只包含current_model和loaded_models
        assert "current_model" in info
        assert "loaded_models" in info
