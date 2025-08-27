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

// SectorCollector 板块分类采集器
type SectorCollector struct {
	tushareClient *client.TushareClient
	marketRepo    storage.MarketRepository
}

// NewSectorCollector 创建板块分类采集器
func NewSectorCollector(tushareClient *client.TushareClient, marketRepo storage.MarketRepository) *SectorCollector {
	return &SectorCollector{
		tushareClient: tushareClient,
		marketRepo:    marketRepo,
	}
}

// CollectSectorClassification 采集板块分类信息
func (c *SectorCollector) CollectSectorClassification(ctx context.Context) error {
	logger.Info("开始采集板块分类信息")

	// 调用Tushare API获取板块分类信息
	params := map[string]interface{}{
		"src": "SW", // 申万行业分类
	}

	fields := "index_code,industry_name,level,parent_code"

	resp, err := c.tushareClient.Call(ctx, "index_classify", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn("未获取到板块分类信息数据")
		return nil
	}

	// 解析数据
	sectors, err := c.parseSectorClassificationData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析板块分类信息失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateSectors(ctx, sectors)
	if err != nil {
		return fmt.Errorf("存储板块分类信息失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储 %d 条板块分类信息", len(sectors)))
	return nil
}

// CollectSectorConstituents 采集板块成分股信息
func (c *SectorCollector) CollectSectorConstituents(ctx context.Context, sectorCode string) error {
	logger.Info(fmt.Sprintf("开始采集板块 %s 的成分股信息", sectorCode))

	// 调用Tushare API获取板块成分股信息
	params := map[string]interface{}{
		"index_code": sectorCode,
	}

	fields := "index_code,con_code,trade_date,weight"

	resp, err := c.tushareClient.Call(ctx, "index_weight", params, fields)
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warn(fmt.Sprintf("未获取到板块 %s 的成分股信息", sectorCode))
		return nil
	}

	// 解析数据
	constituents, err := c.parseSectorConstituentsData(resp.Data)
	if err != nil {
		return fmt.Errorf("解析板块成分股信息失败: %w", err)
	}

	// 批量存储
	err = c.marketRepo.BatchCreateSectorConstituents(ctx, constituents)
	if err != nil {
		return fmt.Errorf("存储板块成分股信息失败: %w", err)
	}

	logger.Info(fmt.Sprintf("成功采集并存储板块 %s 的 %d 条成分股信息", sectorCode, len(constituents)))
	return nil
}

// CollectAllSectors 全板块批量采集
func (c *SectorCollector) CollectAllSectors(ctx context.Context) error {
	logger.Info("开始全板块批量采集")

	// 首先采集板块分类信息
	err := c.CollectSectorClassification(ctx)
	if err != nil {
		return fmt.Errorf("采集板块分类信息失败: %w", err)
	}

	// 获取所有板块代码
	sectors, err := c.marketRepo.ListSectors(ctx, 1000, 0)
	if err != nil {
		return fmt.Errorf("获取板块列表失败: %w", err)
	}

	// 逐个采集板块成分股信息
	for _, sector := range sectors {
		err := c.CollectSectorConstituents(ctx, sector.SectorCode)
		if err != nil {
			logger.Error(fmt.Sprintf("采集板块 %s 成分股失败: %v", sector.SectorCode, err))
			continue
		}
		// 添加延时避免API限制
		time.Sleep(100 * time.Millisecond)
	}

	logger.Info("全板块批量采集完成")
	return nil
}

// CollectIncremental 增量更新板块数据
func (c *SectorCollector) CollectIncremental(ctx context.Context, since time.Time) error {
	logger.Info(fmt.Sprintf("开始增量更新板块数据，更新时间: %s", since.Format("2006-01-02")))

	// 增量更新板块分类信息
	err := c.CollectSectorClassification(ctx)
	if err != nil {
		return fmt.Errorf("增量更新板块分类信息失败: %w", err)
	}

	// 获取活跃板块列表
	sectors, err := c.marketRepo.ListSectors(ctx, 100, 0)
	if err != nil {
		return fmt.Errorf("获取板块列表失败: %w", err)
	}

	// 更新主要板块的成分股信息
	for _, sector := range sectors {
		if sector.IsActive {
			err := c.CollectSectorConstituents(ctx, sector.SectorCode)
			if err != nil {
				logger.Error(fmt.Sprintf("增量更新板块 %s 成分股失败: %v", sector.SectorCode, err))
				continue
			}
			time.Sleep(100 * time.Millisecond)
		}
	}

	logger.Info("增量更新板块数据完成")
	return nil
}

// parseSectorClassificationData 解析板块分类数据
func (c *SectorCollector) parseSectorClassificationData(data *client.TushareData) ([]*models.Sector, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据为空")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	// 检查必需字段
	requiredFields := []string{"index_code", "industry_name", "level", "parent_code"}
	for _, field := range requiredFields {
		if _, exists := fieldMap[field]; !exists {
			return nil, fmt.Errorf("缺少必需字段: %s", field)
		}
	}

	var sectors []*models.Sector
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		sector := &models.Sector{
			SectorCode: c.getStringValue(item, fieldMap["index_code"]),
			SectorName: c.getStringValue(item, fieldMap["industry_name"]),
			SectorType: "行业", // 申万行业分类
			ParentCode: c.getStringValue(item, fieldMap["parent_code"]),
			Level:      c.getIntValue(item, fieldMap["level"]),
			IsActive:   true,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		sectors = append(sectors, sector)
	}

	return sectors, nil
}

// parseSectorConstituentsData 解析板块成分股数据
func (c *SectorCollector) parseSectorConstituentsData(data *client.TushareData) ([]*models.SectorConstituent, error) {
	if len(data.Fields) == 0 || len(data.Items) == 0 {
		return nil, fmt.Errorf("数据为空")
	}

	// 创建字段索引映射
	fieldMap := make(map[string]int)
	for i, field := range data.Fields {
		fieldMap[field] = i
	}

	// 检查必需字段
	requiredFields := []string{"index_code", "con_code", "trade_date", "weight"}
	for _, field := range requiredFields {
		if _, exists := fieldMap[field]; !exists {
			return nil, fmt.Errorf("缺少必需字段: %s", field)
		}
	}

	var constituents []*models.SectorConstituent
	for _, item := range data.Items {
		if len(item) != len(data.Fields) {
			continue
		}

		tradeDateStr := c.getStringValue(item, fieldMap["trade_date"])
		tradeDate, err := time.Parse("20060102", tradeDateStr)
		if err != nil {
			logger.Warn(fmt.Sprintf("解析交易日期失败: %s", tradeDateStr))
			continue
		}

		constituent := &models.SectorConstituent{
			SectorCode: c.getStringValue(item, fieldMap["index_code"]),
			StockCode:  c.getStringValue(item, fieldMap["con_code"]),
			StockName:  "", // 需要从股票基础信息中获取
			Weight:     c.getStringValue(item, fieldMap["weight"]),
			InDate:     tradeDate,
			OutDate:    nil,
			IsActive:   true,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		constituents = append(constituents, constituent)
	}

	return constituents, nil
}

// getStringValue 获取字符串值
func (c *SectorCollector) getStringValue(item []interface{}, index int) string {
	if index < 0 || index >= len(item) {
		return ""
	}
	if item[index] == nil {
		return ""
	}
	if str, ok := item[index].(string); ok {
		return str
	}
	return fmt.Sprintf("%v", item[index])
}

// getIntValue 获取整数值
func (c *SectorCollector) getIntValue(item []interface{}, index int) int {
	if index < 0 || index >= len(item) {
		return 0
	}
	if item[index] == nil {
		return 0
	}
	if val, ok := item[index].(float64); ok {
		return int(val)
	}
	if str, ok := item[index].(string); ok {
		if str == "1" {
			return 1
		} else if str == "2" {
			return 2
		} else if str == "3" {
			return 3
		}
	}
	return 0
}

// GetCollectorInfo 获取采集器信息
func (c *SectorCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "SectorCollector",
		"description": "板块分类数据采集器",
		"version":     "1.0.0",
		"data_source": "Tushare",
		"features": []string{
			"板块分类信息采集",
			"板块成分股采集",
			"全板块批量采集",
			"增量更新",
		},
	}
}