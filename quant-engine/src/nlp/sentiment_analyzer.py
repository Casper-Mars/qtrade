"""情绪分析器

提供文本预处理和情绪分析功能。
"""

import re
from typing import Any

from loguru import logger

from .model_manager import NLPModelManager


class SentimentAnalyzer:
    """情绪分析器

    提供文本预处理和基于FinBERT的情绪分析功能。
    """

    def __init__(self) -> None:
        self.model_manager = NLPModelManager()

    def preprocess_text(self, text: str) -> str:
        """文本预处理（简化版，主要预处理由data-collector服务完成）

        Args:
            text: 原始文本

        Returns:
            str: 预处理后的文本
        """
        if not text:
            return ""

        # 简单的空白字符规范化
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text





    async def analyze_sentiment(self, text: str, title: str | None = None) -> dict[str, float]:
        """分析文本情绪，返回情绪分数和置信度

        根据技术方案文档要求，主要使用NLP模型进行情绪分析

        Args:
            text: 待分析文本
            title: 可选的标题文本

        Returns:
            Dict: 情绪分析结果
            {
                "positive": 0.7,    # 积极情绪概率
                "negative": 0.2,    # 消极情绪概率
                "neutral": 0.1,     # 中性情绪概率
                "confidence": 0.85, # 预测置信度
            }
        """
        if not text:
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "confidence": 1.0
            }

        # 文本预处理
        processed_text = self.preprocess_text(text)
        if title:
            title_processed = self.preprocess_text(title)
            # 标题权重更高，拼接到前面
            processed_text = f"{title_processed} {processed_text}"

        if not processed_text:
            return {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "confidence": 1.0
            }

        # 确保模型已加载
        model_info = self.model_manager.get_model_info()
        if not model_info["current_model"]:
            logger.info("加载默认情绪分析模型")
            self.model_manager.load_model()

        # 使用NLP模型进行情绪分析
        model_result = self.model_manager.predict_sentiment(processed_text)

        # 提取情绪分数
        positive = model_result.get("positive", 0.0)
        negative = model_result.get("negative", 0.0)
        neutral = model_result.get("neutral", 0.0)

        # 计算置信度（最高情绪分数）
        confidence = max(positive, negative, neutral)

        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "confidence": confidence
        }

    async def batch_analyze(self, texts: list[str]) -> list[dict[str, float]]:
        """批量情绪分析

        Args:
            texts: 文本列表

        Returns:
            List[Dict]: 分析结果列表
        """
        results = []

        for text in texts:
            try:
                result = await self.analyze_sentiment(text)
                results.append(result)
            except Exception as e:
                logger.error(f"分析文本失败: {str(e)}")
                results.append({
                    "positive": 0.0,
                    "negative": 0.0,
                    "neutral": 1.0,
                    "confidence": 0.0
                })

        return results

    async def get_sentiment_summary(self, texts: list[str]) -> dict[str, Any]:
        """获取文本集合的情绪摘要

        Args:
            texts: 文本列表

        Returns:
            Dict: 情绪摘要统计
        """
        if not texts:
            return {
                "total_count": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                "average_scores": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                "dominant_sentiment": "neutral"
            }

        results = await self.batch_analyze(texts)

        # 统计情绪分布
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        for result in results:
            # 确定主导情绪
            dominant = max(result, key=lambda x: result[x] if x in ["positive", "negative", "neutral"] else 0)
            sentiment_counts[dominant] += 1

            # 累积分数
            total_scores["positive"] += result["positive"]
            total_scores["negative"] += result["negative"]
            total_scores["neutral"] += result["neutral"]

        # 计算平均分数
        count = len(results)
        average_scores = {key: total_scores[key] / count for key in total_scores}

        # 确定整体主导情绪
        overall_dominant = max(average_scores, key=lambda x: average_scores[x])

        return {
            "total_count": count,
            "sentiment_distribution": sentiment_counts,
            "average_scores": average_scores,
            "dominant_sentiment": overall_dominant
        }
