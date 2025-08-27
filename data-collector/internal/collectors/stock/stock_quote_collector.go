package stock

import (
	"context"
	"fmt"
	"strconv"
	"sync"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// TushareClientInterface 定义Tushare客户端接口
type TushareClientInterface interface {
	Call(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error)
	CallWithRetry(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error)
}

// StockQuoteCollector 股票行情数据采集器
type StockQuoteCollector struct {
	tushareClient TushareClientInterface
	stockRepo     storage.StockRepository
	rateLimiter   *RateLimiter
}

// RateLimiter 速率限制器
type RateLimiter struct {
	mu           sync.Mutex
	lastCallTime time.Time
	callCount    int
	maxCalls     int           // 每分钟最大调用次数
	windowSize   time.Duration // 时间窗口大小
}

// NewRateLimiter 创建速率限制器
func NewRateLimiter(maxCalls int, windowSize time.Duration) *RateLimiter {
	return &RateLimiter{
		maxCalls:   maxCalls,
		windowSize: windowSize,
	}
}

// Wait 等待直到可以进行下一次调用
func (rl *RateLimiter) Wait() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	
	// 如果超过时间窗口，重置计数器
	if now.Sub(rl.lastCallTime) >= rl.windowSize {
		rl.callCount = 0
		rl.lastCallTime = now
	}

	// 如果达到限制，等待到下一个时间窗口
	if rl.callCount >= rl.maxCalls {
		waitTime := rl.windowSize - now.Sub(rl.lastCallTime)
		if waitTime > 0 {
			time.Sleep(waitTime)
			rl.callCount = 0
			rl.lastCallTime = time.Now()
		}
	}

	rl.callCount++
}

// NewStockQuoteCollector 创建股票行情数据采集器
func NewStockQuoteCollector(tushareClient TushareClientInterface, stockRepo storage.StockRepository) *StockQuoteCollector {
	// 创建速率限制器：每分钟最多45次调用（留5次余量）
	rateLimiter := NewRateLimiter(45, time.Minute)
	
	return &StockQuoteCollector{
		tushareClient: tushareClient,
		stockRepo:     stockRepo,
		rateLimiter:   rateLimiter,
	}
}

// CollectByDate 采集指定日期的行情数据
func (c *StockQuoteCollector) CollectByDate(ctx context.Context, date time.Time, symbols []string) error {
	logger.Infof("开始采集 %s 的股票行情数据，股票数量: %d", date.Format("2006-01-02"), len(symbols))

	// 如果没有指定股票代码，获取所有股票
	if len(symbols) == 0 {
		stocks, err := c.stockRepo.ListStocks(ctx, 10000, 0) // 获取所有股票
		if err != nil {
			return fmt.Errorf("获取股票列表失败: %w", err)
		}
		for _, stock := range stocks {
			symbols = append(symbols, stock.TSCode)
		}
	}

	// 分批处理，每批1000只股票
	batchSize := 1000
	for i := 0; i < len(symbols); i += batchSize {
		end := i + batchSize
		if end > len(symbols) {
			end = len(symbols)
		}
		batch := symbols[i:end]

		if err := c.collectBatchQuotes(ctx, date, batch); err != nil {
			logger.Errorf("批量采集行情数据失败，批次: %d-%d, 错误: %v", i, end, err)
			continue // 继续处理下一批
		}

		// 速率限制器已经控制了API调用频率，这里只需要短暂延迟
		time.Sleep(100 * time.Millisecond)
	}

	logger.Infof("完成 %s 的股票行情数据采集", date.Format("2006-01-02"))
	return nil
}

// CollectByDateRange 采集指定时间范围的行情数据
func (c *StockQuoteCollector) CollectByDateRange(ctx context.Context, start, end time.Time, symbols []string) error {
	logger.Infof("开始采集时间范围 %s 到 %s 的股票行情数据", start.Format("2006-01-02"), end.Format("2006-01-02"))

	// 按日期逐天采集
	current := start
	for current.Before(end) || current.Equal(end) {
		// 跳过周末
		if current.Weekday() == time.Saturday || current.Weekday() == time.Sunday {
			current = current.AddDate(0, 0, 1)
			continue
		}

		if err := c.CollectByDate(ctx, current, symbols); err != nil {
			logger.Errorf("采集 %s 行情数据失败: %v", current.Format("2006-01-02"), err)
		}

		current = current.AddDate(0, 0, 1)
		// 速率限制器已经控制了API调用频率，这里只需要短暂延迟
		time.Sleep(200 * time.Millisecond)
	}

	logger.Infof("完成时间范围 %s 到 %s 的股票行情数据采集", start.Format("2006-01-02"), end.Format("2006-01-02"))
	return nil
}

// CollectLatest 采集最新行情数据
func (c *StockQuoteCollector) CollectLatest(ctx context.Context, symbols []string) error {
	// 获取最新交易日
	latestTradeDate := c.getLatestTradeDate()
	logger.Infof("采集最新交易日 %s 的行情数据", latestTradeDate.Format("2006-01-02"))

	return c.CollectByDate(ctx, latestTradeDate, symbols)
}

// collectBatchQuotes 批量采集行情数据
func (c *StockQuoteCollector) collectBatchQuotes(ctx context.Context, date time.Time, symbols []string) error {
	// 使用速率限制器，确保不超过API调用频率限制
	c.rateLimiter.Wait()
	logger.Debugf("速率限制器通过，准备调用Tushare API")
	
	// 调用Tushare API获取行情数据
	params := map[string]interface{}{
		"trade_date": date.Format("20060102"),
	}

	// 如果指定了股票代码，添加到参数中
	if len(symbols) > 0 && len(symbols) <= 1000 {
		// Tushare API支持批量查询，用逗号分隔
		tsCodeStr := ""
		for i, symbol := range symbols {
			if i > 0 {
				tsCodeStr += ","
			}
			tsCodeStr += symbol
		}
		params["ts_code"] = tsCodeStr
	}

	fields := "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"

	resp, err := c.tushareClient.CallWithRetry(ctx, "daily", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warnf("未获取到 %s 的行情数据", date.Format("2006-01-02"))
		return nil
	}

	// 解析数据
	quotes, err := c.parseStockQuoteData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析股票行情数据失败: %w", err)
	}

	logger.Infof("解析到 %d 条股票行情数据", len(quotes))

	// 数据验证
	validQuotes := c.validateQuotes(quotes)
	logger.Infof("验证通过 %d 条股票行情数据", len(validQuotes))

	// 批量保存到数据库
	if len(validQuotes) > 0 {
		if err := c.stockRepo.BatchCreateStockQuotes(ctx, validQuotes); err != nil {
			return fmt.Errorf("保存股票行情数据失败: %w", err)
		}
	}

	return nil
}

// parseStockQuoteData 解析股票行情数据
func (c *StockQuoteCollector) parseStockQuoteData(data *client.TushareData) ([]*models.StockQuote, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据为空")
	}

	// 创建字段索引映射
	fieldIndex := make(map[string]int)
	for i, field := range data.Fields {
		fieldIndex[field] = i
	}

	// 检查必需字段
	requiredFields := []string{"ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"}
	for _, field := range requiredFields {
		if _, exists := fieldIndex[field]; !exists {
			return nil, fmt.Errorf("缺少必需字段: %s", field)
		}
	}

	var quotes []*models.StockQuote
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			logger.Warnf("数据行字段数量不匹配，跳过: %v", item)
			continue
		}

		quote := &models.StockQuote{}

		// 解析TSCode
		if tsCode, ok := item[fieldIndex["ts_code"]].(string); ok {
			// 从TSCode提取Symbol (去掉后缀)
			if len(tsCode) >= 6 {
				quote.Symbol = tsCode[:6]
			} else {
				quote.Symbol = tsCode
			}
		} else {
			logger.Warnf("无效的ts_code: %v", item[fieldIndex["ts_code"]])
			continue
		}

		// 解析交易日期
		if tradeDateStr, ok := item[fieldIndex["trade_date"]].(string); ok {
			if tradeDate, err := time.Parse("20060102", tradeDateStr); err == nil {
				quote.TradeDate = tradeDate
			} else {
				logger.Warnf("无效的trade_date: %v", tradeDateStr)
				continue
			}
		} else {
			logger.Warnf("无效的trade_date: %v", item[fieldIndex["trade_date"]])
			continue
		}

		// 解析价格数据
		quote.Open = c.parseFloatField(item[fieldIndex["open"]])
		quote.High = c.parseFloatField(item[fieldIndex["high"]])
		quote.Low = c.parseFloatField(item[fieldIndex["low"]])
		quote.Close = c.parseFloatField(item[fieldIndex["close"]])
		quote.PreClose = c.parseFloatField(item[fieldIndex["pre_close"]])
		quote.Change = c.parseFloatField(item[fieldIndex["change"]])
		quote.PctChg = c.parseFloatField(item[fieldIndex["pct_chg"]])
		quote.Vol = c.parseFloatField(item[fieldIndex["vol"]])
		quote.Amount = c.parseFloatField(item[fieldIndex["amount"]])

		quote.CreatedAt = time.Now()
		quote.UpdatedAt = time.Now()

		quotes = append(quotes, quote)
	}

	return quotes, nil
}

// parseFloatField 解析浮点数字段
func (c *StockQuoteCollector) parseFloatField(value interface{}) string {
	if value == nil {
		return "0"
	}

	switch v := value.(type) {
	case float64:
		return strconv.FormatFloat(v, 'f', -1, 64)
	case string:
		if v == "" {
			return "0"
		}
		return v
	default:
		return fmt.Sprintf("%v", v)
	}
}

// validateQuotes 验证行情数据
func (c *StockQuoteCollector) validateQuotes(quotes []*models.StockQuote) []*models.StockQuote {
	var validQuotes []*models.StockQuote

	for _, quote := range quotes {
		if c.isValidQuote(quote) {
			validQuotes = append(validQuotes, quote)
		} else {
			logger.Warnf("无效的行情数据，股票: %s, 日期: %s", quote.Symbol, quote.TradeDate.Format("2006-01-02"))
		}
	}

	return validQuotes
}

// isValidQuote 检查行情数据是否有效
func (c *StockQuoteCollector) isValidQuote(quote *models.StockQuote) bool {
	// 检查股票代码
	if quote.Symbol == "" {
		return false
	}

	// 检查交易日期
	if quote.TradeDate.IsZero() {
		return false
	}

	// 解析价格数据进行逻辑验证
	open, _ := strconv.ParseFloat(quote.Open, 64)
	high, _ := strconv.ParseFloat(quote.High, 64)
	low, _ := strconv.ParseFloat(quote.Low, 64)
	close, _ := strconv.ParseFloat(quote.Close, 64)

	// 价格逻辑验证
	if high < low || high < open || high < close || low > open || low > close {
		return false
	}

	// 价格不能为负数
	if open < 0 || high < 0 || low < 0 || close < 0 {
		return false
	}

	return true
}

// getLatestTradeDate 获取最新交易日
func (c *StockQuoteCollector) getLatestTradeDate() time.Time {
	now := time.Now()
	
	// 如果是周末，回退到周五
	for now.Weekday() == time.Saturday || now.Weekday() == time.Sunday {
		now = now.AddDate(0, 0, -1)
	}
	
	// 如果是交易时间之前（9:30之前），使用前一个交易日
	if now.Hour() < 9 || (now.Hour() == 9 && now.Minute() < 30) {
		now = now.AddDate(0, 0, -1)
		// 再次检查是否是周末
		for now.Weekday() == time.Saturday || now.Weekday() == time.Sunday {
			now = now.AddDate(0, 0, -1)
		}
	}
	
	return time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)
}

// GetCollectorInfo 获取采集器信息
func (c *StockQuoteCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "StockQuoteCollector",
		"description": "股票行情数据采集器",
		"version":     "1.0.0",
		"data_source": "Tushare",
		"api_name":    "daily",
	}
}