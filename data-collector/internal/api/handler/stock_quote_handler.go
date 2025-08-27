package handler

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"

	"data-collector/internal/collectors/stock"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// StockQuoteHandler 股票行情API处理器
type StockQuoteHandler struct {
	collector *stock.StockQuoteCollector
	stockRepo storage.StockRepository
}

// NewStockQuoteHandler 创建股票行情API处理器
func NewStockQuoteHandler(tushareClient *client.TushareClient, stockRepo storage.StockRepository) *StockQuoteHandler {
	collector := stock.NewStockQuoteCollector(tushareClient, stockRepo)
	return &StockQuoteHandler{
		collector: collector,
		stockRepo: stockRepo,
	}
}

// CollectQuotesByDate 采集指定日期的行情数据
// @Summary 采集指定日期的股票行情数据
// @Description 采集指定日期的股票行情数据，支持指定股票代码列表
// @Tags 股票行情采集
// @Accept json
// @Produce json
// @Param date query string true "交易日期，格式：2006-01-02"
// @Param symbols query string false "股票代码列表，用逗号分隔，如：000001.SZ,000002.SZ"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/quotes [post]
func (h *StockQuoteHandler) CollectQuotesByDate(c *gin.Context) {
	// 解析日期参数
	dateStr := c.Query("date")
	if dateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "缺少日期参数",
			"code":  "MISSING_DATE",
		})
		return
	}

	date, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		logger.Errorf("解析日期失败: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期格式错误，请使用 YYYY-MM-DD 格式",
			"code":  "INVALID_DATE_FORMAT",
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

	logger.Infof("开始采集 %s 的股票行情数据，股票数量: %d", dateStr, len(symbols))

	// 执行采集
	if err := h.collector.CollectByDate(c.Request.Context(), date, symbols); err != nil {
		logger.Errorf("采集股票行情数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集股票行情数据失败",
			"code":  "COLLECTION_FAILED",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "股票行情数据采集成功",
		"date":    dateStr,
		"symbols": len(symbols),
	})
}

// CollectQuotesByDateRange 采集指定时间范围的行情数据
// @Summary 采集指定时间范围的股票行情数据
// @Description 采集指定时间范围的股票行情数据，支持指定股票代码列表
// @Tags 股票行情采集
// @Accept json
// @Produce json
// @Param start_date query string true "开始日期，格式：2006-01-02"
// @Param end_date query string true "结束日期，格式：2006-01-02"
// @Param symbols query string false "股票代码列表，用逗号分隔，如：000001.SZ,000002.SZ"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/quotes/range [post]
func (h *StockQuoteHandler) CollectQuotesByDateRange(c *gin.Context) {
	// 解析开始日期
	startDateStr := c.Query("start_date")
	if startDateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "缺少开始日期参数",
			"code":  "MISSING_START_DATE",
		})
		return
	}

	startDate, err := time.Parse("2006-01-02", startDateStr)
	if err != nil {
		logger.Errorf("解析开始日期失败: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "开始日期格式错误，请使用 YYYY-MM-DD 格式",
			"code":  "INVALID_START_DATE_FORMAT",
		})
		return
	}

	// 解析结束日期
	endDateStr := c.Query("end_date")
	if endDateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "缺少结束日期参数",
			"code":  "MISSING_END_DATE",
		})
		return
	}

	endDate, err := time.Parse("2006-01-02", endDateStr)
	if err != nil {
		logger.Errorf("解析结束日期失败: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "结束日期格式错误，请使用 YYYY-MM-DD 格式",
			"code":  "INVALID_END_DATE_FORMAT",
		})
		return
	}

	// 验证日期范围
	if endDate.Before(startDate) {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "结束日期不能早于开始日期",
			"code":  "INVALID_DATE_RANGE",
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

	logger.Infof("开始采集 %s 到 %s 的股票行情数据，股票数量: %d", startDateStr, endDateStr, len(symbols))

	// 执行采集
	if err := h.collector.CollectByDateRange(c.Request.Context(), startDate, endDate, symbols); err != nil {
		logger.Errorf("采集股票行情数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集股票行情数据失败",
			"code":  "COLLECTION_FAILED",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":    "股票行情数据采集成功",
		"start_date": startDateStr,
		"end_date":   endDateStr,
		"symbols":    len(symbols),
	})
}

// CollectLatestQuotes 采集最新行情数据
// @Summary 采集最新的股票行情数据
// @Description 采集最新交易日的股票行情数据，支持指定股票代码列表
// @Tags 股票行情采集
// @Accept json
// @Produce json
// @Param symbols query string false "股票代码列表，用逗号分隔，如：000001.SZ,000002.SZ"
// @Success 200 {object} map[string]interface{} "采集成功"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /collect/stock/quotes/latest [post]
func (h *StockQuoteHandler) CollectLatestQuotes(c *gin.Context) {
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

	logger.Infof("开始采集最新股票行情数据，股票数量: %d", len(symbols))

	// 执行采集
	if err := h.collector.CollectLatest(c.Request.Context(), symbols); err != nil {
		logger.Errorf("采集最新股票行情数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "采集最新股票行情数据失败",
			"code":  "COLLECTION_FAILED",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "最新股票行情数据采集成功",
		"symbols": len(symbols),
	})
}

// GetQuotesBySymbol 获取指定股票的行情数据
// @Summary 获取指定股票的行情数据
// @Description 获取指定股票在指定时间范围内的行情数据
// @Tags 股票行情
// @Accept json
// @Produce json
// @Param symbol query string true "股票代码，如：000001"
// @Param start_date query string false "开始日期，格式：2006-01-02"
// @Param end_date query string false "结束日期，格式：2006-01-02"
// @Param limit query int false "限制返回数量，默认100"
// @Param offset query int false "偏移量，默认0"
// @Success 200 {object} map[string]interface{} "查询成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/stocks/quotes/by-symbol [get]
func (h *StockQuoteHandler) GetQuotesBySymbol(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "缺少股票代码参数",
			"code":  "MISSING_SYMBOL",
		})
		return
	}

	// 解析时间范围参数
	startDateStr := c.Query("start_date")
	endDateStr := c.Query("end_date")

	var startDate, endDate time.Time
	var err error

	if startDateStr != "" {
		startDate, err = time.Parse("2006-01-02", startDateStr)
		if err != nil {
			logger.Errorf("解析开始日期失败: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "开始日期格式错误，请使用 YYYY-MM-DD 格式",
				"code":  "INVALID_START_DATE_FORMAT",
			})
			return
		}
	} else {
		// 默认开始日期为30天前
		startDate = time.Now().AddDate(0, 0, -30)
	}

	if endDateStr != "" {
		endDate, err = time.Parse("2006-01-02", endDateStr)
		if err != nil {
			logger.Errorf("解析结束日期失败: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "结束日期格式错误，请使用 YYYY-MM-DD 格式",
				"code":  "INVALID_END_DATE_FORMAT",
			})
			return
		}
	} else {
		// 默认结束日期为今天
		endDate = time.Now()
	}

	// 查询数据
	quotes, err := h.stockRepo.GetStockQuotesBySymbol(c.Request.Context(), symbol, startDate, endDate)
	if err != nil {
		logger.Errorf("查询股票行情数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询股票行情数据失败",
			"code":  "QUERY_FAILED",
			"details": err.Error(),
		})
		return
	}

	// 分页处理
	limitStr := c.DefaultQuery("limit", "100")
	offsetStr := c.DefaultQuery("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 100
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}

	// 应用分页
	total := len(quotes)
	start := offset
	end := offset + limit
	if start > total {
		start = total
	}
	if end > total {
		end = total
	}

	pagedQuotes := quotes[start:end]

	c.JSON(http.StatusOK, gin.H{
		"data": gin.H{
			"quotes": pagedQuotes,
			"pagination": gin.H{
				"total":  total,
				"limit":  limit,
				"offset": offset,
				"count":  len(pagedQuotes),
			},
		},
		"symbol":     symbol,
		"start_date": startDate.Format("2006-01-02"),
		"end_date":   endDate.Format("2006-01-02"),
	})
}

// GetQuotesByDate 获取指定日期的行情数据
// @Summary 获取指定日期的行情数据
// @Description 获取指定日期所有股票的行情数据
// @Tags 股票行情
// @Accept json
// @Produce json
// @Param date query string true "交易日期，格式：2006-01-02"
// @Param limit query int false "限制返回数量，默认100"
// @Param offset query int false "偏移量，默认0"
// @Success 200 {object} map[string]interface{} "查询成功"
// @Failure 400 {object} map[string]interface{} "请求参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /api/v1/stocks/quotes/by-date [get]
func (h *StockQuoteHandler) GetQuotesByDate(c *gin.Context) {
	dateStr := c.Query("date")
	if dateStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "缺少日期参数",
			"code":  "MISSING_DATE",
		})
		return
	}

	date, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		logger.Errorf("解析日期失败: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "日期格式错误，请使用 YYYY-MM-DD 格式",
			"code":  "INVALID_DATE_FORMAT",
		})
		return
	}

	// 查询数据
	quotes, err := h.stockRepo.GetStockQuotesByDate(c.Request.Context(), date)
	if err != nil {
		logger.Errorf("查询股票行情数据失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "查询股票行情数据失败",
			"code":  "QUERY_FAILED",
			"details": err.Error(),
		})
		return
	}

	// 分页处理
	limitStr := c.DefaultQuery("limit", "100")
	offsetStr := c.DefaultQuery("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 100
	}

	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}

	// 应用分页
	total := len(quotes)
	start := offset
	end := offset + limit
	if start > total {
		start = total
	}
	if end > total {
		end = total
	}

	pagedQuotes := quotes[start:end]

	c.JSON(http.StatusOK, gin.H{
		"data": gin.H{
			"quotes": pagedQuotes,
			"pagination": gin.H{
				"total":  total,
				"limit":  limit,
				"offset": offset,
				"count":  len(pagedQuotes),
			},
		},
		"date": dateStr,
	})
}

// splitAndTrim 分割字符串并去除空白
func splitAndTrim(s, sep string) []string {
	if s == "" {
		return nil
	}

	parts := make([]string, 0)
	for _, part := range splitString(s, sep) {
		trimmed := trimString(part)
		if trimmed != "" {
			parts = append(parts, trimmed)
		}
	}
	return parts
}

// splitString 简单的字符串分割
func splitString(s, sep string) []string {
	if s == "" {
		return nil
	}

	var result []string
	start := 0
	for i := 0; i < len(s); i++ {
		if i+len(sep) <= len(s) && s[i:i+len(sep)] == sep {
			result = append(result, s[start:i])
			start = i + len(sep)
			i += len(sep) - 1
		}
	}
	result = append(result, s[start:])
	return result
}

// trimString 去除字符串首尾空白
func trimString(s string) string {
	start := 0
	end := len(s)

	// 去除开头空白
	for start < end && isWhitespace(s[start]) {
		start++
	}

	// 去除结尾空白
	for end > start && isWhitespace(s[end-1]) {
		end--
	}

	return s[start:end]
}

// isWhitespace 检查字符是否为空白字符
func isWhitespace(c byte) bool {
	return c == ' ' || c == '\t' || c == '\n' || c == '\r'
}