package handler

import (
	"net/http"
	"time"

	"data-collector/internal/collectors/market"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"

	"github.com/gin-gonic/gin"
)

// IndustryIndexHandler 行业指数API处理器
type IndustryIndexHandler struct {
	industryIndexCollector *market.IndustryIndexCollector
	industryIndexValidator *market.IndustryIndexValidator
	marketRepo             storage.MarketRepository
}

// NewIndustryIndexHandler 创建行业指数API处理器
func NewIndustryIndexHandler(
	industryIndexCollector *market.IndustryIndexCollector,
	industryIndexValidator *market.IndustryIndexValidator,
	marketRepo storage.MarketRepository,
) *IndustryIndexHandler {
	return &IndustryIndexHandler{
		industryIndexCollector: industryIndexCollector,
		industryIndexValidator: industryIndexValidator,
		marketRepo:             marketRepo,
	}
}

// CollectIndustryClassificationRequest 采集行业分类信息请求
type CollectIndustryClassificationRequest struct {
	Mode string `json:"mode"` // 采集模式: "all", "incremental"
}

// CollectIndustryIndexRequest 采集行业指数数据请求
type CollectIndustryIndexRequest struct {
	IndustryCode string `json:"industry_code"` // 行业代码
	StartDate    string `json:"start_date"`    // 开始日期（格式：2006-01-02）
	EndDate      string `json:"end_date"`      // 结束日期（格式：2006-01-02）
}

// IndustryIndexListRequest 行业指数列表查询请求
type IndustryIndexListRequest struct {
	Page          int    `form:"page" binding:"min=1"`                    // 页码，从1开始
	PageSize      int    `form:"page_size" binding:"min=1,max=1000"`     // 每页数量
	IndustryLevel string `form:"industry_level"`                         // 行业级别筛选
	ParentCode    string `form:"parent_code"`                            // 父级代码筛选
	Keyword       string `form:"keyword"`                                // 关键词搜索
}

// IndustryIndexDataRequest 行业指数数据查询请求
type IndustryIndexDataRequest struct {
	IndustryCode string `form:"industry_code" binding:"required"` // 行业代码
	StartDate    string `form:"start_date"`                      // 开始日期（格式：2006-01-02）
	EndDate      string `form:"end_date"`                        // 结束日期（格式：2006-01-02）
	Page         int    `form:"page" binding:"min=1"`            // 页码，从1开始
	PageSize     int    `form:"page_size" binding:"min=1,max=1000"` // 每页数量
	OrderBy      string `form:"order_by"`                        // 排序字段：trade_date
	Order        string `form:"order"`                           // 排序方向：asc, desc
}

// CollectIndustryClassification 采集行业分类信息
func (h *IndustryIndexHandler) CollectIndustryClassification(c *gin.Context) {
	var req CollectIndustryClassificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	logger.Info("开始采集行业分类信息", "mode", req.Mode)

	ctx := c.Request.Context()

	switch req.Mode {
	case "all", "":
		err := h.industryIndexCollector.CollectIndustryClassification(ctx)
		if err != nil {
			logger.Error("采集行业分类信息失败", "error", err)
			c.JSON(http.StatusInternalServerError, APIResponse{
				Success: false,
				Message: "采集行业分类信息失败",
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
		Message: "行业分类信息采集完成",
	})
}

// CollectIndustryIndex 采集行业指数数据
func (h *IndustryIndexHandler) CollectIndustryIndex(c *gin.Context) {
	var req CollectIndustryIndexRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	// 验证参数
	if req.IndustryCode == "" {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "行业代码不能为空",
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

	logger.Info("开始采集行业指数数据", "industry_code", req.IndustryCode, "start_date", req.StartDate, "end_date", req.EndDate)

	ctx := c.Request.Context()
	err = h.industryIndexCollector.CollectIndustryIndex(ctx, req.IndustryCode, startDate, endDate)
	if err != nil {
		logger.Error("采集行业指数数据失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "采集行业指数数据失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "行业指数数据采集完成",
	})
}

// CollectAllIndustries 全行业批量采集
func (h *IndustryIndexHandler) CollectAllIndustries(c *gin.Context) {
	logger.Info("开始全行业批量采集")

	ctx := c.Request.Context()
	// 设置默认时间范围：最近一年
	startDate := time.Now().AddDate(-1, 0, 0)
	endDate := time.Now()
	err := h.industryIndexCollector.CollectAllIndustries(ctx, startDate, endDate)
	if err != nil {
		logger.Error("全行业批量采集失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "全行业批量采集失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "全行业批量采集完成",
	})
}

// CollectIncrementalIndustryIndex 增量更新行业指数数据
func (h *IndustryIndexHandler) CollectIncrementalIndustryIndex(c *gin.Context) {
	logger.Info("开始增量更新行业指数数据")

	ctx := c.Request.Context()
	// 设置增量更新的截止时间为当前时间
	lastUpdateTime := time.Now()
	err := h.industryIndexCollector.CollectIncremental(ctx, lastUpdateTime)
	if err != nil {
		logger.Error("增量更新行业指数数据失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "增量更新行业指数数据失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "增量更新行业指数数据完成",
	})
}

// GetIndustryIndexList 获取行业指数列表
func (h *IndustryIndexHandler) GetIndustryIndexList(c *gin.Context) {
	var req IndustryIndexListRequest
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

	// 查询行业指数列表
	// 注意：这里需要MarketRepository实现相应的查询方法
	// 暂时使用占位符实现
	indices := make([]interface{}, 0)
	
	// 构造响应数据
	responseData := map[string]interface{}{
		"list":           indices,
		"page":           req.Page,
		"page_size":      req.PageSize,
		"total":          len(indices),
		"industry_level": req.IndustryLevel,
		"parent_code":    req.ParentCode,
		"keyword":        req.Keyword,
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "查询成功",
		Data:    responseData,
	})
}

// GetIndustryIndexData 获取行业指数数据
func (h *IndustryIndexHandler) GetIndustryIndexData(c *gin.Context) {
	industry := c.Query("industry")
	if industry == "" {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "行业参数不能为空",
		})
		return
	}

	startDate := c.Query("start_date")
	endDate := c.Query("end_date")
	limit := c.DefaultQuery("limit", "100")

	// 这里应该调用repository获取数据
	// data, err := h.marketRepo.GetIndustryIndexData(industry, startDate, endDate, limit)

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取行业指数数据成功",
		Data: gin.H{
			"industry":   industry,
			"start_date": startDate,
			"end_date":   endDate,
			"limit":      limit,
			"data":       []interface{}{}, // 实际数据
		},
	})
}

// GetCollectorInfo 获取采集器信息
func (h *IndustryIndexHandler) GetCollectorInfo(c *gin.Context) {
	info := h.industryIndexCollector.GetCollectorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取采集器信息成功",
		Data:    info,
	})
}

// GetValidatorInfo 获取验证器信息
func (h *IndustryIndexHandler) GetValidatorInfo(c *gin.Context) {
	info := h.industryIndexValidator.GetValidatorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取验证器信息成功",
		Data:    info,
	})
}

// HealthCheck 健康检查
func (h *IndustryIndexHandler) HealthCheck(c *gin.Context) {
	status := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"service":   "industry-index-handler",
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "服务正常",
		Data:    status,
	})
}

// RegisterRoutes 注册路由
func (h *IndustryIndexHandler) RegisterRoutes(router *gin.RouterGroup) {
	// 行业指数数据采集相关路由
	router.POST("/industry-indices/collect/classification", h.CollectIndustryClassification)
	router.POST("/industry-indices/collect/index", h.CollectIndustryIndex)
	router.POST("/industry-indices/collect/all", h.CollectAllIndustries)
	router.POST("/industry-indices/collect/incremental", h.CollectIncrementalIndustryIndex)

	// 行业指数数据查询相关路由
	router.GET("/industry-indices", h.GetIndustryIndexList)
	router.GET("/industry-indices/data", h.GetIndustryIndexData)

	// 系统信息相关路由
	router.GET("/industry-indices/collector/info", h.GetCollectorInfo)
	router.GET("/industry-indices/validator/info", h.GetValidatorInfo)
	router.GET("/industry-indices/health", h.HealthCheck)
}