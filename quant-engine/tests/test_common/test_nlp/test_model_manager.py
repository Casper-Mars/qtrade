"""NLP模型管理器单元测试"""

from unittest.mock import Mock, patch

import pytest
import torch

from src.nlp.model_manager import NLPModelManager


class TestNLPModelManager:
    """NLP模型管理器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置单例实例
        NLPModelManager._instance = None
        self.manager = NLPModelManager()

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理所有模型
        if hasattr(self.manager, '_models'):
            self.manager.clear_all_models()
        # 重置单例实例
        NLPModelManager._instance = None

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = NLPModelManager()
        manager2 = NLPModelManager()
        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_initialization(self):
        """测试初始化"""
        assert hasattr(self.manager, '_models')
        assert hasattr(self.manager, '_current_model_key')
        assert hasattr(self.manager, '_device')
        assert hasattr(self.manager, '_initialized')
        assert self.manager._initialized is True
        assert isinstance(self.manager._models, dict)
        assert self.manager._current_model_key is None
        assert isinstance(self.manager._device, torch.device)

    def test_supported_models_config(self):
        """测试支持的模型配置"""
        assert "finbert2-large" in NLPModelManager.SUPPORTED_MODELS
        finbert_config = NLPModelManager.SUPPORTED_MODELS["finbert2-large"]
        assert "model_name" in finbert_config
        assert "description" in finbert_config
        assert "max_length" in finbert_config
        assert finbert_config["model_name"] == "valuesimplex-ai-lab/FinBERT2-large"
        assert finbert_config["max_length"] == 512

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_load_model_success(self, mock_model_class, mock_tokenizer_class):
        """测试成功加载模型"""
        # 模拟tokenizer和model
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # 测试加载
        result = self.manager.load_model("finbert2-large")

        assert result is True
        assert "finbert2-large" in self.manager._models
        assert self.manager._current_model_key == "finbert2-large"

        # 验证模型被移动到设备并设置为评估模式
        mock_model.to.assert_called_once_with(self.manager._device)
        mock_model.eval.assert_called_once()

    def test_load_unsupported_model(self):
        """测试加载不支持的模型"""
        result = self.manager.load_model("unsupported-model")
        assert result is False
        assert "unsupported-model" not in self.manager._models
        assert self.manager._current_model_key is None

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_load_model_already_loaded(self, mock_model_class, mock_tokenizer_class):
        """测试加载已经加载的模型"""
        # 先加载一次
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

        # 重置mock调用计数
        mock_tokenizer_class.from_pretrained.reset_mock()
        mock_model_class.from_pretrained.reset_mock()

        # 再次加载同一个模型
        result = self.manager.load_model("finbert2-large")

        assert result is True
        assert self.manager._current_model_key == "finbert2-large"
        # 验证没有重新加载
        mock_tokenizer_class.from_pretrained.assert_not_called()
        mock_model_class.from_pretrained.assert_not_called()

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_load_model_exception(self, mock_model_class, mock_tokenizer_class):
        """测试加载模型时发生异常"""
        # 模拟异常
        mock_tokenizer_class.from_pretrained.side_effect = Exception("加载失败")

        result = self.manager.load_model("finbert2-large")

        assert result is False
        assert "finbert2-large" not in self.manager._models
        assert self.manager._current_model_key is None

    def test_switch_model_unsupported(self):
        """测试切换到不支持的模型"""
        result = self.manager.switch_model("unsupported-model")
        assert result is False

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_switch_model_not_loaded(self, mock_model_class, mock_tokenizer_class):
        """测试切换到未加载的模型"""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        result = self.manager.switch_model("finbert2-large")

        assert result is True
        assert self.manager._current_model_key == "finbert2-large"

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_switch_model_already_loaded(self, mock_model_class, mock_tokenizer_class):
        """测试切换到已加载的模型"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

        # 切换到已加载的模型
        result = self.manager.switch_model("finbert2-large")

        assert result is True
        assert self.manager._current_model_key == "finbert2-large"

    def test_get_model_info_no_model(self):
        """测试获取模型信息（无当前模型）"""
        info = self.manager.get_model_info()

        assert info["current_model"] is None
        assert info["loaded_models"] == []

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_get_model_info_with_model(self, mock_model_class, mock_tokenizer_class):
        """测试获取模型信息（有当前模型）"""
        # 加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

        info = self.manager.get_model_info()

        assert info["current_model"] == "finbert2-large"
        assert "finbert2-large" in info["loaded_models"]
        assert "supported_models" in info
        assert "device" in info
        assert "current_model_name" in info
        assert "current_model_description" in info

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_unload_model(self, mock_model_class, mock_tokenizer_class):
        """测试卸载模型"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")
        assert "finbert2-large" in self.manager._models

        # 卸载模型
        result = self.manager.unload_model("finbert2-large")

        assert result is True
        assert "finbert2-large" not in self.manager._models
        assert self.manager._current_model_key is None

    def test_unload_model_not_loaded(self):
        """测试卸载未加载的模型"""
        result = self.manager.unload_model("finbert2-large")
        assert result is False

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_clear_all_models(self, mock_model_class, mock_tokenizer_class):
        """测试清理所有模型"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")
        assert len(self.manager._models) > 0

        # 清理所有模型
        self.manager.clear_all_models()

        assert len(self.manager._models) == 0
        assert self.manager._current_model_key is None

    @patch('src.nlp.model_manager.torch')
    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_predict_sentiment_no_model(self, mock_model_class, mock_tokenizer_class, mock_torch):
        """测试没有模型时的情绪预测"""
        # 模拟加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # 模拟tokenizer输出
        mock_tokenizer.return_value = {
            'input_ids': mock_torch.tensor([[1, 2, 3]]),
            'attention_mask': mock_torch.tensor([[1, 1, 1]])
        }

        # 模拟模型输出
        mock_outputs = Mock()
        mock_outputs.logits = mock_torch.tensor([[0.1, 0.2, 0.7]])
        mock_model.return_value = mock_outputs

        # 模拟softmax输出
        mock_torch.nn.functional.softmax.return_value = mock_torch.tensor([[0.2, 0.3, 0.5]])
        mock_torch.tensor([[0.2, 0.3, 0.5]]).cpu.return_value.numpy.return_value = [[0.2, 0.3, 0.5]]

        # 测试预测（会自动加载模型）
        result = self.manager.predict_sentiment("测试文本")

        assert isinstance(result, dict)
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result

    def test_predict_sentiment_no_model_load_fail(self):
        """测试模型加载失败时的情绪预测"""
        with patch.object(self.manager, 'load_model', return_value=False):
            with pytest.raises(RuntimeError, match="无法加载模型"):
                self.manager.predict_sentiment("测试文本")

    @patch('src.nlp.model_manager.torch')
    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_predict_sentiment_success_three_class(self, mock_model_class, mock_tokenizer_class, mock_torch):
        """测试成功的三分类情绪预测"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

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
        mock_predictions.cpu.return_value.numpy.return_value = [[0.2, 0.3, 0.5]]  # 三分类

        result = self.manager.predict_sentiment("测试文本")

        assert result["negative"] == 0.2
        assert result["neutral"] == 0.3
        assert result["positive"] == 0.5

    @patch('src.nlp.model_manager.torch')
    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_predict_sentiment_success_two_class(self, mock_model_class, mock_tokenizer_class, mock_torch):
        """测试成功的二分类情绪预测"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

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
        mock_predictions.cpu.return_value.numpy.return_value = [[0.3, 0.7]]  # 二分类

        result = self.manager.predict_sentiment("测试文本")

        assert result["negative"] == 0.3
        assert result["neutral"] == 0.0
        assert result["positive"] == 0.7

    @patch('src.nlp.model_manager.AutoTokenizer')
    @patch('src.nlp.model_manager.AutoModelForSequenceClassification')
    def test_predict_sentiment_exception(self, mock_model_class, mock_tokenizer_class):
        """测试情绪预测时发生异常"""
        # 先加载模型
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        self.manager.load_model("finbert2-large")

        # 模拟tokenizer异常
        mock_tokenizer.side_effect = Exception("Tokenizer错误")

        with pytest.raises(Exception, match="Tokenizer错误"):
            self.manager.predict_sentiment("测试文本")
