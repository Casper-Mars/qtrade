package routes

import (
	"data-collector/internal/api/handler"
	"data-collector/internal/services"
	"data-collector/internal/storage"

	"github.com/gin-gonic/gin"
)

// SetupNewsRoutes 设置新闻相关路由
func SetupNewsRoutes(router *gin.RouterGroup, newsRepo storage.NewsRepository, newsService *services.NewsService) {
	// 创建新闻处理器
	newsHandler := handler.NewNewsHandler(newsRepo, newsService)

	// 新闻管理路由组
	newsGroup := router.Group("/news")
	{
		// 获取新闻列表
		newsGroup.GET("", newsHandler.GetNewsList)
		
		// 根据ID获取新闻详情 (使用查询参数: ?id=xxx)
		newsGroup.GET("/detail", newsHandler.GetNewsByID)
		
		// 根据时间范围获取新闻
		newsGroup.GET("/time-range", newsHandler.GetNewsByTimeRange)
		
		// 搜索新闻
		newsGroup.GET("/search", newsHandler.SearchNews)
		
		// 根据股票代码获取新闻 (使用查询参数: ?stock_code=xxx)
		newsGroup.GET("/by-stock", newsHandler.GetNewsByStock)
		
		// 手动触发新闻采集
		newsGroup.POST("/collect", newsHandler.TriggerCollection)
		
		// 获取新闻服务状态
		newsGroup.GET("/status", newsHandler.GetServiceStatus)
	}
}