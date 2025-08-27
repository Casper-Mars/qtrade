package handler

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"data-collector/internal/collectors/financial"
	"data-collector/internal/config"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"

	"github.com/gin-gonic/gin"
)

// FinancialHandler 财务数据处理器
type FinancialHandler struct {
	financialManager *financial.FinancialManager
}

// NewFinancialHandler 创建财务数据处理器
func NewFinancialHandler(cfg *config.Config) *FinancialHandler {
	// 创建Tushare客户端
	tushareClient := client.NewTushareClient(cfg.Collection.Tushare.Token, cfg.Collection.Tushare.BaseURL)

	// 获取MySQL数据库连接
	mysqlDB := storage.GetMySQL()
	financialRepo := storage.NewFinancialRepository(mysqlDB)

	// 创建财务数据管理器
	financialManager := financial.NewFinancialManager(tushareClient, financialRepo)

	return &FinancialHandler{
		financialManager: financialManager,
	}
}

// CollectFinancialIndicatorsRequest 财务指标采集请求
type CollectFinancialIndicatorsRequest struct {
	Symbol string `json:"symbol" binding:"required" example:"000001.SZ"` // 股票代码
	Period string `json:"period" example:"20231231"`                    // 报告期，格式：YYYYMMDD
}

// CollectFinancialIndicatorsBatchRequest 批量财务指标采集请求
type CollectFinancialIndicatorsBatchRequest struct {
	Symbols []string `json:"symbols" binding:"required" example:"000001.SZ,000002.SZ"` // 股票代码列表
	Period  string   `json:"period" example:"20231231"`                              // 报告期，格式：YYYYMMDD
}

// CollectFinancialReportsRequest 财务报表采集请求
type CollectFinancialReportsRequest struct {
	Symbol     string `json:"symbol" binding:"required" example:"000001.SZ"` // 股票代码
	Period     string `json:"period" example:"20231231"`                    // 报告期，格式：YYYYMMDD
	ReportType string `json:"report_type" example:"1"`                     // 报表类型：1-合并报表，2-单季合并，3-调整单季合并表，4-调整合并报表，5-调整前合并报表，6-母公司报表，7-母公司单季表，8-母公司调整单季表，9-母公司调整表，10-母公司调整前报表，11-调整前合并报表，12-母公司调整前报表
}

// CollectFinancialIndicators 采集财务指标数据
// @Summary 采集财务指标数据
// @Description 根据股票代码和报告期采集财务指标数据
// @Tags 财务数据
// @Accept json
// @Produce json
// @Param request body CollectFinancialIndicatorsRequest true "采集请求"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/financial/indicators/collect [post]
func (h *FinancialHandler) CollectFinancialIndicators(c *gin.Context) {
	symbol := c.Query("symbol")
	period := c.Query("period")

	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "symbol参数不能为空"})
		return
	}

	// 解析period参数（格式：YYYYMMDD）
	var year, quarter int
	var err error
	if period != "" {
		if len(period) != 8 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数格式错误，应为YYYYMMDD格式"})
			return
		}
		year, err = strconv.Atoi(period[:4])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中年份格式错误"})
			return
		}
		month, err := strconv.Atoi(period[4:6])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中月份格式错误"})
			return
		}
		// 根据月份确定季度
		switch {
		case month <= 3:
			quarter = 1
		case month <= 6:
			quarter = 2
		case month <= 9:
			quarter = 3
		default:
			quarter = 4
		}
	} else {
		// 如果没有period参数，尝试使用year和quarter参数
		yearStr := c.Query("year")
		quarterStr := c.Query("quarter")
		if yearStr == "" || quarterStr == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "请提供period参数（YYYYMMDD格式）或year和quarter参数"})
			return
		}
		year, err = strconv.Atoi(yearStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "year参数格式错误"})
			return
		}
		quarter, err = strconv.Atoi(quarterStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "quarter参数格式错误"})
			return
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 采集财务指标数据
	err = h.financialManager.GetIndicatorCollector().CollectFinancialIndicators(ctx, symbol, year, quarter)
	if err != nil {
		logger.Errorf("采集财务指标数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "采集失败",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "财务指标数据采集成功"})
}

// CollectFinancialIndicatorsBatch 批量采集财务指标数据
// @Summary 批量采集财务指标数据
// @Description 批量采集多个股票的财务指标数据
// @Tags 财务数据
// @Accept json
// @Produce json
// @Param request body CollectFinancialIndicatorsBatchRequest true "批量采集请求"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/financial/indicators/collect/batch [post]
func (h *FinancialHandler) CollectFinancialIndicatorsBatch(c *gin.Context) {
	var request struct {
		Symbols []string `json:"symbols" binding:"required"`
		Period  string   `json:"period"`
		Year    int      `json:"year"`
		Quarter int      `json:"quarter"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 解析period参数（格式：YYYYMMDD）
	var year, quarter int
	var err error
	if request.Period != "" {
		if len(request.Period) != 8 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数格式错误，应为YYYYMMDD格式"})
			return
		}
		year, err = strconv.Atoi(request.Period[:4])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中年份格式错误"})
			return
		}
		month, err := strconv.Atoi(request.Period[4:6])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中月份格式错误"})
			return
		}
		// 根据月份确定季度
		switch {
		case month <= 3:
			quarter = 1
		case month <= 6:
			quarter = 2
		case month <= 9:
			quarter = 3
		default:
			quarter = 4
		}
	} else {
		// 如果没有period参数，使用year和quarter参数
		if request.Year == 0 || request.Quarter == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "请提供period参数（YYYYMMDD格式）或year和quarter参数"})
			return
		}
		year = request.Year
		quarter = request.Quarter
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// 批量采集财务指标数据
	err = h.financialManager.CollectFinancialDataBatch(ctx, request.Symbols, year, quarter)
	if err != nil {
		logger.Errorf("批量采集财务指标数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "批量采集失败",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "批量财务指标数据采集成功"})
}

// CollectFinancialReports 采集财务报表数据
// @Summary 采集财务报表数据
// @Description 根据股票代码和报告期采集财务报表数据
// @Tags 财务数据
// @Accept json
// @Produce json
// @Param request body CollectFinancialReportsRequest true "采集请求"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/financial/reports/collect [post]
func (h *FinancialHandler) CollectFinancialReports(c *gin.Context) {
	symbol := c.Query("symbol")
	period := c.Query("period")
	_ = c.Query("report_type") // TODO: 实现报表类型参数

	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "symbol参数不能为空"})
		return
	}

	// 解析period参数（格式：YYYYMMDD）
	var year, quarter int
	var err error
	if period != "" {
		if len(period) != 8 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数格式错误，应为YYYYMMDD格式"})
			return
		}
		year, err = strconv.Atoi(period[:4])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中年份格式错误"})
			return
		}
		month, err := strconv.Atoi(period[4:6])
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "period参数中月份格式错误"})
			return
		}
		// 根据月份确定季度
		switch {
		case month <= 3:
			quarter = 1
		case month <= 6:
			quarter = 2
		case month <= 9:
			quarter = 3
		default:
			quarter = 4
		}
	} else {
		// 如果没有period参数，尝试使用year和quarter参数
		yearStr := c.Query("year")
		quarterStr := c.Query("quarter")
		if yearStr == "" || quarterStr == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "请提供period参数（YYYYMMDD格式）或year和quarter参数"})
			return
		}
		year, err = strconv.Atoi(yearStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "year参数格式错误"})
			return
		}
		quarter, err = strconv.Atoi(quarterStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "quarter参数格式错误"})
			return
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 采集财务报表数据
	err = h.financialManager.CollectFinancialData(ctx, symbol, year, quarter)
	if err != nil {
		logger.Errorf("采集财务报表数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "采集失败",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "财务报表数据采集成功"})
}

// GetFinancialIndicators 获取财务指标数据
// @Summary 获取财务指标数据
// @Description 根据股票代码获取财务指标数据
// @Tags 财务数据
// @Accept json
// @Produce json
// @Param symbol query string true "股票代码" example("000001.SZ")
// @Param limit query int false "限制数量" default(10)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} map[string]interface{} "查询成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/financial/indicators [get]
func (h *FinancialHandler) GetFinancialIndicators(c *gin.Context) {
	symbol := c.Query("symbol")
	limitStr := c.DefaultQuery("limit", "10")
	offsetStr := c.DefaultQuery("offset", "0")
	yearStr := c.Query("year")
	quarterStr := c.Query("quarter")

	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "symbol参数不能为空"})
		return
	}

	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "limit参数格式错误"})
		return
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "offset参数格式错误"})
		return
	}

	// 获取MySQL数据库连接
	mysqlDB := storage.GetMySQL()
	financialRepo := storage.NewFinancialRepository(mysqlDB)

	// 如果指定了年份和季度，查询特定时间的数据
	if yearStr != "" && quarterStr != "" {
		year, err := strconv.Atoi(yearStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "year参数格式错误"})
			return
		}
		quarter, err := strconv.Atoi(quarterStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "quarter参数格式错误"})
			return
		}

		// 构造结束日期（季度末）
		var endDate time.Time
		switch quarter {
		case 1:
			endDate = time.Date(year, 3, 31, 0, 0, 0, 0, time.UTC)
		case 2:
			endDate = time.Date(year, 6, 30, 0, 0, 0, 0, time.UTC)
		case 3:
			endDate = time.Date(year, 9, 30, 0, 0, 0, 0, time.UTC)
		case 4:
			endDate = time.Date(year, 12, 31, 0, 0, 0, 0, time.UTC)
		default:
			c.JSON(http.StatusBadRequest, gin.H{"error": "quarter参数必须为1-4"})
			return
		}

		// 查询特定时间的财务指标
		indicator, err := financialRepo.GetFinancialIndicator(symbol, endDate)
		if err != nil {
			logger.Errorf("查询财务指标失败: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "查询财务指标失败"})
			return
		}

		if indicator == nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "未找到指定时间的财务指标数据"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"data": indicator,
			"message": "查询成功",
		})
		return
	}

	// 查询该股票的所有财务指标（按时间倒序）
	indicators, err := financialRepo.GetFinancialIndicatorsBySymbol(symbol, limit)
	if err != nil {
		logger.Errorf("查询财务指标列表失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "查询财务指标失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data": indicators,
		"total": len(indicators),
		"limit": limit,
		"offset": offset,
		"symbol": symbol,
		"message": "查询成功",
	})
}

// GetCollectorInfo 获取财务采集器信息
// @Summary 获取财务采集器信息
// @Description 获取财务数据采集器的状态和配置信息
// @Tags 财务数据
// @Accept json
// @Produce json
// @Success 200 {object} map[string]interface{} "查询成功"
// @Router /api/v1/financial/collector/info [get]
func (h *FinancialHandler) GetCollectorInfo(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "财务采集器运行正常",
		"status":  "active",
		"type":    "financial",
	})
}