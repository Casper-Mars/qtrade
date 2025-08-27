package api

import (
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	ginSwagger "github.com/swaggo/gin-swagger"
	swaggerFiles "github.com/swaggo/files"

	"data-collector/internal/api/handler"
	"data-collector/internal/api/middleware"
	"data-collector/internal/api/routes"
	"data-collector/internal/collectors/stock"
	"data-collector/internal/common/validator"
	"data-collector/internal/config"
	"data-collector/internal/services"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// Router 路由器结构体
type Router struct {
	engine             *gin.Engine
	systemHandler      *handler.SystemHandler
	stockHandler       *handler.StockHandler
	stockQuoteHandler  *handler.StockQuoteHandler
	adjFactorHandler   *handler.AdjFactorHandler
	financialHandler   *handler.FinancialHandler
}

// NewRouter 创建新的路由实例
func NewRouter() *Router {
	// 设置Gin模式
	gin.SetMode(gin.ReleaseMode)

	// 创建Gin引擎
	engine := gin.New()

	// 创建系统处理器
	systemHandler := handler.NewSystemHandler("1.0.0", time.Now().Format("2006-01-02 15:04:05"))

	// 创建股票处理器
	stockHandler := createStockHandler()

	// 创建股票行情处理器
	stockQuoteHandler := createStockQuoteHandler()

	// 创建复权因子处理器
	adjFactorHandler := createAdjFactorHandler()

	// 创建财务数据处理器
	financialHandler := createFinancialHandler()

	return &Router{
		engine:             engine,
		systemHandler:      systemHandler,
		stockHandler:       stockHandler,
		stockQuoteHandler:  stockQuoteHandler,
		adjFactorHandler:   adjFactorHandler,
		financialHandler:   financialHandler,
	}
}

// SetupMiddleware 设置中间件
func (r *Router) SetupMiddleware() {
	// 异常恢复中间件
	r.engine.Use(middleware.RecoveryMiddleware())

	// 请求日志中间件
	r.engine.Use(middleware.LoggerMiddleware())

	// 请求ID中间件
	r.engine.Use(middleware.RequestIDMiddleware())
}

// SetupRoutes 设置路由
func (r *Router) SetupRoutes() {
	// 系统级路由
	r.setupSystemRoutes()

	// API路由组
	r.setupAPIRoutes()
}

// setupSystemRoutes 设置系统级路由
func (r *Router) setupSystemRoutes() {
	// 健康检查
	r.engine.GET("/health", r.systemHandler.Health)

	// 版本信息
	r.engine.GET("/version", r.systemHandler.Version)

	// 系统指标
	r.engine.GET("/metrics", r.systemHandler.Metrics)

	// 数据库健康检查
	r.engine.GET("/health/database", r.systemHandler.DatabaseHealth)

	// Swagger API文档
	r.engine.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}

// setupAPIRoutes 设置API路由组
func (r *Router) setupAPIRoutes() {
	// API v1路由组
	v1 := r.engine.Group("/api/v1")
	{
		// 股票数据采集路由组
		collect := v1.Group("/collect")
		{
			// 股票基础信息采集
			collect.POST("/stock/basic", r.stockHandler.CollectStockBasic)
			
			// 股票行情数据采集
			collect.POST("/stock/quotes", r.stockQuoteHandler.CollectQuotesByDate)
			collect.POST("/stock/quotes/range", r.stockQuoteHandler.CollectQuotesByDateRange)
			collect.POST("/stock/quotes/latest", r.stockQuoteHandler.CollectLatestQuotes)
			
			// 复权因子数据采集
			collect.POST("/stock/adj-factors", r.adjFactorHandler.CollectByDate)
			collect.POST("/stock/adj-factors/range", r.adjFactorHandler.CollectByDateRange)
			collect.POST("/stock/adj-factors/latest", r.adjFactorHandler.CollectLatest)
		}

		// 采集器信息路由组
		collector := v1.Group("/collector")
		{
			// 获取股票采集器信息
			collector.GET("/stock/info", r.stockHandler.GetCollectorInfo)
		}

		// 股票数据查询路由组
		stocks := v1.Group("/stocks")
		{
			// 股票行情数据查询
			quotes := stocks.Group("/quotes")
			{
				// 按股票代码查询行情 (使用查询参数: ?symbol=xxx)
				quotes.GET("/by-symbol", r.stockQuoteHandler.GetQuotesBySymbol)
				// 按日期查询行情 (使用查询参数: ?date=xxx)
				quotes.GET("/by-date", r.stockQuoteHandler.GetQuotesByDate)
			}
			
			// 复权因子数据查询
			adjFactors := stocks.Group("/adj-factors")
			{
				// 按股票代码查询复权因子 (使用查询参数: ?symbol=xxx)
				adjFactors.GET("/by-symbol", r.adjFactorHandler.GetAdjFactorsBySymbol)
				// 按日期查询复权因子 (使用查询参数: ?date=xxx)
				adjFactors.GET("/by-date", r.adjFactorHandler.GetAdjFactorByDate)
			}
		}

		// 财务数据相关路由组
		financial := v1.Group("/financial")
		{
			// 财务指标采集
			financial.GET("/indicators/collect", r.financialHandler.CollectFinancialIndicators)
			financial.POST("/indicators/collect/batch", r.financialHandler.CollectFinancialIndicatorsBatch)
			
			// 财务报表采集
			financial.POST("/reports/collect", r.financialHandler.CollectFinancialReports)
			
			// 财务数据查询
			financial.GET("/indicators", r.financialHandler.GetFinancialIndicators)
			
			// 采集器信息
			financial.GET("/collector/info", r.financialHandler.GetCollectorInfo)
		}

		// 新闻数据相关路由组
		// 设置新闻路由
		r.setupNewsRoutes(v1)

		// 政策数据相关路由组
		// 设置政策路由
		r.setupPolicyRoutes(v1)

		// 系统级路由组
		system := v1.Group("/system")
		{
			// 系统状态
			system.GET("/status", r.systemHandler.Health)
		}
	}
}

// setupNewsRoutes 设置新闻路由
func (r *Router) setupNewsRoutes(v1 *gin.RouterGroup) {
	// 获取数据库管理器
	dbManager := storage.GetGlobalDatabaseManager()
	
	// 创建新闻仓储
	newsRepo := storage.NewNewsRepository(dbManager.GetMongoDatabase())
	
	// 创建新闻服务
	newsService := services.NewNewsService(newsRepo)
	
	// 启动新闻服务
	if err := newsService.Start(); err != nil {
		logger.Errorf("启动新闻服务失败: %v", err)
	} else {
		logger.Info("新闻服务启动成功")
	}
	
	// 设置新闻路由
	routes.SetupNewsRoutes(v1, newsRepo, newsService)
}

// setupPolicyRoutes 设置政策路由
func (r *Router) setupPolicyRoutes(v1 *gin.RouterGroup) {
	// 获取数据库管理器
	dbManager := storage.GetGlobalDatabaseManager()
	
	// 创建政策仓储
	policyRepo := storage.NewPolicyRepository(dbManager.GetMongoDatabase())
	
	// 设置政策路由
	routes.SetupPolicyRoutes(v1, policyRepo)
}

// getTushareTokens 获取Tushare tokens配置
func getTushareTokens() []string {
	// 从配置文件读取tokens
	config := config.GetConfig()
	if config != nil && len(config.Collection.Tushare.Tokens) > 0 {
		return config.Collection.Tushare.Tokens
	}
	
	// 兼容单token配置
	if config != nil && config.Collection.Tushare.Token != "" {
		return []string{config.Collection.Tushare.Token}
	}
	
	// 环境变量兜底（优先从环境变量TUSHARE_TOKENS获取多token配置）
	if tokensEnv := os.Getenv("TUSHARE_TOKENS"); tokensEnv != "" {
		return strings.Split(tokensEnv, ",")
	}
	
	// 兼容单token环境变量
	if token := os.Getenv("TUSHARE_TOKEN"); token != "" {
		return []string{token}
	}
	
	// 默认返回空切片
	return []string{}
}

// createStockHandler 创建股票处理器
func createStockHandler() *handler.StockHandler {
	// 获取数据库管理器
	dbManager := storage.GetGlobalDatabaseManager()
	
	// 创建股票仓储
	stockRepo := storage.NewStockRepository(dbManager.GetMySQL())
	
	// 创建Tushare客户端
	tokens := getTushareTokens()
	var tushareClient *client.TushareClient
	if len(tokens) > 1 {
		// 多token模式
		tushareClient = client.NewTushareClientWithTokenManager(tokens, "https://api.tushare.pro")
	} else if len(tokens) == 1 {
		// 单token模式（向后兼容）
		tushareClient = client.NewTushareClient(tokens[0], "https://api.tushare.pro")
	} else {
		// 无token配置，使用空token（测试环境）
		tushareClient = client.NewTushareClient("", "https://api.tushare.pro")
	}
	
	// 创建股票基础信息采集器
	stockBasicCollector := stock.NewStockBasicCollector(tushareClient, stockRepo)
	
	// 创建股票验证器
	stockValidator := validator.NewStockValidator()
	
	// 创建股票处理器
	return handler.NewStockHandler(stockBasicCollector, stockValidator)
}

// createStockQuoteHandler 创建股票行情处理器
func createStockQuoteHandler() *handler.StockQuoteHandler {
	// 获取数据库管理器
	dbManager := storage.GetGlobalDatabaseManager()
	
	// 创建股票仓储
	stockRepo := storage.NewStockRepository(dbManager.GetMySQL())
	
	// 创建Tushare客户端
	tokens := getTushareTokens()
	var tushareClient *client.TushareClient
	if len(tokens) > 1 {
		// 多token模式
		tushareClient = client.NewTushareClientWithTokenManager(tokens, "https://api.tushare.pro")
	} else if len(tokens) == 1 {
		// 单token模式（向后兼容）
		tushareClient = client.NewTushareClient(tokens[0], "https://api.tushare.pro")
	} else {
		// 无token配置，使用空token（测试环境）
		tushareClient = client.NewTushareClient("", "https://api.tushare.pro")
	}
	
	// 创建股票行情处理器
	return handler.NewStockQuoteHandler(tushareClient, stockRepo)
}

// createAdjFactorHandler 创建复权因子处理器
func createAdjFactorHandler() *handler.AdjFactorHandler {
	// 获取数据库管理器
	dbManager := storage.GetGlobalDatabaseManager()
	
	// 创建股票仓储
	stockRepo := storage.NewStockRepository(dbManager.GetMySQL())
	
	// 创建Tushare客户端
	tokens := getTushareTokens()
	var tushareClient *client.TushareClient
	if len(tokens) > 1 {
		// 多token模式
		tushareClient = client.NewTushareClientWithTokenManager(tokens, "https://api.tushare.pro")
	} else if len(tokens) == 1 {
		// 单token模式（向后兼容）
		tushareClient = client.NewTushareClient(tokens[0], "https://api.tushare.pro")
	} else {
		// 无token配置，使用空token（测试环境）
		tushareClient = client.NewTushareClient("", "https://api.tushare.pro")
	}
	
	// 创建复权因子采集器
	adjFactorCollector := stock.NewAdjFactorCollector(tushareClient, stockRepo)
	
	// 创建复权因子处理器
	return handler.NewAdjFactorHandler(adjFactorCollector, stockRepo)
}

// createFinancialHandler 创建财务数据处理器
func createFinancialHandler() *handler.FinancialHandler {
	// 获取配置
	cfg := config.GetConfig()
	
	// 创建财务数据处理器
	return handler.NewFinancialHandler(cfg)
}

// GetEngine 获取Gin引擎
func (r *Router) GetEngine() *gin.Engine {
	return r.engine
}
