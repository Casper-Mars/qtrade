package storage

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"data-collector/internal/models"
)

// FinancialRepository 财务数据存储接口
type FinancialRepository interface {
	// 财务报表相关操作
	CreateFinancialReport(report *models.FinancialReport) error
	GetFinancialReport(symbol string, endDate time.Time, reportType string) (*models.FinancialReport, error)
	GetFinancialReportsBySymbol(symbol string, limit int) ([]*models.FinancialReport, error)
	GetFinancialReportsByDateRange(symbol string, startDate, endDate time.Time) ([]*models.FinancialReport, error)
	UpdateFinancialReport(report *models.FinancialReport) error
	DeleteFinancialReport(id int64) error
	BatchCreateFinancialReports(reports []*models.FinancialReport) error

	// 财务指标相关操作
	CreateFinancialIndicator(indicator *models.FinancialIndicator) error
	GetFinancialIndicator(symbol string, endDate time.Time) (*models.FinancialIndicator, error)
	GetFinancialIndicatorsBySymbol(symbol string, limit int) ([]*models.FinancialIndicator, error)
	GetFinancialIndicatorsByDateRange(symbol string, startDate, endDate time.Time) ([]*models.FinancialIndicator, error)
	UpdateFinancialIndicator(indicator *models.FinancialIndicator) error
	DeleteFinancialIndicator(id int64) error
	BatchCreateFinancialIndicators(indicators []*models.FinancialIndicator) error

	// 查询操作
	GetLatestFinancialReport(symbol string) (*models.FinancialReport, error)
	GetLatestFinancialIndicator(symbol string) (*models.FinancialIndicator, error)
	GetFinancialReportsByReportType(reportType string, limit int) ([]*models.FinancialReport, error)
}

// financialRepository 财务数据存储实现
type financialRepository struct {
	db *sql.DB
}

// NewFinancialRepository 创建财务数据存储实例
func NewFinancialRepository(db *sql.DB) FinancialRepository {
	return &financialRepository{
		db: db,
	}
}

// CreateFinancialReport 创建财务报表记录
func (r *financialRepository) CreateFinancialReport(report *models.FinancialReport) error {
	query := `
		INSERT INTO financial_reports (
			symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	result, err := r.db.Exec(query,
		report.Symbol, report.TSCode, report.AnnDate, report.FDate, report.EndDate, report.ReportType,
		report.TotalAssets, report.TotalLiab, report.TotalHldrEqyExcMinInt, report.TotalCurAssets, report.TotalCurLiab, report.MoneyFunds,
		report.Revenue, report.OperCost, report.NIncome, report.NIncomeAttrP, report.BasicEps,
		report.NCfFrOa, report.NCfFrInvA, report.NCfFrFncA,
	)
	if err != nil {
		return fmt.Errorf("failed to create financial report: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get last insert id: %w", err)
	}

	report.ID = id
	return nil
}

// GetFinancialReport 获取财务报表记录
func (r *financialRepository) GetFinancialReport(symbol string, endDate time.Time, reportType string) (*models.FinancialReport, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a, created_at, updated_at
		FROM financial_reports
		WHERE symbol = ? AND end_date = ? AND report_type = ?
	`

	report := &models.FinancialReport{}
	err := r.db.QueryRow(query, symbol, endDate, reportType).Scan(
		&report.ID, &report.Symbol, &report.TSCode, &report.AnnDate, &report.FDate, &report.EndDate, &report.ReportType,
		&report.TotalAssets, &report.TotalLiab, &report.TotalHldrEqyExcMinInt, &report.TotalCurAssets, &report.TotalCurLiab, &report.MoneyFunds,
		&report.Revenue, &report.OperCost, &report.NIncome, &report.NIncomeAttrP, &report.BasicEps,
		&report.NCfFrOa, &report.NCfFrInvA, &report.NCfFrFncA, &report.CreatedAt, &report.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get financial report: %w", err)
	}

	return report, nil
}

// GetFinancialReportsBySymbol 根据股票代码获取财务报表列表
func (r *financialRepository) GetFinancialReportsBySymbol(symbol string, limit int) ([]*models.FinancialReport, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a, created_at, updated_at
		FROM financial_reports
		WHERE symbol = ?
		ORDER BY end_date DESC
		LIMIT ?
	`

	rows, err := r.db.Query(query, symbol, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query financial reports: %w", err)
	}
	defer rows.Close()

	var reports []*models.FinancialReport
	for rows.Next() {
		report := &models.FinancialReport{}
		err := rows.Scan(
			&report.ID, &report.Symbol, &report.TSCode, &report.AnnDate, &report.FDate, &report.EndDate, &report.ReportType,
			&report.TotalAssets, &report.TotalLiab, &report.TotalHldrEqyExcMinInt, &report.TotalCurAssets, &report.TotalCurLiab, &report.MoneyFunds,
			&report.Revenue, &report.OperCost, &report.NIncome, &report.NIncomeAttrP, &report.BasicEps,
			&report.NCfFrOa, &report.NCfFrInvA, &report.NCfFrFncA, &report.CreatedAt, &report.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan financial report: %w", err)
		}
		reports = append(reports, report)
	}

	return reports, nil
}

// GetFinancialReportsByDateRange 根据日期范围获取财务报表
func (r *financialRepository) GetFinancialReportsByDateRange(symbol string, startDate, endDate time.Time) ([]*models.FinancialReport, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a, created_at, updated_at
		FROM financial_reports
		WHERE symbol = ? AND end_date >= ? AND end_date <= ?
		ORDER BY end_date DESC
	`

	rows, err := r.db.Query(query, symbol, startDate, endDate)
	if err != nil {
		return nil, fmt.Errorf("failed to query financial reports by date range: %w", err)
	}
	defer rows.Close()

	var reports []*models.FinancialReport
	for rows.Next() {
		report := &models.FinancialReport{}
		err := rows.Scan(
			&report.ID, &report.Symbol, &report.TSCode, &report.AnnDate, &report.FDate, &report.EndDate, &report.ReportType,
			&report.TotalAssets, &report.TotalLiab, &report.TotalHldrEqyExcMinInt, &report.TotalCurAssets, &report.TotalCurLiab, &report.MoneyFunds,
			&report.Revenue, &report.OperCost, &report.NIncome, &report.NIncomeAttrP, &report.BasicEps,
			&report.NCfFrOa, &report.NCfFrInvA, &report.NCfFrFncA, &report.CreatedAt, &report.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan financial report: %w", err)
		}
		reports = append(reports, report)
	}

	return reports, nil
}

// UpdateFinancialReport 更新财务报表记录
func (r *financialRepository) UpdateFinancialReport(report *models.FinancialReport) error {
	query := `
		UPDATE financial_reports SET
			ts_code = ?, ann_date = ?, f_date = ?, report_type = ?,
			total_assets = ?, total_liab = ?, total_hldr_eqy_exc_min_int = ?, total_cur_assets = ?, total_cur_liab = ?, money_funds = ?,
			revenue = ?, oper_cost = ?, n_income = ?, n_income_attr_p = ?, basic_eps = ?,
			n_cf_fr_oa = ?, n_cf_fr_inv_a = ?, n_cf_fr_fnc_a = ?, updated_at = CURRENT_TIMESTAMP
		WHERE id = ?
	`

	_, err := r.db.Exec(query,
		report.TSCode, report.AnnDate, report.FDate, report.ReportType,
		report.TotalAssets, report.TotalLiab, report.TotalHldrEqyExcMinInt, report.TotalCurAssets, report.TotalCurLiab, report.MoneyFunds,
		report.Revenue, report.OperCost, report.NIncome, report.NIncomeAttrP, report.BasicEps,
		report.NCfFrOa, report.NCfFrInvA, report.NCfFrFncA, report.ID,
	)
	if err != nil {
		return fmt.Errorf("failed to update financial report: %w", err)
	}

	return nil
}

// DeleteFinancialReport 删除财务报表记录
func (r *financialRepository) DeleteFinancialReport(id int64) error {
	query := `DELETE FROM financial_reports WHERE id = ?`

	_, err := r.db.Exec(query, id)
	if err != nil {
		return fmt.Errorf("failed to delete financial report: %w", err)
	}

	return nil
}

// BatchCreateFinancialReports 批量创建财务报表记录
func (r *financialRepository) BatchCreateFinancialReports(reports []*models.FinancialReport) error {
	if len(reports) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(reports))
	valueArgs := make([]interface{}, 0, len(reports)*20)

	for _, report := range reports {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
		valueArgs = append(valueArgs,
			report.Symbol, report.TSCode, report.AnnDate, report.FDate, report.EndDate, report.ReportType,
			report.TotalAssets, report.TotalLiab, report.TotalHldrEqyExcMinInt, report.TotalCurAssets, report.TotalCurLiab, report.MoneyFunds,
			report.Revenue, report.OperCost, report.NIncome, report.NIncomeAttrP, report.BasicEps,
			report.NCfFrOa, report.NCfFrInvA, report.NCfFrFncA,
		)
	}

	query := fmt.Sprintf(`
		INSERT INTO financial_reports (
			symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a
		) VALUES %s
		ON DUPLICATE KEY UPDATE
			ts_code = VALUES(ts_code),
			ann_date = VALUES(ann_date),
			f_date = VALUES(f_date),
			report_type = VALUES(report_type),
			total_assets = VALUES(total_assets),
			total_liab = VALUES(total_liab),
			total_hldr_eqy_exc_min_int = VALUES(total_hldr_eqy_exc_min_int),
			total_cur_assets = VALUES(total_cur_assets),
			total_cur_liab = VALUES(total_cur_liab),
			money_funds = VALUES(money_funds),
			revenue = VALUES(revenue),
			oper_cost = VALUES(oper_cost),
			n_income = VALUES(n_income),
			n_income_attr_p = VALUES(n_income_attr_p),
			basic_eps = VALUES(basic_eps),
			n_cf_fr_oa = VALUES(n_cf_fr_oa),
			n_cf_fr_inv_a = VALUES(n_cf_fr_inv_a),
			n_cf_fr_fnc_a = VALUES(n_cf_fr_fnc_a),
			updated_at = CURRENT_TIMESTAMP
	`, strings.Join(valueStrings, ","))

	_, err := r.db.Exec(query, valueArgs...)
	if err != nil {
		return fmt.Errorf("failed to batch create financial reports: %w", err)
	}

	return nil
}

// CreateFinancialIndicator 创建财务指标记录
func (r *financialRepository) CreateFinancialIndicator(indicator *models.FinancialIndicator) error {
	query := `
		INSERT INTO financial_indicators (
			symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	result, err := r.db.Exec(query,
		indicator.Symbol, indicator.TSCode, indicator.AnnDate, indicator.EndDate,
		indicator.ROE, indicator.ROA, indicator.ROIC, indicator.GrossMargin, indicator.NetMargin, indicator.OperMargin,
		indicator.RevenueYoy, indicator.NIncomeYoy, indicator.AssetsYoy,
		indicator.DebtToAssets, indicator.CurrentRatio, indicator.QuickRatio,
		indicator.AssetTurnover, indicator.InventoryTurnover, indicator.ArTurnover,
		indicator.PE, indicator.PB, indicator.PS, indicator.PCF,
	)
	if err != nil {
		return fmt.Errorf("failed to create financial indicator: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get last insert id: %w", err)
	}

	indicator.ID = id
	return nil
}

// GetFinancialIndicator 获取财务指标记录
func (r *financialRepository) GetFinancialIndicator(symbol string, endDate time.Time) (*models.FinancialIndicator, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf, created_at, updated_at
		FROM financial_indicators
		WHERE symbol = ? AND end_date = ?
	`

	indicator := &models.FinancialIndicator{}
	err := r.db.QueryRow(query, symbol, endDate).Scan(
		&indicator.ID, &indicator.Symbol, &indicator.TSCode, &indicator.AnnDate, &indicator.EndDate,
		&indicator.ROE, &indicator.ROA, &indicator.ROIC, &indicator.GrossMargin, &indicator.NetMargin, &indicator.OperMargin,
		&indicator.RevenueYoy, &indicator.NIncomeYoy, &indicator.AssetsYoy,
		&indicator.DebtToAssets, &indicator.CurrentRatio, &indicator.QuickRatio,
		&indicator.AssetTurnover, &indicator.InventoryTurnover, &indicator.ArTurnover,
		&indicator.PE, &indicator.PB, &indicator.PS, &indicator.PCF, &indicator.CreatedAt, &indicator.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get financial indicator: %w", err)
	}

	return indicator, nil
}

// GetFinancialIndicatorsBySymbol 根据股票代码获取财务指标列表
func (r *financialRepository) GetFinancialIndicatorsBySymbol(symbol string, limit int) ([]*models.FinancialIndicator, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf, created_at, updated_at
		FROM financial_indicators
		WHERE symbol = ?
		ORDER BY end_date DESC
		LIMIT ?
	`

	rows, err := r.db.Query(query, symbol, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query financial indicators: %w", err)
	}
	defer rows.Close()

	var indicators []*models.FinancialIndicator
	for rows.Next() {
		indicator := &models.FinancialIndicator{}
		err := rows.Scan(
			&indicator.ID, &indicator.Symbol, &indicator.TSCode, &indicator.AnnDate, &indicator.EndDate,
			&indicator.ROE, &indicator.ROA, &indicator.ROIC, &indicator.GrossMargin, &indicator.NetMargin, &indicator.OperMargin,
			&indicator.RevenueYoy, &indicator.NIncomeYoy, &indicator.AssetsYoy,
			&indicator.DebtToAssets, &indicator.CurrentRatio, &indicator.QuickRatio,
			&indicator.AssetTurnover, &indicator.InventoryTurnover, &indicator.ArTurnover,
			&indicator.PE, &indicator.PB, &indicator.PS, &indicator.PCF, &indicator.CreatedAt, &indicator.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan financial indicator: %w", err)
		}
		indicators = append(indicators, indicator)
	}

	return indicators, nil
}

// GetFinancialIndicatorsByDateRange 根据日期范围获取财务指标
func (r *financialRepository) GetFinancialIndicatorsByDateRange(symbol string, startDate, endDate time.Time) ([]*models.FinancialIndicator, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf, created_at, updated_at
		FROM financial_indicators
		WHERE symbol = ? AND end_date >= ? AND end_date <= ?
		ORDER BY end_date DESC
	`

	rows, err := r.db.Query(query, symbol, startDate, endDate)
	if err != nil {
		return nil, fmt.Errorf("failed to query financial indicators by date range: %w", err)
	}
	defer rows.Close()

	var indicators []*models.FinancialIndicator
	for rows.Next() {
		indicator := &models.FinancialIndicator{}
		err := rows.Scan(
			&indicator.ID, &indicator.Symbol, &indicator.TSCode, &indicator.AnnDate, &indicator.EndDate,
			&indicator.ROE, &indicator.ROA, &indicator.ROIC, &indicator.GrossMargin, &indicator.NetMargin, &indicator.OperMargin,
			&indicator.RevenueYoy, &indicator.NIncomeYoy, &indicator.AssetsYoy,
			&indicator.DebtToAssets, &indicator.CurrentRatio, &indicator.QuickRatio,
			&indicator.AssetTurnover, &indicator.InventoryTurnover, &indicator.ArTurnover,
			&indicator.PE, &indicator.PB, &indicator.PS, &indicator.PCF, &indicator.CreatedAt, &indicator.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan financial indicator: %w", err)
		}
		indicators = append(indicators, indicator)
	}

	return indicators, nil
}

// UpdateFinancialIndicator 更新财务指标记录
func (r *financialRepository) UpdateFinancialIndicator(indicator *models.FinancialIndicator) error {
	query := `
		UPDATE financial_indicators SET
			ts_code = ?, ann_date = ?,
			roe = ?, roa = ?, roic = ?, gross_margin = ?, net_margin = ?, oper_margin = ?,
			revenue_yoy = ?, n_income_yoy = ?, assets_yoy = ?,
			debt_to_assets = ?, current_ratio = ?, quick_ratio = ?,
			asset_turnover = ?, inventory_turnover = ?, ar_turnover = ?,
			pe = ?, pb = ?, ps = ?, pcf = ?, updated_at = CURRENT_TIMESTAMP
		WHERE id = ?
	`

	_, err := r.db.Exec(query,
		indicator.TSCode, indicator.AnnDate,
		indicator.ROE, indicator.ROA, indicator.ROIC, indicator.GrossMargin, indicator.NetMargin, indicator.OperMargin,
		indicator.RevenueYoy, indicator.NIncomeYoy, indicator.AssetsYoy,
		indicator.DebtToAssets, indicator.CurrentRatio, indicator.QuickRatio,
		indicator.AssetTurnover, indicator.InventoryTurnover, indicator.ArTurnover,
		indicator.PE, indicator.PB, indicator.PS, indicator.PCF, indicator.ID,
	)
	if err != nil {
		return fmt.Errorf("failed to update financial indicator: %w", err)
	}

	return nil
}

// DeleteFinancialIndicator 删除财务指标记录
func (r *financialRepository) DeleteFinancialIndicator(id int64) error {
	query := `DELETE FROM financial_indicators WHERE id = ?`

	_, err := r.db.Exec(query, id)
	if err != nil {
		return fmt.Errorf("failed to delete financial indicator: %w", err)
	}

	return nil
}

// BatchCreateFinancialIndicators 批量创建财务指标记录
func (r *financialRepository) BatchCreateFinancialIndicators(indicators []*models.FinancialIndicator) error {
	if len(indicators) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(indicators))
	valueArgs := make([]interface{}, 0, len(indicators)*23)

	for _, indicator := range indicators {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
		valueArgs = append(valueArgs,
			indicator.Symbol, indicator.TSCode, indicator.AnnDate, indicator.EndDate,
			indicator.ROE, indicator.ROA, indicator.ROIC, indicator.GrossMargin, indicator.NetMargin, indicator.OperMargin,
			indicator.RevenueYoy, indicator.NIncomeYoy, indicator.AssetsYoy,
			indicator.DebtToAssets, indicator.CurrentRatio, indicator.QuickRatio,
			indicator.AssetTurnover, indicator.InventoryTurnover, indicator.ArTurnover,
			indicator.PE, indicator.PB, indicator.PS, indicator.PCF,
		)
	}

	query := fmt.Sprintf(`
		INSERT INTO financial_indicators (
			symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf
		) VALUES %s
		ON DUPLICATE KEY UPDATE
			ts_code = VALUES(ts_code),
			ann_date = VALUES(ann_date),
			roe = VALUES(roe),
			roa = VALUES(roa),
			roic = VALUES(roic),
			gross_margin = VALUES(gross_margin),
			net_margin = VALUES(net_margin),
			oper_margin = VALUES(oper_margin),
			revenue_yoy = VALUES(revenue_yoy),
			n_income_yoy = VALUES(n_income_yoy),
			assets_yoy = VALUES(assets_yoy),
			debt_to_assets = VALUES(debt_to_assets),
			current_ratio = VALUES(current_ratio),
			quick_ratio = VALUES(quick_ratio),
			asset_turnover = VALUES(asset_turnover),
			inventory_turnover = VALUES(inventory_turnover),
			ar_turnover = VALUES(ar_turnover),
			pe = VALUES(pe),
			pb = VALUES(pb),
			ps = VALUES(ps),
			pcf = VALUES(pcf),
			updated_at = CURRENT_TIMESTAMP
	`, strings.Join(valueStrings, ","))

	_, err := r.db.Exec(query, valueArgs...)
	if err != nil {
		return fmt.Errorf("failed to batch create financial indicators: %w", err)
	}

	return nil
}

// GetLatestFinancialReport 获取最新的财务报表
func (r *financialRepository) GetLatestFinancialReport(symbol string) (*models.FinancialReport, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a, created_at, updated_at
		FROM financial_reports
		WHERE symbol = ?
		ORDER BY end_date DESC
		LIMIT 1
	`

	report := &models.FinancialReport{}
	err := r.db.QueryRow(query, symbol).Scan(
		&report.ID, &report.Symbol, &report.TSCode, &report.AnnDate, &report.FDate, &report.EndDate, &report.ReportType,
		&report.TotalAssets, &report.TotalLiab, &report.TotalHldrEqyExcMinInt, &report.TotalCurAssets, &report.TotalCurLiab, &report.MoneyFunds,
		&report.Revenue, &report.OperCost, &report.NIncome, &report.NIncomeAttrP, &report.BasicEps,
		&report.NCfFrOa, &report.NCfFrInvA, &report.NCfFrFncA, &report.CreatedAt, &report.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get latest financial report: %w", err)
	}

	return report, nil
}

// GetLatestFinancialIndicator 获取最新的财务指标
func (r *financialRepository) GetLatestFinancialIndicator(symbol string) (*models.FinancialIndicator, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, end_date,
			roe, roa, roic, gross_margin, net_margin, oper_margin,
			revenue_yoy, n_income_yoy, assets_yoy,
			debt_to_assets, current_ratio, quick_ratio,
			asset_turnover, inventory_turnover, ar_turnover,
			pe, pb, ps, pcf, created_at, updated_at
		FROM financial_indicators
		WHERE symbol = ?
		ORDER BY end_date DESC
		LIMIT 1
	`

	indicator := &models.FinancialIndicator{}
	err := r.db.QueryRow(query, symbol).Scan(
		&indicator.ID, &indicator.Symbol, &indicator.TSCode, &indicator.AnnDate, &indicator.EndDate,
		&indicator.ROE, &indicator.ROA, &indicator.ROIC, &indicator.GrossMargin, &indicator.NetMargin, &indicator.OperMargin,
		&indicator.RevenueYoy, &indicator.NIncomeYoy, &indicator.AssetsYoy,
		&indicator.DebtToAssets, &indicator.CurrentRatio, &indicator.QuickRatio,
		&indicator.AssetTurnover, &indicator.InventoryTurnover, &indicator.ArTurnover,
		&indicator.PE, &indicator.PB, &indicator.PS, &indicator.PCF, &indicator.CreatedAt, &indicator.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to get latest financial indicator: %w", err)
	}

	return indicator, nil
}

// GetFinancialReportsByReportType 根据报告类型获取财务报表
func (r *financialRepository) GetFinancialReportsByReportType(reportType string, limit int) ([]*models.FinancialReport, error) {
	query := `
		SELECT id, symbol, ts_code, ann_date, f_date, end_date, report_type,
			total_assets, total_liab, total_hldr_eqy_exc_min_int, total_cur_assets, total_cur_liab, money_funds,
			revenue, oper_cost, n_income, n_income_attr_p, basic_eps,
			n_cf_fr_oa, n_cf_fr_inv_a, n_cf_fr_fnc_a, created_at, updated_at
		FROM financial_reports
		WHERE report_type = ?
		ORDER BY end_date DESC
		LIMIT ?
	`

	rows, err := r.db.Query(query, reportType, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query financial reports by report type: %w", err)
	}
	defer rows.Close()

	var reports []*models.FinancialReport
	for rows.Next() {
		report := &models.FinancialReport{}
		err := rows.Scan(
			&report.ID, &report.Symbol, &report.TSCode, &report.AnnDate, &report.FDate, &report.EndDate, &report.ReportType,
			&report.TotalAssets, &report.TotalLiab, &report.TotalHldrEqyExcMinInt, &report.TotalCurAssets, &report.TotalCurLiab, &report.MoneyFunds,
			&report.Revenue, &report.OperCost, &report.NIncome, &report.NIncomeAttrP, &report.BasicEps,
			&report.NCfFrOa, &report.NCfFrInvA, &report.NCfFrFncA, &report.CreatedAt, &report.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan financial report: %w", err)
		}
		reports = append(reports, report)
	}

	return reports, nil
}