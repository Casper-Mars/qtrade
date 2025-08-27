package financial

import (
	"context"
	"fmt"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// FinancialIndicatorCollector 财务指标采集器
type FinancialIndicatorCollector struct {
	tushareClient *client.TushareClient
	repository   storage.FinancialRepository
}

// NewFinancialIndicatorCollector 创建财务指标采集器
func NewFinancialIndicatorCollector(tushareClient *client.TushareClient, repository storage.FinancialRepository) *FinancialIndicatorCollector {
	return &FinancialIndicatorCollector{
		tushareClient: tushareClient,
		repository:   repository,
	}
}

// CollectFinancialIndicators 采集财务指标数据
func (c *FinancialIndicatorCollector) CollectFinancialIndicators(ctx context.Context, symbol string, year int, quarter int) error {
	logger.Infof("开始采集财务指标数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)

	// 构建请求参数
	params := map[string]interface{}{
		"ts_code": symbol,
		"period": fmt.Sprintf("%d%02d", year, quarter*3), // 转换为YYYYMM格式
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "fina_indicator", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warnf("未获取到财务指标数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
		return nil
	}

	// 解析并保存数据
	for _, item := range resp.Data.Items {
		indicator, err := c.parseFinancialIndicatorData(item, resp.Data.Fields)
		if err != nil {
			logger.Errorf("解析财务指标数据失败: %v", err)
			continue
		}

		// 检查是否已存在
		existing, _ := c.repository.GetFinancialIndicator(indicator.Symbol, indicator.EndDate)
		if existing != nil {
			// 更新现有记录
			indicator.ID = existing.ID
			indicator.CreatedAt = existing.CreatedAt
			if err := c.repository.UpdateFinancialIndicator(indicator); err != nil {
				logger.Errorf("更新财务指标数据失败: %v", err)
			}
		} else {
			// 创建新记录
			if err := c.repository.CreateFinancialIndicator(indicator); err != nil {
				logger.Errorf("保存财务指标数据失败: %v", err)
			}
		}
	}

	logger.Infof("财务指标数据采集完成: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
	return nil
}

// CollectBatch 批量采集财务指标数据
func (c *FinancialIndicatorCollector) CollectBatch(ctx context.Context, symbols []string, year int, quarter int) error {
	logger.Infof("开始批量采集财务指标数据: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)

	for _, symbol := range symbols {
		if err := c.CollectFinancialIndicators(ctx, symbol, year, quarter); err != nil {
			logger.Errorf("采集财务指标失败: symbol=%s, error=%v", symbol, err)
		}

		// 添加延迟避免频率限制
		time.Sleep(100 * time.Millisecond)
	}

	logger.Infof("批量财务指标数据采集完成: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)
	return nil
}

// parseFinancialIndicatorData 解析财务指标数据
func (c *FinancialIndicatorCollector) parseFinancialIndicatorData(item []interface{}, fields []string) (*models.FinancialIndicator, error) {
	indicator := &models.FinancialIndicator{}

	for i, field := range fields {
		if i >= len(item) {
			break
		}

		value := item[i]
		if value == nil {
			continue
		}

		switch field {
		case "ts_code":
			indicator.TSCode = fmt.Sprintf("%v", value)
			indicator.Symbol = indicator.TSCode
		case "ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					indicator.AnnDate = date
				}
			}
		case "end_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					indicator.EndDate = date
				}
			}
		// 盈利能力指标
		case "roe":
			indicator.ROE = fmt.Sprintf("%v", value)
		case "roa":
			indicator.ROA = fmt.Sprintf("%v", value)
		case "roic":
			indicator.ROIC = fmt.Sprintf("%v", value)
		case "gross_margin":
			indicator.GrossMargin = fmt.Sprintf("%v", value)
		case "netprofit_margin":
			indicator.NetMargin = fmt.Sprintf("%v", value)
		case "op_income_of_gr":
			indicator.OperMargin = fmt.Sprintf("%v", value)
		// 成长能力指标
		case "or_yoy":
			indicator.RevenueYoy = fmt.Sprintf("%v", value)
		case "profit_to_gr":
			indicator.NIncomeYoy = fmt.Sprintf("%v", value)
		case "assets_yoy":
			indicator.AssetsYoy = fmt.Sprintf("%v", value)
		// 偿债能力指标
		case "debt_to_assets":
			indicator.DebtToAssets = fmt.Sprintf("%v", value)
		case "current_ratio":
			indicator.CurrentRatio = fmt.Sprintf("%v", value)
		case "quick_ratio":
			indicator.QuickRatio = fmt.Sprintf("%v", value)
		// 运营能力指标
		case "assets_turn":
			indicator.AssetTurnover = fmt.Sprintf("%v", value)
		case "inv_turn":
			indicator.InventoryTurnover = fmt.Sprintf("%v", value)
		case "ar_turn":
			indicator.ArTurnover = fmt.Sprintf("%v", value)
		// 估值指标
		case "pe":
			indicator.PE = fmt.Sprintf("%v", value)
		case "pb":
			indicator.PB = fmt.Sprintf("%v", value)
		case "ps":
			indicator.PS = fmt.Sprintf("%v", value)
		case "pcf":
			indicator.PCF = fmt.Sprintf("%v", value)
		}
	}

	indicator.CreatedAt = time.Now()
	indicator.UpdatedAt = time.Now()
	return indicator, nil
}