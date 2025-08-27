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

// IndustryIndexCollector 行业指数采集器
type IndustryIndexCollector struct {
	tushareClient *client.TushareClient
	marketRepo    storage.MarketRepository
}

// NewIndustryIndexCollector 创建行业指数采集器
func NewIndustryIndexCollector(tushareClient *client.TushareClient, marketRepo storage.MarketRepository) *IndustryIndexCollector {
	return &IndustryIndexCollector{
		tushareClient: tushareClient,
		marketRepo:    marketRepo,
	}
}

// CollectIndustryClassification 采集行业分类信息
func (c *IndustryIndexCollector) CollectIndustryClassification(ctx context.Context) error {
	logger.Info("开始采集行业分类信息")

	// 调用Tushare API获取行业分类信息
	params := map[string]interface{}{
		"src": "SW2021", // 申万2021版行业分类
	}

	fields := "index_code,industry_name,level,parent_code"

	resp, err := c.tushareClient.Call(ctx, "index_classify", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn("未获取到行业分类信息数据")
		return nil
	}

	// 解析数据
	industries, err := c.parseIndustryClassificationData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析行业分类信息失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateIndustryIndices(ctx, industries)
	if err != nil {
		return fmt.Errorf("存储行业分类信息失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储 %d 条行业分类信息", len(industries)))
	return nil
}

// CollectIndustryIndex 采集行业指数数据
func (c *IndustryIndexCollector) CollectIndustryIndex(ctx context.Context, industry string, start, end time.Time) error {
	logger.Info(fmt.Sprintf("开始采集行业 %s 的指数数据，时间范围: %s - %s", industry, start.Format("20060102"), end.Format("20060102")))

	// 调用Tushare API获取行业指数数据
	params := map[string]interface{}{
		"ts_code":    industry,
		"start_date": start.Format("20060102"),
		"end_date":   end.Format("20060102"),
	}

	fields := "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg"

	resp, err := c.tushareClient.Call(ctx, "index_daily", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn(fmt.Sprintf("未获取到行业 %s 的指数数据", industry))
		return nil
	}

	// 解析数据
	indices, err := c.parseIndustryIndexData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析行业指数数据失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateIndustryIndices(ctx, indices)
	if err != nil {
		return fmt.Errorf("存储行业指数数据失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储行业 %s 的 %d 条指数数据", industry, len(indices)))
	return nil
}

// CollectAllIndustries 全行业批量采集
func (c *IndustryIndexCollector) CollectAllIndustries(ctx context.Context, start, end time.Time) error {
	logger.Info("开始批量采集所有行业指数数据")

	// 获取所有行业分类
	industries, err := c.marketRepo.ListIndustryIndices(ctx, 1000, 0)
	if err != nil {
		return fmt.Errorf("获取行业分类列表失败: %w", err)
	}

	if len(industries) == 0 {
		logger.Warn("未找到行业分类信息，请先执行行业分类信息采集")
		return nil
	}

	// 提取行业代码
	industryCodes := make([]string, 0)
	for _, industry := range industries {
		if industry.IndustryLevel == "1" { // 只采集一级行业
			industryCodes = append(industryCodes, industry.IndexCode)
		}
	}

	// 批量采集
	for i, industryCode := range industryCodes {
		logger.Info(fmt.Sprintf("采集进度: %d/%d - %s", i+1, len(industryCodes), industryCode))

		err := c.CollectIndustryIndex(ctx, industryCode, start, end)
		if err != nil {
			logger.Error(fmt.Sprintf("采集行业 %s 失败: %v", industryCode, err))
			continue
		}

		// 避免API调用过于频繁
		time.Sleep(100 * time.Millisecond)
	}

	logger.Info("批量采集完成")
	return nil
}

// CollectIncremental 增量更新行业指数数据
func (c *IndustryIndexCollector) CollectIncremental(ctx context.Context, since time.Time) error {
	logger.Info(fmt.Sprintf("开始增量采集行业指数数据，起始时间: %s", since.Format("2006-01-02")))

	// 获取所有行业分类
	industries, err := c.marketRepo.ListIndustryIndices(ctx, 1000, 0)
	if err != nil {
		return fmt.Errorf("获取行业分类列表失败: %w", err)
	}

	if len(industries) == 0 {
		logger.Warn("未找到行业分类信息，请先执行行业分类信息采集")
		return nil
	}

	// 提取行业代码
	industryCodes := make([]string, 0)
	for _, industry := range industries {
		if industry.IndustryLevel == "1" { // 只采集一级行业
			industryCodes = append(industryCodes, industry.IndexCode)
		}
	}

	// 批量采集
	for i, industryCode := range industryCodes {
		logger.Info(fmt.Sprintf("增量采集进度: %d/%d - %s", i+1, len(industryCodes), industryCode))

		err := c.CollectIndustryIndex(ctx, industryCode, since, time.Now())
		if err != nil {
			logger.Error(fmt.Sprintf("增量采集行业 %s 失败: %v", industryCode, err))
			continue
		}

		// 避免API调用过于频繁
		time.Sleep(100 * time.Millisecond)
	}

	logger.Info("增量采集完成")
	return nil
}

// parseIndustryClassificationData 解析行业分类信息数据
func (c *IndustryIndexCollector) parseIndustryClassificationData(data *client.TushareData) ([]*models.IndustryIndex, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据格式错误")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	var industries []*models.IndustryIndex
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		industry := &models.IndustryIndex{}

		// 解析各字段
		if idx, ok := fieldMap["index_code"]; ok && item[idx] != nil {
			industry.IndexCode = item[idx].(string)
		}
		if idx, ok := fieldMap["industry_name"]; ok && item[idx] != nil {
			industry.IndexName = item[idx].(string)
		}
		if idx, ok := fieldMap["level"]; ok && item[idx] != nil {
			industry.IndustryLevel = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["parent_code"]; ok && item[idx] != nil {
			industry.ParentCode = item[idx].(string)
		}

		industries = append(industries, industry)
	}

	return industries, nil
}

// parseIndustryIndexData 解析行业指数数据
func (c *IndustryIndexCollector) parseIndustryIndexData(data *client.TushareData) ([]*models.IndustryIndex, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据格式错误")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	var indices []*models.IndustryIndex
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		index := &models.IndustryIndex{}

		// 解析各字段
		if idx, ok := fieldMap["ts_code"]; ok && item[idx] != nil {
			index.IndexCode = item[idx].(string)
		}
		if idx, ok := fieldMap["trade_date"]; ok && item[idx] != nil {
			if dateStr, ok := item[idx].(string); ok && dateStr != "" {
				if tradeDate, err := time.Parse("20060102", dateStr); err == nil {
					index.TradeDate = tradeDate
				}
			}
		}
		if idx, ok := fieldMap["open"]; ok && item[idx] != nil {
			index.Open = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["high"]; ok && item[idx] != nil {
			index.High = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["low"]; ok && item[idx] != nil {
			index.Low = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["close"]; ok && item[idx] != nil {
			index.Close = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["pre_close"]; ok && item[idx] != nil {
			index.PreClose = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["change"]; ok && item[idx] != nil {
			index.ChangeAmount = fmt.Sprintf("%v", item[idx])
		}
		if idx, ok := fieldMap["pct_chg"]; ok && item[idx] != nil {
			index.PctChg = fmt.Sprintf("%v", item[idx])
		}

		indices = append(indices, index)
	}

	return indices, nil
}

// GetCollectorInfo 获取采集器信息
func (c *IndustryIndexCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "IndustryIndexCollector",
		"description": "行业指数数据采集器",
		"version":     "1.0.0",
		"data_source": "Tushare",
		"supported_apis": []string{
			"index_classify",
			"index_daily",
		},
	}
}