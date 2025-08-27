package handler

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"data-collector/internal/collectors/stock"
	"data-collector/internal/common/validator"
	"data-collector/internal/models"
	"data-collector/pkg/logger"
)

// StockHandler 股票数据处理器
type StockHandler struct {
	stockBasicCollector *stock.StockBasicCollector
	stockValidator      *validator.StockValidator
}

// NewStockHandler 创建股票数据处理器
func NewStockHandler(stockBasicCollector *stock.StockBasicCollector, stockValidator *validator.StockValidator) *StockHandler {
	return &StockHandler{
		stockBasicCollector: stockBasicCollector,
		stockValidator:      stockValidator,
	}
}

// CollectStockBasicRequest 采集股票基础信息请求
type CollectStockBasicRequest struct {
	Mode   string `json:"mode"`   // 采集模式: "all", "incremental", "symbol"
	Symbol string `json:"symbol"` // 股票代码（当mode为symbol时使用）
	Since  string `json:"since"`  // 起始时间（当mode为incremental时使用，格式：2006-01-02）
}

// CollectStockBasicResponse 采集股票基础信息响应
type CollectStockBasicResponse struct {
	Success bool                `json:"success"`
	Message string              `json:"message"`
	Data    *models.StockBasic  `json:"data,omitempty"`
	Count   int                 `json:"count,omitempty"`
}

// APIResponse 通用API响应
type APIResponse struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// CollectStockBasic 采集股票基础信息
// @Summary 采集股票基础信息
// @Description 根据不同模式采集股票基础信息，支持全量采集、增量采集和单个股票采集
// @Tags 股票数据采集
// @Accept json
// @Produce json
// @Param request body CollectStockBasicRequest true "采集请求参数"
// @Success 200 {object} APIResponse "采集成功"
// @Failure 400 {object} APIResponse "请求参数错误"
// @Failure 500 {object} APIResponse "服务器内部错误"
// @Router /collect/stock/basic [post]
func (h *StockHandler) CollectStockBasic(c *gin.Context) {
	ctx := c.Request.Context()
	
	// 解析请求
	var req CollectStockBasicRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Errorf("解析请求失败: %v", err)
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求格式错误",
			Error:   err.Error(),
		})
		return
	}
	
	logger.Infof("收到股票基础信息采集请求: %+v", req)
	
	// 根据模式执行不同的采集逻辑
	switch req.Mode {
	case "all":
		if err := h.stockBasicCollector.CollectAll(ctx); err != nil {
			logger.Errorf("全量采集股票基础信息失败: %v", err)
			c.JSON(http.StatusInternalServerError, APIResponse{
				Success: false,
				Message: "全量采集失败",
				Error:   err.Error(),
			})
			return
		}
		c.JSON(http.StatusOK, APIResponse{
			Success: true,
			Message: "全量采集股票基础信息成功",
		})
		
	case "incremental":
		if req.Since == "" {
			c.JSON(http.StatusBadRequest, APIResponse{
				Success: false,
				Message: "增量采集需要指定起始时间",
				Error:   "since参数不能为空",
			})
			return
		}
		
		sinceTime, err := time.Parse("2006-01-02", req.Since)
		if err != nil {
			logger.Errorf("解析起始时间失败: %v", err)
			c.JSON(http.StatusBadRequest, APIResponse{
				Success: false,
				Message: "起始时间格式错误",
				Error:   "时间格式应为: 2006-01-02",
			})
			return
		}
		
		if err := h.stockBasicCollector.CollectIncremental(ctx, sinceTime); err != nil {
			logger.Errorf("增量采集股票基础信息失败: %v", err)
			c.JSON(http.StatusInternalServerError, APIResponse{
				Success: false,
				Message: "增量采集失败",
				Error:   err.Error(),
			})
			return
		}
		c.JSON(http.StatusOK, APIResponse{
			Success: true,
			Message: "增量采集股票基础信息成功",
		})
		
	case "symbol":
		if req.Symbol == "" {
			c.JSON(http.StatusBadRequest, APIResponse{
				Success: false,
				Message: "按股票代码采集需要指定股票代码",
				Error:   "symbol参数不能为空",
			})
			return
		}
		
		// 验证股票代码格式
		if err := h.stockValidator.ValidateSymbol(req.Symbol); err != nil {
			logger.Errorf("股票代码格式验证失败: %v", err)
			c.JSON(http.StatusBadRequest, APIResponse{
				Success: false,
				Message: "股票代码格式错误",
				Error:   err.Error(),
			})
			return
		}
		
		stock, err := h.stockBasicCollector.CollectBySymbol(ctx, req.Symbol)
		if err != nil {
			logger.Errorf("按股票代码采集基础信息失败: %v", err)
			c.JSON(http.StatusInternalServerError, APIResponse{
				Success: false,
				Message: "采集失败",
				Error:   err.Error(),
			})
			return
		}
		
		c.JSON(http.StatusOK, APIResponse{
			Success: true,
			Message: "采集股票基础信息成功",
			Data:    stock,
		})
		
	default:
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "不支持的采集模式",
			Error:   "支持的模式: all, incremental, symbol",
		})
	}
}

// GetCollectorInfo 获取采集器信息
func (h *StockHandler) GetCollectorInfo(c *gin.Context) {
	info := h.stockBasicCollector.GetCollectorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取采集器信息成功",
		Data:    info,
	})
}

// HealthCheck 健康检查
func (h *StockHandler) HealthCheck(c *gin.Context) {
	health := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"service":   "stock-collector",
		"version":   "1.0.0",
	}
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "服务健康",
		Data:    health,
	})
}

// RegisterRoutes 注册路由
func (h *StockHandler) RegisterRoutes(router *gin.Engine) {
	v1 := router.Group("/api/v1")
	{
		// 股票基础信息采集
		v1.POST("/collect/stock/basic", h.CollectStockBasic)
		
		// 获取采集器信息
		v1.GET("/collector/stock/info", h.GetCollectorInfo)
		
		// 健康检查
		v1.GET("/health", h.HealthCheck)
	}
}