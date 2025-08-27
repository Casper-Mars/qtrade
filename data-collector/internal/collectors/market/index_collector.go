package market

import (
	"context"
	"fmt"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// IndexCollector 大盘指数采集器
type IndexCollector struct {
	tushareClient *client.TushareClient
	marketRepo    storage.MarketRepository
}

// NewIndexCollector 创建大盘指数采集器
func NewIndexCollector(tushareClient *client.TushareClient, marketRepo storage.MarketRepository) *IndexCollector {
	return &IndexCollector{
		tushareClient: tushareClient,
		marketRepo:    marketRepo,
	}
}

// CollectIndexBasic 采集指数基础信息
func (c *IndexCollector) CollectIndexBasic(ctx context.Context) error {
	logger.Info("开始采集指数基础信息")

	// 调用Tushare API获取指数基础信息
	params := map[string]interface{}{
		"market": "SSE,SZSE,CSI", // 上交所、深交所、中证指数
	}

	fields := "ts_code,name,market,publisher,category,base_date,base_point,list_date"

	resp, err := c.tushareClient.Call(ctx, "index_basic", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn("未获取到指数基础信息数据")
		return nil
	}

	// 解析数据
	indices, err := c.parseIndexBasicData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析指数基础信息失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateIndexBasics(ctx, indices)
	if err != nil {
		return fmt.Errorf("存储指数基础信息失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储 %d 条指数基础信息", len(indices)))
	return nil
}

// CollectIndexDaily 采集指数历史行情数据
func (c *IndexCollector) CollectIndexDaily(ctx context.Context, tsCode string, start, end time.Time) error {
	logger.Info(fmt.Sprintf("开始采集指数 %s 的历史行情数据，时间范围: %s - %s", tsCode, start.Format("20060102"), end.Format("20060102")))

	// 调用Tushare API获取指数行情数据
	params := map[string]interface{}{
		"ts_code":    tsCode,
		"start_date": start.Format("20060102"),
		"end_date":   end.Format("20060102"),
	}

	fields := "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"

	resp, err := c.tushareClient.Call(ctx, "index_daily", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn(fmt.Sprintf("未获取到指数 %s 的行情数据", tsCode))
		return nil
	}

	// 解析数据
	quotes, err := c.parseIndexQuoteData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析指数行情数据失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateIndexQuotes(ctx, quotes)
	if err != nil {
		return fmt.Errorf("存储指数行情数据失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储指数 %s 的 %d 条行情数据", tsCode, len(quotes)))
	return nil
}

// CollectBatch 批量采集指数数据
func (c *IndexCollector) CollectBatch(ctx context.Context, tsCodes []string, start, end time.Time) error {
	logger.Info(fmt.Sprintf("开始批量采集 %d 个指数的历史数据", len(tsCodes)))

	for i, tsCode := range tsCodes {
		logger.Info(fmt.Sprintf("采集进度: %d/%d - %s", i+1, len(tsCodes), tsCode))

		err := c.CollectIndexDaily(ctx, tsCode, start, end)
		if err != nil {
			logger.Error(fmt.Sprintf("采集指数 %s 失败: %v", tsCode, err))
			continue
		}

		// 避免API调用过于频繁
		time.Sleep(100 * time.Millisecond)
	}

	logger.Info("批量采集完成")
	return nil
}

// CollectIncremental 增量更新指数数据
func (c *IndexCollector) CollectIncremental(ctx context.Context, since time.Time) error {
	logger.Info(fmt.Sprintf("开始增量采集指数数据，起始时间: %s", since.Format("2006-01-02")))

	// 获取所有指数代码
	indices, err := c.marketRepo.ListIndexBasics(ctx, 1000, 0)
	if err != nil {
		return fmt.Errorf("获取指数列表失败: %w", err)
	}

	if len(indices) == 0 {
		logger.Warn("未找到指数基础信息，请先执行指数基础信息采集")
		return nil
	}

	// 提取指数代码
	tsCodes := make([]string, len(indices))
	for i, index := range indices {
		tsCodes[i] = index.IndexCode
	}

	// 批量采集
	return c.CollectBatch(ctx, tsCodes, since, time.Now())
}

// parseIndexBasicData 解析指数基础信息数据
func (c *IndexCollector) parseIndexBasicData(data *client.TushareData) ([]*models.IndexBasic, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据格式错误")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	var indices []*models.IndexBasic
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		index := &models.IndexBasic{}

		// 解析各字段
		if idx, ok := fieldMap["ts_code"]; ok && item[idx] != nil {
			index.IndexCode = item[idx].(string)
		}
		if idx, ok := fieldMap["name"]; ok && item[idx] != nil {
			index.IndexName = item[idx].(string)
		}
		if idx, ok := fieldMap["market"]; ok && item[idx] != nil {
			index.Market = item[idx].(string)
		}
		if idx, ok := fieldMap["publisher"]; ok && item[idx] != nil {
			index.Publisher = item[idx].(string)
		}
		if idx, ok := fieldMap["category"]; ok && item[idx] != nil {
			index.Category = item[idx].(string)
		}
		if idx, ok := fieldMap["base_date"]; ok && item[idx] != nil {
			if dateStr, ok := item[idx].(string); ok && dateStr != "" {
				if baseDate, err := time.Parse("20060102", dateStr); err == nil {
					index.BaseDate = baseDate
				}
			}
		}
		if idx, ok := fieldMap["base_point"]; ok && item[idx] != nil {
			index.BasePoint = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["list_date"]; ok && item[idx] != nil {
			if dateStr, ok := item[idx].(string); ok && dateStr != "" {
				if listDate, err := time.Parse("20060102", dateStr); err == nil {
					index.ListDate = listDate
				}
			}
		}

		indices = append(indices, index)
	}

	return indices, nil
}

// parseIndexQuoteData 解析指数行情数据
func (c *IndexCollector) parseIndexQuoteData(data *client.TushareData) ([]*models.IndexQuote, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据格式错误")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	var quotes []*models.IndexQuote
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		quote := &models.IndexQuote{}

		// 解析各字段
		if idx, ok := fieldMap["ts_code"]; ok && item[idx] != nil {
			quote.IndexCode = item[idx].(string)
		}
		if idx, ok := fieldMap["trade_date"]; ok && item[idx] != nil {
			if dateStr, ok := item[idx].(string); ok && dateStr != "" {
				if tradeDate, err := time.Parse("20060102", dateStr); err == nil {
					quote.TradeDate = tradeDate
				}
			}
		}
		if idx, ok := fieldMap["open"]; ok && item[idx] != nil {
			quote.Open = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["high"]; ok && item[idx] != nil {
			quote.High = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["low"]; ok && item[idx] != nil {
			quote.Low = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["close"]; ok && item[idx] != nil {
			quote.Close = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["pre_close"]; ok && item[idx] != nil {
			quote.PreClose = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["change"]; ok && item[idx] != nil {
			quote.ChangeAmount = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["pct_chg"]; ok && item[idx] != nil {
			quote.PctChg = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["vol"]; ok && item[idx] != nil {
			quote.Vol = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["amount"]; ok && item[idx] != nil {
			quote.Amount = fmt.Sprintf("%v", item[idx])
		}

		quotes = append(quotes, quote)
	}

	return quotes, nil
}

// GetCollectorInfo 获取采集器信息
func (c *IndexCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "IndexCollector",
		"description": "大盘指数数据采集器",
		"version":     "1.0.0",
		"data_source": "Tushare",
		"supported_apis": []string{
			"index_basic",
			"index_daily",
		},
	}
}