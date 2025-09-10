"""情感因子服务层"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from loguru import logger
from sqlalchemy.orm import Session

from ..calculators.sentiment import SentimentFactorCalculator
from ..dao import NewsSentimentFactorDAO
from ..models.schemas import (
    SentimentFactorRequest,
    SentimentFactorResponse,
    BatchSentimentFactorRequest,
    BatchSentimentFactorResponse,
    SentimentTrendRequest,
    SentimentTrendResponse,
)
from ...config.database import get_db_session


class SentimentFactorService:
    """情感因子服务类
    
    负责情感因子的业务逻辑编排，包括：
    - 情感因子计算
    - 数据库事务管理
    - 业务规则验证
    """
    
    def __init__(self):
        """初始化情感因子服务"""
        self.sentiment_calculator = SentimentFactorCalculator()
        self._sentiment_dao: Optional[NewsSentimentFactorDAO] = None
    
    def _get_dao(self) -> NewsSentimentFactorDAO:
        """获取DAO实例（懒加载单例模式）
        
        Returns:
            NewsSentimentFactorDAO: DAO实例
        """
        if self._sentiment_dao is None:
            db_session: Session = next(get_db_session())
            self._sentiment_dao = NewsSentimentFactorDAO(db_session)
        return self._sentiment_dao
    
    async def calculate_sentiment_factor(self, request: SentimentFactorRequest) -> SentimentFactorResponse:
        """计算单个股票情感因子
        
        Args:
            request: 情感因子计算请求
            
        Returns:
            SentimentFactorResponse: 情感因子响应
            
        Raises:
            ValueError: 当未找到新闻数据时
            Exception: 计算过程中的其他错误
        """
        try:
            logger.info(f"开始计算情感因子: {request.stock_code} ({request.date})")
            
            # 计算日期范围
            start_date = datetime.strptime(request.date, "%Y-%m-%d") - timedelta(days=request.time_window)
            end_date = datetime.strptime(request.date, "%Y-%m-%d")
            
            # 计算情感因子
            result = await self.sentiment_calculator.calculate_stock_sentiment_factor(
                stock_code=request.stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if result is None:
                raise ValueError(f"未找到股票 {request.stock_code} 在指定时间范围内的新闻数据")
            
            # 保存到数据库
            sentiment_dao = self._get_dao()
            sentiment_dao.create(
                stock_code=request.stock_code,
                factor_value=result["sentiment_factor"],
                calculation_date=request.date,
                news_count=result["news_count"]
            )
            
            logger.info(f"情感因子计算完成: {request.stock_code} = {result['sentiment_factor']}")
            
            # 构造响应数据
            return SentimentFactorResponse(
                stock_code=request.stock_code,
                date=request.date,
                sentiment_factors={
                    "overall": result["sentiment_factor"],
                    "positive": result["positive_score"],
                    "negative": result["negative_score"],
                    "neutral": result["neutral_score"]
                },
                source_weights={"news": 1.0},
                data_counts={"news": result["news_count"]}
            )
            
        except Exception as e:
            logger.error(f"计算情感因子失败: {e}")
            raise
    
    async def batch_calculate_sentiment_factors(self, request: BatchSentimentFactorRequest) -> BatchSentimentFactorResponse:
        """批量计算情感因子
        
        Args:
            request: 批量情感因子计算请求
            
        Returns:
            BatchSentimentFactorResponse: 批量计算响应
        """
        try:
            logger.info(f"开始批量计算情感因子: {len(request.stock_codes)} 只股票")
            
            # 计算日期范围
            end_date = datetime.strptime(request.calculation_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=request.days_back)
            
            results = []
            errors = []
            successful_count = 0
            
            # 批量计算情感因子
            calculation_date = datetime.strptime(request.calculation_date, "%Y-%m-%d")
            batch_results = await self.sentiment_calculator.calculate_batch_sentiment_factors(
                request.stock_codes,
                calculation_date
            )
            
            for i, stock_code in enumerate(request.stock_codes):
                try:
                    # 获取对应的计算结果
                    result = batch_results[i] if i < len(batch_results) else None
                    if not result:
                        errors.append({
                            "stock_code": stock_code,
                            "error": "未找到新闻数据"
                        })
                        continue
                    
                    # 保存到数据库
                    start_date = calculation_date - timedelta(days=7)
                    await NewsSentimentFactorDAO.save_sentiment_factor(
                        stock_code=stock_code,
                        sentiment_factor=result["sentiment_factor"],
                        positive_score=result["positive_score"],
                        negative_score=result["negative_score"],
                        neutral_score=result["neutral_score"],
                        confidence=result["confidence"],
                        news_count=result["news_count"],
                        calculation_date=request.calculation_date,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=request.calculation_date,
                        volume_adjustment=1.0
                    )
                    results.append(result)
                    successful_count += 1
                    
                except Exception as e:
                    logger.error(f"计算股票 {stock_code} 情感因子失败: {e}")
                    errors.append({
                        "stock_code": stock_code,
                        "error": str(e)
                    })
            
            # 转换结果格式
            response_results = []
            for result in results:
                if result:
                    response_results.append(SentimentFactorResponse(
                        stock_code=result["stock_code"],
                        date=request.calculation_date,
                        sentiment_factors={
                            "overall": result["sentiment_factor"],
                            "positive": result["positive_score"],
                            "negative": result["negative_score"],
                            "neutral": result["neutral_score"]
                        },
                        source_weights={"news": 1.0},
                        data_counts={"news": result["news_count"]}
                    ))
            
            logger.info(f"批量计算完成: 成功 {successful_count}/{len(request.stock_codes)}")
            
            return BatchSentimentFactorResponse(
                calculation_date=request.calculation_date,
                total_stocks=len(request.stock_codes),
                successful_stocks=successful_count,
                failed_stocks=len(errors),
                results=response_results,
                errors=errors if errors else None,
            )
            
        except Exception as e:
            logger.error(f"批量计算情感因子失败: {e}")
            raise
    
    async def get_sentiment_factor(self, stock_code: str, date: str) -> Optional[Dict[str, Any]]:
        """获取单个股票的情感因子数据
        
        Args:
            stock_code: 股票代码
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            情感因子数据或None
        """
        try:
            dao = self._get_dao()
            factors = dao.get_by_stock_and_date(stock_code, date)
            
            if not factors:
                return None
                
            # 取第一个因子数据（通常一个股票一天只有一条记录）
            factor = factors[0]
            return {
                "id": factor.id,
                "stock_code": factor.stock_code,
                "factor_value": factor.factor_value,
                "calculation_date": factor.calculation_date.isoformat(),
                "news_count": factor.news_count,
                "created_at": factor.created_at.isoformat(),
                "updated_at": factor.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"获取情感因子数据失败: {e}")
            raise
    
    async def get_sentiment_factors_by_date(self, date: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指定日期的所有情感因子数据
        
        Args:
            date: 日期 (YYYY-MM-DD)
            limit: 返回数量限制
            
        Returns:
            情感因子数据列表
        """
        try:
            dao = self._get_dao()
            factors = await dao.get_sentiment_factors_by_date(date, limit)
            
            # 转换为字典格式
            result = []
            for factor in factors:
                result.append({
                    "stock_code": factor.stock_code,
                    "date": factor.date,
                    "sentiment_factors": factor.sentiment_factors,
                    "source_weights": factor.source_weights,
                    "data_counts": factor.data_counts
                })
            
            return result
        except Exception as e:
            logger.error(f"获取日期情感因子数据失败: {e}")
            raise
    
    async def get_sentiment_trend(self, request: SentimentTrendRequest) -> SentimentTrendResponse:
        """获取股票情感趋势
        
        Args:
            request: 情感趋势查询请求
            
        Returns:
            SentimentTrendResponse: 趋势数据响应
        """
        try:
            dao = self._get_dao()
            
            # 获取趋势数据
            trend_data = await dao.get_sentiment_trend(
                stock_code=request.stock_code,
                days=request.days,
            )
            
            # 获取统计数据
            statistics = await dao.get_sentiment_statistics(
                stock_code=request.stock_code,
                days=request.days,
            )
            
            return SentimentTrendResponse(
                stock_code=request.stock_code,
                period=f"{request.days}天",
                daily_factors=trend_data,
                statistics=statistics,
            )
            
        except Exception as e:
            logger.error(f"获取情感趋势失败: {e}")
            raise