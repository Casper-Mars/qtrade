package handler

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"

	"data-collector/internal/collectors/stock"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"
)

// AdjFactorHandler 复权因子数据处理器
type AdjFactorHandler struct {
	collector *stock.AdjFactorCollector
	stockRepo storage.StockRepository
}

// NewAdjFactorHandler 创建复权因子数据处理器
func NewAdjFactorHandler(collector *stock.AdjFactorCollector, stockRepo storage.StockRepository) *AdjFactorHandler {
	return &AdjFactorHandler{
		collector: collector,
		stockRepo: stockRepo,
	}
}

// CollectByDate 按日期采集复权因子数据
// @Summary 按日期采集复权因子数据
// @Description 采集指定日期的复权因子数据
// @Tags 复权因子采集
// @Accept json
// @Produce json
// @Param date query string true "交易日期 (YYYY-MM-DD)"
// @Param symbols query string false "股票代码列表，逗号分隔，为空则采集所有股票"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/adj-factors [post]
func (h *AdjFactorHandler) CollectByDate(c *gin.Context) {
	dateStr := c.Query("date")
	if dateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期参数不能为空",
		})
		return
	}

	date, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期格式错误，请使用 YYYY-MM-DD 格式",
		})
		return
	}

	// 解析股票代码列表
	var symbols []string
	symbolsStr := c.Query("symbols")
	if symbolsStr != "" {
		// 简单的逗号分隔解析
		for _, symbol := range splitAndTrim(symbolsStr, ",") {
			if symbol != "" {
				symbols = append(symbols, symbol)
			}
		}
	}

	ctx := c.Request.Context()
	err = h.collector.CollectByDate(ctx, date, symbols)
	if err != nil {
		logger.Errorf("采集复权因子数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集复权因子数据失败",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "复权因子数据采集成功",
		"date":    dateStr,
		"symbols": len(symbols),
	})
}

// CollectByDateRange 按日期范围采集复权因子数据
// @Summary 按日期范围采集复权因子数据
// @Description 采集指定日期范围的复权因子数据
// @Tags 复权因子采集
// @Accept json
// @Produce json
// @Param start_date query string true "开始日期 (YYYY-MM-DD)"
// @Param end_date query string true "结束日期 (YYYY-MM-DD)"
// @Param symbols query string false "股票代码列表，逗号分隔，为空则采集所有股票"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/adj-factors/range [post]
func (h *AdjFactorHandler) CollectByDateRange(c *gin.Context) {
	startDateStr := c.Query("start_date")
	endDateStr := c.Query("end_date")

	if startDateStr == "" || endDateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "开始日期和结束日期不能为空",
		})
		return
	}

	startDate, err := time.Parse("2006-01-02", startDateStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "开始日期格式错误，请使用 YYYY-MM-DD 格式",
		})
		return
	}

	endDate, err := time.Parse("2006-01-02", endDateStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "结束日期格式错误，请使用 YYYY-MM-DD 格式",
		})
		return
	}

	if endDate.Before(startDate) {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "结束日期不能早于开始日期",
		})
		return
	}

	// 解析股票代码列表
	var symbols []string
	symbolsStr := c.Query("symbols")
	if symbolsStr != "" {
		for _, symbol := range splitAndTrim(symbolsStr, ",") {
			if symbol != "" {
				symbols = append(symbols, symbol)
			}
		}
	}

	ctx := c.Request.Context()
	err = h.collector.CollectByDateRange(ctx, startDate, endDate, symbols)
	if err != nil {
		logger.Errorf("采集复权因子数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集复权因子数据失败",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":    "复权因子数据采集成功",
		"start_date": startDateStr,
		"end_date":   endDateStr,
		"symbols":    len(symbols),
	})
}

// CollectLatest 采集最新复权因子数据
// @Summary 采集最新复权因子数据
// @Description 采集最新交易日的复权因子数据
// @Tags 复权因子采集
// @Accept json
// @Produce json
// @Param symbols query string false "股票代码列表，逗号分隔，为空则采集所有股票"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/adj-factors/latest [post]
func (h *AdjFactorHandler) CollectLatest(c *gin.Context) {
	// 解析股票代码列表
	var symbols []string
	symbolsStr := c.Query("symbols")
	if symbolsStr != "" {
		for _, symbol := range splitAndTrim(symbolsStr, ",") {
			if symbol != "" {
				symbols = append(symbols, symbol)
			}
		}
	}

	ctx := c.Request.Context()
	err := h.collector.CollectLatest(ctx, symbols)
	if err != nil {
		logger.Errorf("采集最新复权因子数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集最新复权因子数据失败",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "最新复权因子数据采集成功",
		"symbols": len(symbols),
	})
}

// GetAdjFactorsBySymbol 查询指定股票的复权因子数据
// @Summary 查询指定股票的复权因子数据
// @Description 查询指定股票在指定时间范围内的复权因子数据
// @Tags 复权因子查询
// @Accept json
// @Produce json
// @Param symbol query string true "股票代码"
// @Param start_date query string false "开始日期 (YYYY-MM-DD)"
// @Param end_date query string false "结束日期 (YYYY-MM-DD)"
// @Success 200 {object} map[string]interface{} "查询成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /stocks/adj-factors/by-symbol [get]
func (h *AdjFactorHandler) GetAdjFactorsBySymbol(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "股票代码不能为空",
		})
		return
	}

	// 解析日期范围
	startDateStr := c.Query("start_date")
	endDateStr := c.Query("end_date")

	var startDate, endDate time.Time
	var err error

	if startDateStr != "" {
		startDate, err = time.Parse("2006-01-02", startDateStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "开始日期格式错误，请使用 YYYY-MM-DD 格式",
			})
			return
		}
	} else {
		// 默认查询最近30天
		startDate = time.Now().AddDate(0, 0, -30)
	}

	if endDateStr != "" {
		endDate, err = time.Parse("2006-01-02", endDateStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "结束日期格式错误，请使用 YYYY-MM-DD 格式",
			})
			return
		}
	} else {
		// 默认到今天
		endDate = time.Now()
	}

	ctx := c.Request.Context()
	adjFactors, err := h.stockRepo.GetAdjFactorsByTSCode(ctx, symbol, startDate, endDate)
	if err != nil {
		logger.Errorf("查询复权因子数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询复权因子数据失败",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"symbol":      symbol,
		"start_date":  startDate.Format("2006-01-02"),
		"end_date":    endDate.Format("2006-01-02"),
		"count":       len(adjFactors),
		"adj_factors": adjFactors,
	})
}

// GetAdjFactorByDate 查询指定日期的复权因子数据
// @Summary 查询指定日期的复权因子数据
// @Description 查询指定日期的所有股票复权因子数据
// @Tags 复权因子查询
// @Accept json
// @Produce json
// @Param date path string true "交易日期 (YYYY-MM-DD)"
// @Param limit query int false "返回数量限制，默认100"
// @Param offset query int false "偏移量，默认0"
// @Success 200 {object} map[string]interface{} "查询成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /stocks/adj-factors/by-date [get]
func (h *AdjFactorHandler) GetAdjFactorByDate(c *gin.Context) {
	dateStr := c.Query("date")
	if dateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期不能为空",
		})
		return
	}

	_, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期格式错误，请使用 YYYY-MM-DD 格式",
		})
		return
	}

	// 解析分页参数
	limit := 100
	offset := 0

	if limitStr := c.Query("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := c.Query("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	// 注意：这里需要实现按日期查询所有复权因子的方法
	// 由于当前StockRepository接口没有这个方法，我们暂时返回空结果
	// 在实际项目中，需要在StockRepository中添加GetAdjFactorsByDate方法

	c.JSON(http.StatusOK, gin.H{
		"date":        dateStr,
		"limit":       limit,
		"offset":      offset,
		"count":       0,
		"adj_factors": []interface{}{},
		"message":     "该功能需要在StockRepository中添加GetAdjFactorsByDate方法",
	})
}