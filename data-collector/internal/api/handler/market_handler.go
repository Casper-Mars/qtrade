package handler

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"data-collector/internal/collectors/market"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"
)

// MarketHandler 市场数据处理器
type MarketHandler struct {
	indexCollector *market.IndexCollector
	indexValidator *market.IndexValidator
	marketRepo     storage.MarketRepository
}

// NewMarketHandler 创建市场数据处理器
func NewMarketHandler(indexCollector *market.IndexCollector, indexValidator *market.IndexValidator, marketRepo storage.MarketRepository) *MarketHandler {
	return &MarketHandler{
		indexCollector: indexCollector,
		indexValidator: indexValidator,
		marketRepo:     marketRepo,
	}
}

// CollectIndexBasicRequest 采集指数基础信息请求
type CollectIndexBasicRequest struct {
	Mode string `json:"mode"` // 采集模式: "all", "incremental"
}

// CollectIndexDailyRequest 采集指数历史数据请求
type CollectIndexDailyRequest struct {
	IndexCode string `json:"index_code"` // 指数代码
	StartDate string `json:"start_date"` // 开始日期（格式：2006-01-02）
	EndDate   string `json:"end_date"`   // 结束日期（格式：2006-01-02）
}

// IndexListRequest 指数列表查询请求
type IndexListRequest struct {
	Page     int    `form:"page" binding:"min=1"`                    // 页码，从1开始
	PageSize int    `form:"page_size" binding:"min=1,max=1000"`     // 每页数量
	Market   string `form:"market"`                                 // 市场筛选
	Category string `form:"category"`                               // 分类筛选
	Keyword  string `form:"keyword"`                                // 关键词搜索
}

// IndexQuoteListRequest 指数行情查询请求
type IndexQuoteListRequest struct {
	IndexCode string `form:"index_code" binding:"required"` // 指数代码
	StartDate string `form:"start_date"`                   // 开始日期（格式：2006-01-02）
	EndDate   string `form:"end_date"`                     // 结束日期（格式：2006-01-02）
	Page      int    `form:"page" binding:"min=1"`         // 页码，从1开始
	PageSize  int    `form:"page_size" binding:"min=1,max=1000"` // 每页数量
	OrderBy   string `form:"order_by"`                     // 排序字段：trade_date
	Order     string `form:"order"`                        // 排序方向：asc, desc
}

// CollectIndexBasic 采集指数基础信息
func (h *MarketHandler) CollectIndexBasic(c *gin.Context) {
	var req CollectIndexBasicRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	logger.Info("开始采集指数基础信息", "mode", req.Mode)

	ctx := c.Request.Context()

	switch req.Mode {
	case "all", "":
		err := h.indexCollector.CollectIndexBasic(ctx)
		if err != nil {
			logger.Error("采集指数基础信息失败", "error", err)
			c.JSON(http.StatusInternalServerError, APIResponse{
				Success: false,
				Message: "采集指数基础信息失败",
				Error:   err.Error(),
			})
			return
		}
	default:
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "不支持的采集模式",
			Error:   "mode must be 'all'",
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "指数基础信息采集完成",
	})
}

// CollectIndexDaily 采集指数历史数据
func (h *MarketHandler) CollectIndexDaily(c *gin.Context) {
	var req CollectIndexDailyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	// 验证参数
	if req.IndexCode == "" {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "指数代码不能为空",
		})
		return
	}

	// 解析日期
	startDate, err := time.Parse("2006-01-02", req.StartDate)
	if err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "开始日期格式错误",
			Error:   err.Error(),
		})
		return
	}

	endDate, err := time.Parse("2006-01-02", req.EndDate)
	if err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "结束日期格式错误",
			Error:   err.Error(),
		})
		return
	}

	logger.Info("开始采集指数历史数据", "index_code", req.IndexCode, "start_date", req.StartDate, "end_date", req.EndDate)

	ctx := c.Request.Context()
	err = h.indexCollector.CollectIndexDaily(ctx, req.IndexCode, startDate, endDate)
	if err != nil {
		logger.Error("采集指数历史数据失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "采集指数历史数据失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "指数历史数据采集完成",
	})
}

// GetIndexList 获取指数列表
func (h *MarketHandler) GetIndexList(c *gin.Context) {
	var req IndexListRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	// 设置默认值
	if req.Page == 0 {
		req.Page = 1
	}
	if req.PageSize == 0 {
		req.PageSize = 20
	}

	// 计算偏移量
	offset := (req.Page - 1) * req.PageSize

	ctx := c.Request.Context()

	// 查询指数列表
	indices, err := h.marketRepo.ListIndexBasics(ctx, req.PageSize, offset)
	if err != nil {
		logger.Error("查询指数列表失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "查询指数列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 构造响应数据
	responseData := map[string]interface{}{
		"list":      indices,
		"page":      req.Page,
		"page_size": req.PageSize,
		"total":     len(indices),
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "查询成功",
		Data:    responseData,
	})
}

// GetIndexQuotes 获取指数行情数据
func (h *MarketHandler) GetIndexQuotes(c *gin.Context) {
	var req IndexQuoteListRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	// 设置默认值
	if req.Page == 0 {
		req.Page = 1
	}
	if req.PageSize == 0 {
		req.PageSize = 20
	}
	if req.OrderBy == "" {
		req.OrderBy = "trade_date"
	}
	if req.Order == "" {
		req.Order = "desc"
	}

	ctx := c.Request.Context()

	// 查询指数行情数据
	// 如果没有指定日期范围，查询最近的数据
	startDate := time.Now().AddDate(0, -1, 0) // 默认查询最近一个月
	endDate := time.Now()
	if req.StartDate != "" {
		if parsed, err := time.Parse("2006-01-02", req.StartDate); err == nil {
			startDate = parsed
		}
	}
	if req.EndDate != "" {
		if parsed, err := time.Parse("2006-01-02", req.EndDate); err == nil {
			endDate = parsed
		}
	}

	quotes, err := h.marketRepo.GetIndexQuotesByCode(ctx, req.IndexCode, startDate, endDate)
	if err != nil {
		logger.Error("查询指数行情数据失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "查询指数行情数据失败",
			Error:   err.Error(),
		})
		return
	}

	// 构造响应数据
	responseData := map[string]interface{}{
		"list":       quotes,
		"index_code": req.IndexCode,
		"page":       req.Page,
		"page_size":  req.PageSize,
		"total":      len(quotes),
		"order_by":   req.OrderBy,
		"order":      req.Order,
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "查询成功",
		Data:    responseData,
	})
}

// GetCollectorInfo 获取采集器信息
func (h *MarketHandler) GetCollectorInfo(c *gin.Context) {
	info := h.indexCollector.GetCollectorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取采集器信息成功",
		Data:    info,
	})
}

// GetValidatorInfo 获取验证器信息
func (h *MarketHandler) GetValidatorInfo(c *gin.Context) {
	info := h.indexValidator.GetValidatorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取验证器信息成功",
		Data:    info,
	})
}

// HealthCheck 健康检查
func (h *MarketHandler) HealthCheck(c *gin.Context) {
	status := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"service":   "market-handler",
		"version":   "1.0.0",
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "服务正常",
		Data:    status,
	})
}

// RegisterRoutes 注册路由
func (h *MarketHandler) RegisterRoutes(router *gin.Engine) {
	api := router.Group("/api/v1/market")
	{
		// 数据采集接口
		api.POST("/collect/index/basic", h.CollectIndexBasic)
		api.POST("/collect/index/daily", h.CollectIndexDaily)

		// 数据查询接口
		api.GET("/index/list", h.GetIndexList)
		api.GET("/index/quotes", h.GetIndexQuotes)

		// 系统信息接口
		api.GET("/collector/info", h.GetCollectorInfo)
		api.GET("/validator/info", h.GetValidatorInfo)
		api.GET("/health", h.HealthCheck)
	}
}