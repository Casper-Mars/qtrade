package financial

import (
	"context"
	"fmt"
	"time"

	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// FinancialManager 财务数据采集管理器
type FinancialManager struct {
	reportCollector    *FinancialReportCollector
	indicatorCollector *FinancialIndicatorCollector
}

// NewFinancialManager 创建财务数据采集管理器
func NewFinancialManager(tushareClient *client.TushareClient, repository storage.FinancialRepository) *FinancialManager {
	return &FinancialManager{
		reportCollector:    NewFinancialReportCollector(tushareClient, repository),
		indicatorCollector: NewFinancialIndicatorCollector(tushareClient, repository),
	}
}

// CollectFinancialData 采集完整的财务数据（报表+指标）
func (m *FinancialManager) CollectFinancialData(ctx context.Context, symbol string, year int, quarter int) error {
	logger.Infof("开始采集完整财务数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)

	// 并行采集财务报表数据
	errChan := make(chan error, 4)

	// 采集资产负债表
	go func() {
		errChan <- m.reportCollector.CollectBalanceSheet(ctx, symbol, year, quarter)
	}()

	// 采集利润表
	go func() {
		errChan <- m.reportCollector.CollectIncomeStatement(ctx, symbol, year, quarter)
	}()

	// 采集现金流量表
	go func() {
		errChan <- m.reportCollector.CollectCashFlow(ctx, symbol, year, quarter)
	}()

	// 采集财务指标
	go func() {
		errChan <- m.indicatorCollector.CollectFinancialIndicators(ctx, symbol, year, quarter)
	}()

	// 等待所有采集任务完成
	var errors []error
	for i := 0; i < 4; i++ {
		if err := <-errChan; err != nil {
			errors = append(errors, err)
		}
	}

	if len(errors) > 0 {
		logger.Errorf("财务数据采集部分失败: symbol=%s, errors=%v", symbol, errors)
		return fmt.Errorf("财务数据采集部分失败: %v", errors)
	}

	logger.Infof("完整财务数据采集完成: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
	return nil
}

// CollectFinancialDataBatch 批量采集财务数据
func (m *FinancialManager) CollectFinancialDataBatch(ctx context.Context, symbols []string, year int, quarter int) error {
	logger.Infof("开始批量采集财务数据: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)

	for _, symbol := range symbols {
		if err := m.CollectFinancialData(ctx, symbol, year, quarter); err != nil {
			logger.Errorf("采集财务数据失败: symbol=%s, error=%v", symbol, err)
		}

		// 添加延迟避免频率限制
		time.Sleep(200 * time.Millisecond)
	}

	logger.Infof("批量财务数据采集完成: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)
	return nil
}

// CollectHistoricalData 采集历史财务数据
func (m *FinancialManager) CollectHistoricalData(ctx context.Context, symbols []string, startYear, endYear int) error {
	logger.Infof("开始采集历史财务数据: symbols=%d, startYear=%d, endYear=%d", len(symbols), startYear, endYear)

	for year := startYear; year <= endYear; year++ {
		for quarter := 1; quarter <= 4; quarter++ {
			logger.Infof("采集历史数据: year=%d, quarter=%d", year, quarter)

			if err := m.CollectFinancialDataBatch(ctx, symbols, year, quarter); err != nil {
				logger.Errorf("采集历史财务数据失败: year=%d, quarter=%d, error=%v", year, quarter, err)
			}

			// 季度间添加更长延迟
			time.Sleep(1 * time.Second)
		}

		// 年度间添加更长延迟
		time.Sleep(2 * time.Second)
	}

	logger.Infof("历史财务数据采集完成: symbols=%d, startYear=%d, endYear=%d", len(symbols), startYear, endYear)
	return nil
}

// CollectLatestData 采集最新财务数据（当前年度和季度）
func (m *FinancialManager) CollectLatestData(ctx context.Context, symbols []string) error {
	now := time.Now()
	year := now.Year()
	quarter := (int(now.Month()) + 2) / 3 // 计算当前季度

	// 如果是年初，可能需要采集上一年的数据
	if now.Month() <= 3 {
		// 采集上一年Q4数据
		if err := m.CollectFinancialDataBatch(ctx, symbols, year-1, 4); err != nil {
			logger.Errorf("采集上年Q4财务数据失败: %v", err)
		}
	}

	// 采集当前季度数据
	return m.CollectFinancialDataBatch(ctx, symbols, year, quarter)
}

// GetReportCollector 获取财务报表采集器
func (m *FinancialManager) GetReportCollector() *FinancialReportCollector {
	return m.reportCollector
}

// GetIndicatorCollector 获取财务指标采集器
func (m *FinancialManager) GetIndicatorCollector() *FinancialIndicatorCollector {
	return m.indicatorCollector
}