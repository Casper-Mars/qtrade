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

        # 积极词汇库
        self.positive_words = {
            "上涨", "增长", "盈利", "利好", "看好", "乐观", "强势", "突破", "创新高",
            "收益", "回升", "反弹", "买入", "推荐", "优秀", "超预期", "利润", "增收",
            "扩张", "发展", "机会", "潜力", "优势", "成功", "改善", "提升", "增加"
        }

        # 消极词汇库
        self.negative_words = {
            "下跌", "下降", "亏损", "利空", "看空", "悲观", "弱势", "跌破", "创新低",
            "损失", "下滑", "暴跌", "卖出", "风险", "糟糕", "低于预期", "减少", "萎缩",
            "困难", "挑战", "威胁", "问题", "失败", "恶化", "担忧"
        }

        # 程度修饰词
        self.degree_modifiers = {
            "极其": 2.0, "非常": 1.8, "十分": 1.6, "相当": 1.4, "比较": 1.2,
            "稍微": 0.8, "略微": 0.6, "有点": 0.7, "一点": 0.5, "些许": 0.4
        }

        # 否定词
        self.negation_words = {"不", "没", "无", "非", "未", "否", "别", "勿"}

    def preprocess_text(self, text: str) -> str:
        """文本预处理

        Args:
            text: 原始文本

        Returns:
            str: 预处理后的文本
        """
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # 移除邮箱
        text = re.sub(r'\S+@\S+', '', text)

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？；：""''（）【】]', '', text)

        # 去除首尾空格
        text = text.strip()

        return text

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        """提取关键词

        Args:
            text: 文本内容

        Returns:
            Dict[str, List[str]]: 包含积极和消极关键词的字典
        """
        positive_keywords = []
        negative_keywords = []

        for word in self.positive_words:
            if word in text:
                positive_keywords.append(word)

        for word in self.negative_words:
            if word in text:
                negative_keywords.append(word)

        return {
            "positive": positive_keywords,
            "negative": negative_keywords
        }

    def calculate_rule_based_sentiment(self, text: str) -> dict[str, float]:
        """基于规则的情绪计算

        Args:
            text: 文本内容

        Returns:
            Dict[str, float]: 情绪分数
        """
        if not text:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

        positive_score = 0.0
        negative_score = 0.0

        # 分词（简单按字符处理）
        words = list(text)

        i = 0
        while i < len(words):
            words[i]

            # 检查程度修饰词
            degree = 1.0
            for modifier, weight in self.degree_modifiers.items():
                if text[i:i+len(modifier)] == modifier:
                    degree = weight
                    i += len(modifier) - 1
                    break

            # 检查否定词
            negation = False
            for neg_word in self.negation_words:
                if text[i:i+len(neg_word)] == neg_word:
                    negation = True
                    break

            # 检查情绪词
            for pos_word in self.positive_words:
                if text[i:i+len(pos_word)] == pos_word:
                    score = degree
                    if negation:
                        negative_score += score
                    else:
                        positive_score += score
                    i += len(pos_word) - 1
                    break

            for neg_word in self.negative_words:
                if text[i:i+len(neg_word)] == neg_word:
                    score = degree
                    if negation:
                        positive_score += score
                    else:
                        negative_score += score
                    i += len(neg_word) - 1
                    break

            i += 1

        # 归一化
        total = positive_score + negative_score
        if total > 0:
            positive_score /= total
            negative_score /= total
            neutral_score = 0.0
        else:
            positive_score = 0.0
            negative_score = 0.0
            neutral_score = 1.0

        return {
            "positive": positive_score,
            "negative": negative_score,
            "neutral": neutral_score
        }

    def analyze_sentiment(self, text: str, use_model: bool = True, model_weight: float = 0.7) -> dict[str, Any]:
        """综合情绪分析

        Args:
            text: 待分析文本
            use_model: 是否使用深度学习模型
            model_weight: 模型结果权重（0-1）

        Returns:
            Dict: 情绪分析结果
        """
        if not text:
            return {
                "sentiment_scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "dominant_sentiment": "neutral",
                "confidence": 0.0,
                "keywords": {"positive": [], "negative": []},
                "processed_text": ""
            }

        # 文本预处理
        processed_text = self.preprocess_text(text)

        if not processed_text:
            return {
                "sentiment_scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "dominant_sentiment": "neutral",
                "confidence": 0.0,
                "keywords": {"positive": [], "negative": []},
                "processed_text": processed_text
            }

        # 提取关键词
        keywords = self.extract_keywords(processed_text)

        # 基于规则的情绪分析
        rule_scores = self.calculate_rule_based_sentiment(processed_text)

        # 最终情绪分数
        final_scores = rule_scores.copy()

        # 如果使用模型且文本长度适合
        if use_model and len(processed_text) > 5:
            try:
                # 确保模型已加载
                if not self.model_manager.get_model_info()["current_model"]:
                    logger.info("加载默认情绪分析模型")
                    self.model_manager.load_model()

                # 使用模型预测
                model_scores = self.model_manager.predict_sentiment(processed_text)

                # 加权融合
                for key in final_scores:
                    final_scores[key] = (
                        model_weight * model_scores.get(key, 0.0) +
                        (1 - model_weight) * rule_scores[key]
                    )

            except Exception as e:
                logger.warning(f"模型预测失败，使用规则方法: {str(e)}")

        # 确定主导情绪
        dominant_sentiment = max(final_scores, key=lambda x: final_scores[x])
        confidence = final_scores[dominant_sentiment]

        return {
            "sentiment_scores": final_scores,
            "dominant_sentiment": dominant_sentiment,
            "confidence": confidence,
            "keywords": keywords,
            "processed_text": processed_text,
            "rule_scores": rule_scores,
            "model_used": use_model
        }

    def batch_analyze(self, texts: list[str], use_model: bool = True) -> list[dict[str, Any]]:
        """批量情绪分析

        Args:
            texts: 文本列表
            use_model: 是否使用深度学习模型

        Returns:
            List[Dict]: 分析结果列表
        """
        results = []

        for text in texts:
            try:
                result = self.analyze_sentiment(text, use_model=use_model)
                results.append(result)
            except Exception as e:
                logger.error(f"分析文本失败: {str(e)}")
                results.append({
                    "sentiment_scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                    "dominant_sentiment": "neutral",
                    "confidence": 0.0,
                    "keywords": {"positive": [], "negative": []},
                    "processed_text": text,
                    "error": str(e)
                })

        return results

    def get_sentiment_summary(self, texts: list[str]) -> dict[str, Any]:
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

        results = self.batch_analyze(texts)

        # 统计情绪分布
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_scores = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        for result in results:
            dominant = result["dominant_sentiment"]
            sentiment_counts[dominant] += 1

            for key, score in result["sentiment_scores"].items():
                total_scores[key] += score

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
