"""情绪因子计算器

基于新闻文本的情绪分析计算情绪因子。
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from ...clients.data_collector_client import DataCollectorClient
from ...nlp.sentiment_analyzer import SentimentAnalyzer


class SentimentFactorCalculator:
    """情绪因子计算器

    基于新闻文本的情绪分析计算股票的情绪因子。
    """

    def __init__(self) -> None:
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_client = DataCollectorClient()

        # 情绪因子权重配置
        self.weights = {
            "title_weight": 0.4,      # 标题权重
            "content_weight": 0.6,    # 内容权重
            "time_decay_factor": 0.1,  # 时间衰减因子
            "volume_weight": 0.2      # 新闻量权重
        }

    def _calculate_time_weight(self, news_time: datetime, current_time: datetime) -> float:
        """计算时间权重

        Args:
            news_time: 新闻时间
            current_time: 当前时间

        Returns:
            float: 时间权重（0-1）
        """
        time_diff = (current_time - news_time).total_seconds() / 3600  # 小时差

        # 指数衰减：权重 = exp(-decay_factor * hours)
        import math
        weight = math.exp(-self.weights["time_decay_factor"] * time_diff)
        return max(0.01, weight)  # 最小权重0.01

    def _get_degree_modifier(self, text: str) -> float:
        """获取程度修饰词权重

        Args:
            text: 文本内容

        Returns:
            float: 程度修饰权重
        """
        degree_words = {
            "大幅": 1.5, "显著": 1.4, "明显": 1.3, "大量": 1.3,
            "急剧": 1.6, "暴涨": 1.8, "暴跌": 1.8, "飙升": 1.7,
            "轻微": 0.7, "略微": 0.6, "小幅": 0.8, "稍微": 0.7
        }

        max_modifier = 1.0
        for word, weight in degree_words.items():
            if word in text:
                max_modifier = max(max_modifier, weight)

        return max_modifier

    def calculate_news_sentiment_score(self, news_data: list[dict]) -> dict[str, float]:
        """计算新闻情绪分数

        Args:
            news_data: 新闻数据列表，每个元素包含title, content, publish_time等字段

        Returns:
            Dict[str, float]: 情绪分数结果
        """
        if not news_data:
            return {
                "sentiment_score": 0.0,
                "positive_score": 0.0,
                "negative_score": 0.0,
                "neutral_score": 1.0,
                "news_count": 0,
                "confidence": 0.0
            }

        current_time = datetime.now()
        total_weighted_score = 0.0
        total_weight = 0.0

        positive_sum = 0.0
        negative_sum = 0.0
        neutral_sum = 0.0

        confidence_scores = []

        for news in news_data:
            try:
                # 获取新闻内容
                title = news.get("title", "")
                content = news.get("content", "")
                publish_time = news.get("publish_time")

                if publish_time is None:
                    continue  # 跳过没有发布时间的新闻

                if isinstance(publish_time, str):
                    publish_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                elif not isinstance(publish_time, datetime):
                    continue  # 跳过时间格式不正确的新闻

                # 分析标题情绪
                title_sentiment = self.sentiment_analyzer.analyze_sentiment(title)

                # 分析内容情绪
                content_sentiment = self.sentiment_analyzer.analyze_sentiment(content)

                # 计算综合情绪分数
                title_score = (
                    title_sentiment["sentiment_scores"]["positive"] -
                    title_sentiment["sentiment_scores"]["negative"]
                )

                content_score = (
                    content_sentiment["sentiment_scores"]["positive"] -
                    content_sentiment["sentiment_scores"]["negative"]
                )

                # 加权平均
                combined_score = (
                    self.weights["title_weight"] * title_score +
                    self.weights["content_weight"] * content_score
                )

                # 程度修饰词调整
                title_modifier = self._get_degree_modifier(title)
                content_modifier = self._get_degree_modifier(content)
                modifier = max(title_modifier, content_modifier)

                combined_score *= modifier

                # 时间权重
                time_weight = self._calculate_time_weight(publish_time, current_time)

                # 最终权重
                final_weight = time_weight

                # 累积加权分数
                total_weighted_score += combined_score * final_weight
                total_weight += final_weight

                # 累积各类情绪分数
                avg_positive = (
                    self.weights["title_weight"] * title_sentiment["sentiment_scores"]["positive"] +
                    self.weights["content_weight"] * content_sentiment["sentiment_scores"]["positive"]
                )
                avg_negative = (
                    self.weights["title_weight"] * title_sentiment["sentiment_scores"]["negative"] +
                    self.weights["content_weight"] * content_sentiment["sentiment_scores"]["negative"]
                )
                avg_neutral = (
                    self.weights["title_weight"] * title_sentiment["sentiment_scores"]["neutral"] +
                    self.weights["content_weight"] * content_sentiment["sentiment_scores"]["neutral"]
                )

                positive_sum += avg_positive * final_weight
                negative_sum += avg_negative * final_weight
                neutral_sum += avg_neutral * final_weight

                # 收集置信度
                avg_confidence = (
                    self.weights["title_weight"] * title_sentiment["confidence"] +
                    self.weights["content_weight"] * content_sentiment["confidence"]
                )
                confidence_scores.append(avg_confidence)

            except Exception as e:
                logger.error(f"处理新闻数据失败: {str(e)}")
                continue

        # 计算最终结果
        if total_weight > 0:
            final_sentiment_score = total_weighted_score / total_weight
            final_positive = positive_sum / total_weight
            final_negative = negative_sum / total_weight
            final_neutral = neutral_sum / total_weight
            final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        else:
            final_sentiment_score = 0.0
            final_positive = 0.0
            final_negative = 0.0
            final_neutral = 1.0
            final_confidence = 0.0

        return {
            "sentiment_score": final_sentiment_score,
            "positive_score": final_positive,
            "negative_score": final_negative,
            "neutral_score": final_neutral,
            "news_count": len(news_data),
            "confidence": final_confidence
        }

    async def calculate_stock_sentiment_factor(self, stock_code: str, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """计算股票情绪因子

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 情绪因子结果
        """
        try:
            # 获取新闻数据
            news_data = await self.data_client.get_news_data(
                symbol=stock_code,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )

            if not news_data:
                logger.warning(f"股票 {stock_code} 在指定时间范围内没有新闻数据")
                return {
                    "stock_code": stock_code,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "sentiment_factor": 0.0,
                    "sentiment_details": {
                        "sentiment_score": 0.0,
                        "positive_score": 0.0,
                        "negative_score": 0.0,
                        "neutral_score": 1.0,
                        "news_count": 0,
                        "confidence": 0.0
                    },
                    "calculation_time": datetime.now().isoformat()
                }

            # 计算情绪分数
            sentiment_result = self.calculate_news_sentiment_score(news_data)

            # 情绪因子 = 情绪分数，范围 [-1, 1]
            sentiment_factor = sentiment_result["sentiment_score"]

            # 新闻量调整：新闻越多，因子越可靠
            news_count = sentiment_result["news_count"]
            volume_adjustment = min(1.0, news_count / 10.0)  # 10条新闻为基准

            # 最终因子值
            final_factor = sentiment_factor * volume_adjustment

            return {
                "stock_code": stock_code,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "sentiment_factor": final_factor,
                "sentiment_details": sentiment_result,
                "volume_adjustment": volume_adjustment,
                "calculation_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"计算股票 {stock_code} 情绪因子失败: {str(e)}")
            raise

    async def calculate_batch_sentiment_factors(self, stock_codes: list[str], date: datetime) -> list[dict[str, Any]]:
        """批量计算情绪因子

        Args:
            stock_codes: 股票代码列表
            date: 计算日期

        Returns:
            List[Dict]: 情绪因子结果列表
        """
        results = []

        # 计算时间范围：当前日期前7天的新闻
        end_date = date
        start_date = date - timedelta(days=7)

        for stock_code in stock_codes:
            try:
                result = await self.calculate_stock_sentiment_factor(stock_code, start_date, end_date)
                results.append(result)

            except Exception as e:
                logger.error(f"计算股票 {stock_code} 情绪因子失败: {str(e)}")
                # 添加错误结果
                results.append({
                    "stock_code": stock_code,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "sentiment_factor": 0.0,
                    "error": str(e),
                    "calculation_time": datetime.now().isoformat()
                })

        return results

    async def get_sentiment_trend(self, stock_code: str, days: int = 30) -> dict[str, Any]:
        """获取情绪趋势

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            Dict: 情绪趋势数据
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 按天计算情绪因子
        daily_factors = []
        current_date = start_date

        while current_date <= end_date:
            day_start = current_date
            day_end = current_date + timedelta(days=1)

            try:
                factor_result = await self.calculate_stock_sentiment_factor(stock_code, day_start, day_end)
                daily_factors.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sentiment_factor": factor_result["sentiment_factor"],
                    "news_count": factor_result["sentiment_details"]["news_count"]
                })
            except Exception as e:
                logger.warning(f"计算 {current_date.strftime('%Y-%m-%d')} 情绪因子失败: {str(e)}")
                daily_factors.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sentiment_factor": 0.0,
                    "news_count": 0
                })

            current_date += timedelta(days=1)

        # 计算趋势统计
        factors = [item["sentiment_factor"] for item in daily_factors]

        if factors:
            avg_sentiment = sum(factors) / len(factors)
            max_sentiment = max(factors)
            min_sentiment = min(factors)

            # 计算趋势方向
            recent_avg = sum(factors[-7:]) / min(7, len(factors))  # 最近7天平均
            early_avg = sum(factors[:7]) / min(7, len(factors))    # 前7天平均

            trend_direction = "stable"
            if recent_avg > early_avg + 0.1:
                trend_direction = "improving"
            elif recent_avg < early_avg - 0.1:
                trend_direction = "declining"
        else:
            avg_sentiment = 0.0
            max_sentiment = 0.0
            min_sentiment = 0.0
            trend_direction = "stable"

        return {
            "stock_code": stock_code,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "daily_factors": daily_factors,
            "statistics": {
                "average_sentiment": avg_sentiment,
                "max_sentiment": max_sentiment,
                "min_sentiment": min_sentiment,
                "trend_direction": trend_direction
            }
        }
