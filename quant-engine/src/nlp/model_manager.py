"""NLP模型管理器

提供单例模式的模型管理，支持加载和切换多种中文金融BERT模型。
"""

import threading
from typing import Any, Self

import torch
from loguru import logger
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class NLPModelManager:
    """NLP模型管理器（单例模式）

    支持加载和管理多种中文金融BERT模型：
    - 熵简科技的FinBERT2-large
    """

    _instance = None
    _lock = threading.Lock()

    # 支持的模型配置
    SUPPORTED_MODELS = {
        "finbert2-large": {
            "model_name": "valuesimplex-ai-lab/FinBERT2-large",
            "description": "熵简科技FinBERT2-large模型",
            "max_length": 512
        }
    }

    def __new__(cls) -> Self:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._models: dict[str, tuple[AutoTokenizer, AutoModelForSequenceClassification]] = {}
            self._current_model_key: str | None = None
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._initialized = True
            logger.info(f"NLP模型管理器初始化完成，使用设备: {self._device}")

    def load_model(self, model_key: str = "finbert2-large") -> bool:
        """加载指定的模型

        Args:
            model_key: 模型键名，支持的模型见SUPPORTED_MODELS

        Returns:
            bool: 加载是否成功
        """
        if model_key not in self.SUPPORTED_MODELS:
            logger.error(f"不支持的模型: {model_key}，支持的模型: {list(self.SUPPORTED_MODELS.keys())}")
            return False

        if model_key in self._models:
            logger.info(f"模型 {model_key} 已加载，切换为当前模型")
            self._current_model_key = model_key
            return True

        try:
            model_config = self.SUPPORTED_MODELS[model_key]
            model_name = model_config["model_name"]

            logger.info(f"开始加载模型: {model_name}")

            # 加载tokenizer和模型
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)  # type: ignore

            # 移动模型到指定设备
            model.to(self._device)
            model.eval()

            # 缓存模型
            self._models[model_key] = (tokenizer, model)
            self._current_model_key = model_key

            logger.info(f"模型 {model_key} 加载成功")
            return True

        except Exception as e:
            logger.error(f"加载模型 {model_key} 失败: {str(e)}")
            return False

    def predict_sentiment(self, text: str) -> dict[str, float]:
        """预测文本情绪

        Args:
            text: 待分析的文本

        Returns:
            Dict[str, float]: 情绪分析结果，包含positive、negative、neutral的概率
        """
        if not self._current_model_key or self._current_model_key not in self._models:
            logger.warning("没有可用的模型，尝试加载默认模型")
            if not self.load_model():
                raise RuntimeError("无法加载模型")

        # 确保current_model_key不为None
        current_key = self._current_model_key
        if current_key is None:
            raise RuntimeError("模型键为空")

        tokenizer, model = self._models[current_key]
        # 类型注解确保正确的方法调用
        tokenizer = tokenizer  # AutoTokenizer
        model = model  # AutoModelForSequenceClassification
        model_config = self.SUPPORTED_MODELS[current_key]

        try:
            # 文本预处理和tokenization
            inputs = tokenizer(  # type: ignore
                text,
                return_tensors="pt",
                max_length=model_config["max_length"],
                truncation=True,
                padding=True
            )

            # 移动输入到指定设备
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # 模型推理
            with torch.no_grad():
                outputs = model(**inputs)  # type: ignore
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # 转换为概率分布
            probs = predictions.cpu().numpy()[0]

            # 根据模型输出格式调整标签映射
            if len(probs) == 3:
                # 三分类：negative, neutral, positive
                result = {
                    "negative": float(probs[0]),
                    "neutral": float(probs[1]),
                    "positive": float(probs[2])
                }
            else:
                # 二分类：negative, positive
                result = {
                    "negative": float(probs[0]),
                    "neutral": 0.0,
                    "positive": float(probs[1])
                }

            return result

        except Exception as e:
            logger.error(f"情绪预测失败: {str(e)}")
            raise

    def switch_model(self, model_key: str) -> bool:
        """切换当前使用的模型

        Args:
            model_key: 目标模型键名

        Returns:
            bool: 切换是否成功
        """
        if model_key not in self.SUPPORTED_MODELS:
            logger.error(f"不支持的模型: {model_key}")
            return False

        if model_key not in self._models:
            logger.info(f"模型 {model_key} 未加载，开始加载")
            return self.load_model(model_key)

        self._current_model_key = model_key
        logger.info(f"已切换到模型: {model_key}")
        return True

    def get_model_info(self) -> dict[str, Any]:
        """获取当前模型信息

        Returns:
            Dict: 模型信息
        """
        if not self._current_model_key:
            return {"current_model": None, "loaded_models": list(self._models.keys())}

        current_config = self.SUPPORTED_MODELS[self._current_model_key]
        return {
            "current_model": self._current_model_key,
            "current_model_name": current_config["model_name"],
            "current_model_description": current_config["description"],
            "loaded_models": list(self._models.keys()),
            "supported_models": list(self.SUPPORTED_MODELS.keys()),
            "device": str(self._device)
        }

    def unload_model(self, model_key: str) -> bool:
        """卸载指定模型以释放内存

        Args:
            model_key: 要卸载的模型键名

        Returns:
            bool: 卸载是否成功
        """
        if model_key not in self._models:
            logger.warning(f"模型 {model_key} 未加载")
            return False

        del self._models[model_key]

        if self._current_model_key == model_key:
            self._current_model_key = None

        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"模型 {model_key} 已卸载")
        return True

    def clear_all_models(self) -> None:
        """清理所有已加载的模型"""
        self._models.clear()
        self._current_model_key = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("所有模型已清理")
