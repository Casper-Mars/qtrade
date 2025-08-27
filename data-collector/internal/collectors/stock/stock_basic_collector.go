package stock

import (
	"context"
	"fmt"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// StockBasicCollector 股票基础信息采集器
type StockBasicCollector struct {
	tushareClient *client.TushareClient
	stockRepo     storage.StockRepository
}

// NewStockBasicCollector 创建股票基础信息采集器
func NewStockBasicCollector(tushareClient *client.TushareClient, stockRepo storage.StockRepository) *StockBasicCollector {
	return &StockBasicCollector{
		tushareClient: tushareClient,
		stockRepo:     stockRepo,
	}
}

// CollectAll 采集所有股票基础信息
func (c *StockBasicCollector) CollectAll(ctx context.Context) error {
	logger.Info("开始采集所有股票基础信息")
	
	// 调用Tushare API获取股票基础信息
	params := map[string]interface{}{
		"list_status": "L", // 只获取上市状态的股票
	}
	
	fields := "ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs"
	
	resp, err := c.tushareClient.Call(ctx, "stock_basic", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}
	
	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn("未获取到股票基础信息数据")
		return nil
	}
	
	// 解析数据
	stocks, err := c.parseStockBasicData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析股票基础信息失败: %w", err)
	}
	
	logger.Infof("解析到 %d 条股票基础信息", len(stocks))
	
	// 批量保存到数据库
	if err := c.stockRepo.BatchCreateStocks(ctx, stocks); err != nil {
		return fmt.Errorf("保存股票基础信息失败: %w", err)
	}
	
	logger.Infof("成功采集并保存 %d 条股票基础信息", len(stocks))
	return nil
}

// CollectIncremental 增量采集股票基础信息
func (c *StockBasicCollector) CollectIncremental(ctx context.Context, since time.Time) error {
	logger.Infof("开始增量采集股票基础信息，起始时间: %v", since)
	
	// 获取最近上市的股票
	params := map[string]interface{}{
		"list_status": "L",
		"list_date":   since.Format("20060102"),
	}
	
	fields := "ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs"
	
	resp, err := c.tushareClient.Call(ctx, "stock_basic", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}
	
	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Info("未获取到新的股票基础信息数据")
		return nil
	}
	
	// 解析数据
	stocks, err := c.parseStockBasicData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析股票基础信息失败: %w", err)
	}
	
	logger.Infof("解析到 %d 条新股票基础信息", len(stocks))
	
	// 批量保存到数据库
	if err := c.stockRepo.BatchCreateStocks(ctx, stocks); err != nil {
		return fmt.Errorf("保存股票基础信息失败: %w", err)
	}
	
	logger.Infof("成功增量采集并保存 %d 条股票基础信息", len(stocks))
	return nil
}

// CollectBySymbol 根据股票代码采集基础信息
func (c *StockBasicCollector) CollectBySymbol(ctx context.Context, symbol string) (*models.StockBasic, error) {
	logger.Infof("开始采集股票 %s 的基础信息", symbol)
	
	params := map[string]interface{}{
		"ts_code": symbol,
	}
	
	fields := "ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs"
	
	resp, err := c.tushareClient.Call(ctx, "stock_basic", params, fields)
	if err != nil {
		return nil, fmt.Errorf("调用Tushare API失败: %w", err)
	}
	
	if resp.Data == nil || len(resp.Data.Items) == 0 {
		return nil, fmt.Errorf("未找到股票 %s 的基础信息", symbol)
	}
	
	// 解析数据
	stocks, err := c.parseStockBasicData(resp.Data)
	if err != nil {
		return nil, fmt.Errorf("解析股票基础信息失败: %w", err)
	}
	
	if len(stocks) == 0 {
		return nil, fmt.Errorf("未找到股票 %s 的基础信息", symbol)
	}
	
	stock := stocks[0]
	
	// 保存到数据库
	if err := c.stockRepo.CreateStock(ctx, stock); err != nil {
		return nil, fmt.Errorf("保存股票基础信息失败: %w", err)
	}
	
	logger.Infof("成功采集并保存股票 %s 的基础信息", symbol)
	return stock, nil
}

// parseStockBasicData 解析Tushare返回的股票基础信息数据
func (c *StockBasicCollector) parseStockBasicData(data *client.TushareData) ([]*models.StockBasic, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据为空")
	}
	
	// 创建字段索引映射
	fieldIndex := make(map[string]int)
	for i, field := range data.Fields {
		fieldIndex[field] = i
	}
	
	var stocks []*models.StockBasic
	
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			logger.Warnf("数据行长度不匹配，跳过: %v", item)
			continue
		}
		
		stock := &models.StockBasic{}
		
		// 解析各字段
		if idx, ok := fieldIndex["ts_code"]; ok && item[idx] != nil {
			stock.TSCode = item[idx].(string)
		}
		
		if idx, ok := fieldIndex["symbol"]; ok && item[idx] != nil {
			stock.Symbol = item[idx].(string)
		}
		
		if idx, ok := fieldIndex["name"]; ok && item[idx] != nil {
			stock.Name = item[idx].(string)
		}
		
		if idx, ok := fieldIndex["area"]; ok && item[idx] != nil {
			stock.Area = item[idx].(string)
		}
		
		if idx, ok := fieldIndex["industry"]; ok && item[idx] != nil {
			stock.Industry = item[idx].(string)
		}
		
		if idx, ok := fieldIndex["market"]; ok && item[idx] != nil {
			stock.Market = item[idx].(string)
		}
		
		// 解析上市日期
		if idx, ok := fieldIndex["list_date"]; ok && item[idx] != nil {
			if dateStr, ok := item[idx].(string); ok && dateStr != "" {
				if listDate, err := time.Parse("20060102", dateStr); err == nil {
					stock.ListDate = listDate
				}
			}
		}
		

		
		// 解析是否沪深港通标的
		if idx, ok := fieldIndex["is_hs"]; ok && item[idx] != nil {
			if hsStr, ok := item[idx].(string); ok {
				stock.IsHS = hsStr
			}
		}
		
		// 设置时间戳
		now := time.Now()
		stock.CreatedAt = now
		stock.UpdatedAt = now
		
		// 验证必要字段
		if stock.TSCode == "" || stock.Symbol == "" || stock.Name == "" {
			logger.Warnf("股票基础信息缺少必要字段，跳过: %+v", stock)
			continue
		}
		
		stocks = append(stocks, stock)
	}
	
	return stocks, nil
}

// GetCollectorInfo 获取采集器信息
func (c *StockBasicCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "StockBasicCollector",
		"description": "股票基础信息采集器",
		"version":     "1.0.0",
		"data_source": "Tushare",
		"api_name":    "stock_basic",
	}
}