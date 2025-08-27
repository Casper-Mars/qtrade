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

// FinancialReportCollector 财务报表采集器
type FinancialReportCollector struct {
	tushareClient *client.TushareClient
	repository   storage.FinancialRepository
}

// NewFinancialReportCollector 创建财务报表采集器
func NewFinancialReportCollector(tushareClient *client.TushareClient, repository storage.FinancialRepository) *FinancialReportCollector {
	return &FinancialReportCollector{
		tushareClient: tushareClient,
		repository:   repository,
	}
}

// CollectBalanceSheet 采集资产负债表数据
func (c *FinancialReportCollector) CollectBalanceSheet(ctx context.Context, symbol string, year int, quarter int) error {
	logger.Infof("开始采集资产负债表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)

	// 构建请求参数
	params := map[string]interface{}{
		"ts_code": symbol,
		"period": fmt.Sprintf("%d%02d", year, quarter*3), // 转换为YYYYMM格式
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "balancesheet", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warnf("未获取到资产负债表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
		return nil
	}

	// 解析并保存数据
	for _, item := range resp.Data.Items {
		report, err := c.parseBalanceSheetData(item, resp.Data.Fields)
		if err != nil {
			logger.Errorf("解析资产负债表数据失败: %v", err)
			continue
		}

		// 检查是否已存在
		existing, _ := c.repository.GetFinancialReport(report.Symbol, report.EndDate, report.ReportType)
		if existing != nil {
			// 更新现有记录
			report.ID = existing.ID
			report.CreatedAt = existing.CreatedAt
			if err := c.repository.UpdateFinancialReport(report); err != nil {
				logger.Errorf("更新资产负债表数据失败: %v", err)
			}
		} else {
			// 创建新记录
			if err := c.repository.CreateFinancialReport(report); err != nil {
				logger.Errorf("保存资产负债表数据失败: %v", err)
			}
		}
	}

	logger.Infof("资产负债表数据采集完成: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
	return nil
}

// CollectIncomeStatement 采集利润表数据
func (c *FinancialReportCollector) CollectIncomeStatement(ctx context.Context, symbol string, year int, quarter int) error {
	logger.Infof("开始采集利润表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)

	// 构建请求参数
	params := map[string]interface{}{
		"ts_code": symbol,
		"period": fmt.Sprintf("%d%02d", year, quarter*3), // 转换为YYYYMM格式
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "income", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warnf("未获取到利润表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
		return nil
	}

	// 解析并保存数据
	for _, item := range resp.Data.Items {
		report, err := c.parseIncomeStatementData(item, resp.Data.Fields)
		if err != nil {
			logger.Errorf("解析利润表数据失败: %v", err)
			continue
		}

		// 检查是否已存在
		existing, _ := c.repository.GetFinancialReport(report.Symbol, report.EndDate, report.ReportType)
		if existing != nil {
			// 更新现有记录
			report.ID = existing.ID
			report.CreatedAt = existing.CreatedAt
			if err := c.repository.UpdateFinancialReport(report); err != nil {
				logger.Errorf("更新利润表数据失败: %v", err)
			}
		} else {
			// 创建新记录
			if err := c.repository.CreateFinancialReport(report); err != nil {
				logger.Errorf("保存利润表数据失败: %v", err)
			}
		}
	}

	logger.Infof("利润表数据采集完成: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
	return nil
}

// CollectCashFlow 采集现金流量表数据
func (c *FinancialReportCollector) CollectCashFlow(ctx context.Context, symbol string, year int, quarter int) error {
	logger.Infof("开始采集现金流量表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)

	// 构建请求参数
	params := map[string]interface{}{
		"ts_code": symbol,
		"period": fmt.Sprintf("%d%02d", year, quarter*3), // 转换为YYYYMM格式
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "cashflow", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	if resp.Data == nil || len(resp.Data.Items) == 0 {
		logger.Warnf("未获取到现金流量表数据: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
		return nil
	}

	// 解析并保存数据
	for _, item := range resp.Data.Items {
		report, err := c.parseCashFlowData(item, resp.Data.Fields)
		if err != nil {
			logger.Errorf("解析现金流量表数据失败: %v", err)
			continue
		}

		// 检查是否已存在
		existing, _ := c.repository.GetFinancialReport(report.Symbol, report.EndDate, report.ReportType)
		if existing != nil {
			// 更新现有记录
			report.ID = existing.ID
			report.CreatedAt = existing.CreatedAt
			if err := c.repository.UpdateFinancialReport(report); err != nil {
				logger.Errorf("更新现金流量表数据失败: %v", err)
			}
		} else {
			// 创建新记录
			if err := c.repository.CreateFinancialReport(report); err != nil {
				logger.Errorf("保存现金流量表数据失败: %v", err)
			}
		}
	}

	logger.Infof("现金流量表数据采集完成: symbol=%s, year=%d, quarter=%d", symbol, year, quarter)
	return nil
}

// CollectBatch 批量采集财务报表数据
func (c *FinancialReportCollector) CollectBatch(ctx context.Context, symbols []string, year int, quarter int) error {
	logger.Infof("开始批量采集财务报表数据: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)

	for _, symbol := range symbols {
		// 采集资产负债表
		if err := c.CollectBalanceSheet(ctx, symbol, year, quarter); err != nil {
			logger.Errorf("采集资产负债表失败: symbol=%s, error=%v", symbol, err)
		}

		// 采集利润表
		if err := c.CollectIncomeStatement(ctx, symbol, year, quarter); err != nil {
			logger.Errorf("采集利润表失败: symbol=%s, error=%v", symbol, err)
		}

		// 采集现金流量表
		if err := c.CollectCashFlow(ctx, symbol, year, quarter); err != nil {
			logger.Errorf("采集现金流量表失败: symbol=%s, error=%v", symbol, err)
		}

		// 添加延迟避免频率限制
		time.Sleep(100 * time.Millisecond)
	}

	logger.Infof("批量财务报表数据采集完成: symbols=%d, year=%d, quarter=%d", len(symbols), year, quarter)
	return nil
}

// parseBalanceSheetData 解析资产负债表数据
func (c *FinancialReportCollector) parseBalanceSheetData(item []interface{}, fields []string) (*models.FinancialReport, error) {
	report := &models.FinancialReport{}

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
			report.TSCode = fmt.Sprintf("%v", value)
			report.Symbol = report.TSCode
		case "ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.AnnDate = date
				}
			}
		case "f_ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.FDate = date
				}
			}
		case "end_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.EndDate = date
				}
			}
		case "report_type":
			report.ReportType = fmt.Sprintf("%v", value)
		case "total_assets":
			report.TotalAssets = fmt.Sprintf("%v", value)
		case "total_liab":
			report.TotalLiab = fmt.Sprintf("%v", value)
		case "total_hldr_eqy_exc_min_int":
			report.TotalHldrEqyExcMinInt = fmt.Sprintf("%v", value)
		case "total_cur_assets":
			report.TotalCurAssets = fmt.Sprintf("%v", value)
		case "total_cur_liab":
			report.TotalCurLiab = fmt.Sprintf("%v", value)
		case "money_funds":
			report.MoneyFunds = fmt.Sprintf("%v", value)
		}
	}

	report.CreatedAt = time.Now()
	report.UpdatedAt = time.Now()
	return report, nil
}

// parseIncomeStatementData 解析利润表数据
func (c *FinancialReportCollector) parseIncomeStatementData(item []interface{}, fields []string) (*models.FinancialReport, error) {
	report := &models.FinancialReport{}

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
			report.TSCode = fmt.Sprintf("%v", value)
			report.Symbol = report.TSCode
		case "ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.AnnDate = date
				}
			}
		case "f_ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.FDate = date
				}
			}
		case "end_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.EndDate = date
				}
			}
		case "report_type":
			report.ReportType = fmt.Sprintf("%v", value)
		case "revenue":
			report.Revenue = fmt.Sprintf("%v", value)
		case "oper_cost":
			report.OperCost = fmt.Sprintf("%v", value)
		case "n_income":
			report.NIncome = fmt.Sprintf("%v", value)
		case "n_income_attr_p":
			report.NIncomeAttrP = fmt.Sprintf("%v", value)
		case "basic_eps":
			report.BasicEps = fmt.Sprintf("%v", value)
		}
	}

	report.CreatedAt = time.Now()
	report.UpdatedAt = time.Now()
	return report, nil
}

// parseCashFlowData 解析现金流量表数据
func (c *FinancialReportCollector) parseCashFlowData(item []interface{}, fields []string) (*models.FinancialReport, error) {
	report := &models.FinancialReport{}

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
			report.TSCode = fmt.Sprintf("%v", value)
			report.Symbol = report.TSCode
		case "ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.AnnDate = date
				}
			}
		case "f_ann_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.FDate = date
				}
			}
		case "end_date":
			if dateStr := fmt.Sprintf("%v", value); dateStr != "" {
				if date, err := time.Parse("20060102", dateStr); err == nil {
					report.EndDate = date
				}
			}
		case "report_type":
			report.ReportType = fmt.Sprintf("%v", value)
		case "n_cashflow_act":
			report.NCfFrOa = fmt.Sprintf("%v", value)
		case "n_cashflow_inv_act":
			report.NCfFrInvA = fmt.Sprintf("%v", value)
		case "n_cashflow_fin_act":
			report.NCfFrFncA = fmt.Sprintf("%v", value)
		}
	}

	report.CreatedAt = time.Now()
	report.UpdatedAt = time.Now()
	return report, nil
}