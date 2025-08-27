package storage

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"data-collector/internal/models"
)

// MarketRepository 市场数据仓库接口
type MarketRepository interface {
	// 大盘指数基础信息相关操作
	CreateIndexBasic(ctx context.Context, index *models.IndexBasic) error
	GetIndexBasicByCode(ctx context.Context, indexCode string) (*models.IndexBasic, error)
	GetIndexBasicByName(ctx context.Context, indexName string) (*models.IndexBasic, error)
	UpdateIndexBasic(ctx context.Context, index *models.IndexBasic) error
	DeleteIndexBasic(ctx context.Context, indexCode string) error
	ListIndexBasics(ctx context.Context, limit, offset int) ([]*models.IndexBasic, error)
	BatchCreateIndexBasics(ctx context.Context, indices []*models.IndexBasic) error

	// 指数行情数据相关操作
	CreateIndexQuote(ctx context.Context, quote *models.IndexQuote) error
	GetIndexQuote(ctx context.Context, indexCode string, tradeDate time.Time) (*models.IndexQuote, error)
	GetIndexQuotesByCode(ctx context.Context, indexCode string, startDate, endDate time.Time) ([]*models.IndexQuote, error)
	GetIndexQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.IndexQuote, error)
	UpdateIndexQuote(ctx context.Context, quote *models.IndexQuote) error
	DeleteIndexQuote(ctx context.Context, indexCode string, tradeDate time.Time) error
	BatchCreateIndexQuotes(ctx context.Context, quotes []*models.IndexQuote) error

	// 行业指数相关操作
	CreateIndustryIndex(ctx context.Context, industry *models.IndustryIndex) error
	GetIndustryIndexByCode(ctx context.Context, industryCode string) (*models.IndustryIndex, error)
	UpdateIndustryIndex(ctx context.Context, industry *models.IndustryIndex) error
	DeleteIndustryIndex(ctx context.Context, industryCode string) error
	ListIndustryIndices(ctx context.Context, limit, offset int) ([]*models.IndustryIndex, error)
	BatchCreateIndustryIndices(ctx context.Context, industries []*models.IndustryIndex) error

	// 板块分类相关操作
	CreateSector(ctx context.Context, sector *models.Sector) error
	GetSectorByCode(ctx context.Context, sectorCode string) (*models.Sector, error)
	UpdateSector(ctx context.Context, sector *models.Sector) error
	DeleteSector(ctx context.Context, sectorCode string) error
	ListSectors(ctx context.Context, limit, offset int) ([]*models.Sector, error)
	BatchCreateSectors(ctx context.Context, sectors []*models.Sector) error

	// 板块成分股相关操作
	CreateSectorConstituent(ctx context.Context, constituent *models.SectorConstituent) error
	GetSectorConstituents(ctx context.Context, sectorCode string) ([]*models.SectorConstituent, error)
	GetStockSectors(ctx context.Context, stockCode string) ([]*models.SectorConstituent, error)
	UpdateSectorConstituent(ctx context.Context, constituent *models.SectorConstituent) error
	DeleteSectorConstituent(ctx context.Context, sectorCode, stockCode string) error
	BatchCreateSectorConstituents(ctx context.Context, constituents []*models.SectorConstituent) error
}

// marketRepository 市场数据仓库实现
type marketRepository struct {
	db *sql.DB
}

// NewMarketRepository 创建市场数据仓库
func NewMarketRepository(db *sql.DB) MarketRepository {
	return &marketRepository{
		db: db,
	}
}

// CreateIndexBasic 创建大盘指数基础信息
func (r *marketRepository) CreateIndexBasic(ctx context.Context, index *models.IndexBasic) error {
	query := `
		INSERT INTO market_indexes (index_code, index_name, market, publisher, category, base_date, base_point, list_date, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		index.IndexCode, index.IndexName, index.Market, index.Publisher,
		index.Category, index.BaseDate, index.BasePoint, index.ListDate)
	return err
}

// GetIndexBasicByCode 根据指数代码获取指数信息
func (r *marketRepository) GetIndexBasicByCode(ctx context.Context, indexCode string) (*models.IndexBasic, error) {
	query := `
		SELECT id, index_code, index_name, market, publisher, category, base_date, base_point, list_date, created_at, updated_at
		FROM market_indexes WHERE index_code = ?
	`
	index := &models.IndexBasic{}
	err := r.db.QueryRowContext(ctx, query, indexCode).Scan(
		&index.ID, &index.IndexCode, &index.IndexName, &index.Market, &index.Publisher,
		&index.Category, &index.BaseDate, &index.BasePoint, &index.ListDate,
		&index.CreatedAt, &index.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return index, nil
}

// GetIndexBasicByName 根据指数名称获取指数信息
func (r *marketRepository) GetIndexBasicByName(ctx context.Context, indexName string) (*models.IndexBasic, error) {
	query := `
		SELECT id, index_code, index_name, market, publisher, category, base_date, base_point, list_date, created_at, updated_at
		FROM market_indexes WHERE index_name = ?
	`
	index := &models.IndexBasic{}
	err := r.db.QueryRowContext(ctx, query, indexName).Scan(
		&index.ID, &index.IndexCode, &index.IndexName, &index.Market, &index.Publisher,
		&index.Category, &index.BaseDate, &index.BasePoint, &index.ListDate,
		&index.CreatedAt, &index.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return index, nil
}

// UpdateIndexBasic 更新指数信息
func (r *marketRepository) UpdateIndexBasic(ctx context.Context, index *models.IndexBasic) error {
	query := `
		UPDATE market_indexes SET index_name = ?, market = ?, publisher = ?, category = ?, base_date = ?, base_point = ?, list_date = ?, updated_at = NOW()
		WHERE index_code = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		index.IndexName, index.Market, index.Publisher, index.Category,
		index.BaseDate, index.BasePoint, index.ListDate, index.IndexCode)
	return err
}

// DeleteIndexBasic 删除指数信息
func (r *marketRepository) DeleteIndexBasic(ctx context.Context, indexCode string) error {
	query := `DELETE FROM market_indexes WHERE index_code = ?`
	_, err := r.db.ExecContext(ctx, query, indexCode)
	return err
}

// ListIndexBasics 获取指数列表
func (r *marketRepository) ListIndexBasics(ctx context.Context, limit, offset int) ([]*models.IndexBasic, error) {
	query := `
		SELECT id, index_code, index_name, market, publisher, category, base_date, base_point, list_date, created_at, updated_at
		FROM market_indexes ORDER BY id LIMIT ? OFFSET ?
	`
	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var indices []*models.IndexBasic
	for rows.Next() {
		index := &models.IndexBasic{}
		err := rows.Scan(
			&index.ID, &index.IndexCode, &index.IndexName, &index.Market, &index.Publisher,
			&index.Category, &index.BaseDate, &index.BasePoint, &index.ListDate,
			&index.CreatedAt, &index.UpdatedAt)
		if err != nil {
			return nil, err
		}
		indices = append(indices, index)
	}
	return indices, nil
}

// BatchCreateIndexBasics 批量创建指数基础信息
func (r *marketRepository) BatchCreateIndexBasics(ctx context.Context, indices []*models.IndexBasic) error {
	if len(indices) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(indices))
	valueArgs := make([]interface{}, 0, len(indices)*8)

	for _, index := range indices {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			index.IndexCode, index.IndexName, index.Market, index.Publisher,
			index.Category, index.BaseDate, index.BasePoint, index.ListDate)
	}

	query := fmt.Sprintf(`
		INSERT INTO market_indexes (index_code, index_name, market, publisher, category, base_date, base_point, list_date, created_at, updated_at)
		VALUES %s
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateIndexQuote 创建指数行情数据
func (r *marketRepository) CreateIndexQuote(ctx context.Context, quote *models.IndexQuote) error {
	query := `
		INSERT INTO index_quotes (index_code, trade_date, close, open, high, low, pre_close, change_amount, pct_chg, vol, amount, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		quote.IndexCode, quote.TradeDate, quote.Close, quote.Open, quote.High, quote.Low,
		quote.PreClose, quote.ChangeAmount, quote.PctChg, quote.Vol, quote.Amount)
	return err
}

// GetIndexQuote 获取指定日期的指数行情
func (r *marketRepository) GetIndexQuote(ctx context.Context, indexCode string, tradeDate time.Time) (*models.IndexQuote, error) {
	query := `
		SELECT id, index_code, trade_date, close, open, high, low, pre_close, change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM index_quotes WHERE index_code = ? AND trade_date = ?
	`
	quote := &models.IndexQuote{}
	err := r.db.QueryRowContext(ctx, query, indexCode, tradeDate).Scan(
		&quote.ID, &quote.IndexCode, &quote.TradeDate, &quote.Close, &quote.Open, &quote.High, &quote.Low,
		&quote.PreClose, &quote.ChangeAmount, &quote.PctChg, &quote.Vol, &quote.Amount,
		&quote.CreatedAt, &quote.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return quote, nil
}

// GetIndexQuotesByCode 获取指定指数的行情数据
func (r *marketRepository) GetIndexQuotesByCode(ctx context.Context, indexCode string, startDate, endDate time.Time) ([]*models.IndexQuote, error) {
	query := `
		SELECT id, index_code, trade_date, close, open, high, low, pre_close, change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM index_quotes WHERE index_code = ? AND trade_date BETWEEN ? AND ? ORDER BY trade_date
	`
	rows, err := r.db.QueryContext(ctx, query, indexCode, startDate, endDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var quotes []*models.IndexQuote
	for rows.Next() {
		quote := &models.IndexQuote{}
		err := rows.Scan(
			&quote.ID, &quote.IndexCode, &quote.TradeDate, &quote.Close, &quote.Open, &quote.High, &quote.Low,
			&quote.PreClose, &quote.ChangeAmount, &quote.PctChg, &quote.Vol, &quote.Amount,
			&quote.CreatedAt, &quote.UpdatedAt)
		if err != nil {
			return nil, err
		}
		quotes = append(quotes, quote)
	}
	return quotes, nil
}

// GetIndexQuotesByDate 获取指定日期的所有指数行情
func (r *marketRepository) GetIndexQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.IndexQuote, error) {
	query := `
		SELECT id, index_code, trade_date, close, open, high, low, pre_close, change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM index_quotes WHERE trade_date = ? ORDER BY index_code
	`
	rows, err := r.db.QueryContext(ctx, query, tradeDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var quotes []*models.IndexQuote
	for rows.Next() {
		quote := &models.IndexQuote{}
		err := rows.Scan(
			&quote.ID, &quote.IndexCode, &quote.TradeDate, &quote.Close, &quote.Open, &quote.High, &quote.Low,
			&quote.PreClose, &quote.ChangeAmount, &quote.PctChg, &quote.Vol, &quote.Amount,
			&quote.CreatedAt, &quote.UpdatedAt)
		if err != nil {
			return nil, err
		}
		quotes = append(quotes, quote)
	}
	return quotes, nil
}

// UpdateIndexQuote 更新指数行情数据
func (r *marketRepository) UpdateIndexQuote(ctx context.Context, quote *models.IndexQuote) error {
	query := `
		UPDATE index_quotes SET close = ?, open = ?, high = ?, low = ?, pre_close = ?, change_amount = ?, pct_chg = ?, vol = ?, amount = ?, updated_at = NOW()
		WHERE index_code = ? AND trade_date = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		quote.Close, quote.Open, quote.High, quote.Low, quote.PreClose,
		quote.ChangeAmount, quote.PctChg, quote.Vol, quote.Amount,
		quote.IndexCode, quote.TradeDate)
	return err
}

// DeleteIndexQuote 删除指数行情数据
func (r *marketRepository) DeleteIndexQuote(ctx context.Context, indexCode string, tradeDate time.Time) error {
	query := `DELETE FROM index_quotes WHERE index_code = ? AND trade_date = ?`
	_, err := r.db.ExecContext(ctx, query, indexCode, tradeDate)
	return err
}

// BatchCreateIndexQuotes 批量创建指数行情数据
func (r *marketRepository) BatchCreateIndexQuotes(ctx context.Context, quotes []*models.IndexQuote) error {
	if len(quotes) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(quotes))
	valueArgs := make([]interface{}, 0, len(quotes)*11)

	for _, quote := range quotes {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			quote.IndexCode, quote.TradeDate, quote.Close, quote.Open, quote.High, quote.Low,
			quote.PreClose, quote.ChangeAmount, quote.PctChg, quote.Vol, quote.Amount)
	}

	query := fmt.Sprintf(`
		INSERT INTO index_quotes (index_code, trade_date, close, open, high, low, pre_close, change_amount, pct_chg, vol, amount, created_at, updated_at)
		VALUES %s
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateIndustryIndex 创建行业指数
func (r *marketRepository) CreateIndustryIndex(ctx context.Context, industry *models.IndustryIndex) error {
	query := `
		INSERT INTO industry_indexes (index_code, index_name, industry_level, parent_code, trade_date, open, high, low, close, pre_close, change_amount, pct_chg, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		industry.IndexCode, industry.IndexName, industry.IndustryLevel, industry.ParentCode,
		industry.TradeDate, industry.Open, industry.High, industry.Low, industry.Close,
		industry.PreClose, industry.ChangeAmount, industry.PctChg)
	return err
}

// GetIndustryIndexByCode 根据行业代码获取行业指数
func (r *marketRepository) GetIndustryIndexByCode(ctx context.Context, indexCode string) (*models.IndustryIndex, error) {
	query := `
		SELECT id, index_code, index_name, industry_level, parent_code, trade_date, open, high, low, close, pre_close, change_amount, pct_chg, created_at, updated_at
		FROM industry_indexes WHERE index_code = ?
	`
	industry := &models.IndustryIndex{}
	err := r.db.QueryRowContext(ctx, query, indexCode).Scan(
		&industry.ID, &industry.IndexCode, &industry.IndexName, &industry.IndustryLevel,
		&industry.ParentCode, &industry.TradeDate, &industry.Open, &industry.High, &industry.Low,
		&industry.Close, &industry.PreClose, &industry.ChangeAmount, &industry.PctChg,
		&industry.CreatedAt, &industry.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return industry, nil
}

// UpdateIndustryIndex 更新行业指数
func (r *marketRepository) UpdateIndustryIndex(ctx context.Context, industry *models.IndustryIndex) error {
	query := `
		UPDATE industry_indexes SET index_name = ?, industry_level = ?, parent_code = ?, trade_date = ?, open = ?, high = ?, low = ?, close = ?, pre_close = ?, change_amount = ?, pct_chg = ?, updated_at = NOW()
		WHERE index_code = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		industry.IndexName, industry.IndustryLevel, industry.ParentCode, industry.TradeDate,
		industry.Open, industry.High, industry.Low, industry.Close, industry.PreClose,
		industry.ChangeAmount, industry.PctChg, industry.IndexCode)
	return err
}

// DeleteIndustryIndex 删除行业指数
func (r *marketRepository) DeleteIndustryIndex(ctx context.Context, indexCode string) error {
	query := `DELETE FROM industry_indexes WHERE index_code = ?`
	_, err := r.db.ExecContext(ctx, query, indexCode)
	return err
}

// ListIndustryIndices 获取行业指数列表
func (r *marketRepository) ListIndustryIndices(ctx context.Context, limit, offset int) ([]*models.IndustryIndex, error) {
	query := `
		SELECT id, index_code, index_name, industry_level, parent_code, trade_date, open, high, low, close, pre_close, change_amount, pct_chg, created_at, updated_at
		FROM industry_indexes ORDER BY id LIMIT ? OFFSET ?
	`
	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var industries []*models.IndustryIndex
	for rows.Next() {
		industry := &models.IndustryIndex{}
		err := rows.Scan(
			&industry.ID, &industry.IndexCode, &industry.IndexName, &industry.IndustryLevel,
			&industry.ParentCode, &industry.TradeDate, &industry.Open, &industry.High, &industry.Low,
			&industry.Close, &industry.PreClose, &industry.ChangeAmount, &industry.PctChg,
			&industry.CreatedAt, &industry.UpdatedAt)
		if err != nil {
			return nil, err
		}
		industries = append(industries, industry)
	}
	return industries, nil
}

// BatchCreateIndustryIndices 批量创建行业指数
func (r *marketRepository) BatchCreateIndustryIndices(ctx context.Context, industries []*models.IndustryIndex) error {
	if len(industries) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(industries))
	valueArgs := make([]interface{}, 0, len(industries)*12)

	for _, industry := range industries {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			industry.IndexCode, industry.IndexName, industry.IndustryLevel, industry.ParentCode,
			industry.TradeDate, industry.Open, industry.High, industry.Low, industry.Close,
			industry.PreClose, industry.ChangeAmount, industry.PctChg)
	}

	query := fmt.Sprintf(`
		INSERT INTO industry_indexes (index_code, index_name, industry_level, parent_code, trade_date, open, high, low, close, pre_close, change_amount, pct_chg, created_at, updated_at)
		VALUES %s
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateSector 创建板块分类
func (r *marketRepository) CreateSector(ctx context.Context, sector *models.Sector) error {
	query := `
		INSERT INTO sector_classifications (sector_code, sector_name, level, parent_code, created_at, updated_at)
		VALUES (?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		sector.SectorCode, sector.SectorName, sector.Level, sector.ParentCode)
	return err
}

// GetSectorByCode 根据板块代码获取板块信息
func (r *marketRepository) GetSectorByCode(ctx context.Context, sectorCode string) (*models.Sector, error) {
	query := `
		SELECT id, sector_code, sector_name, level, parent_code, created_at, updated_at
		FROM sector_classifications WHERE sector_code = ?
	`
	sector := &models.Sector{}
	err := r.db.QueryRowContext(ctx, query, sectorCode).Scan(
		&sector.ID, &sector.SectorCode, &sector.SectorName, &sector.Level,
		&sector.ParentCode, &sector.CreatedAt, &sector.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return sector, nil
}

// UpdateSector 更新板块信息
func (r *marketRepository) UpdateSector(ctx context.Context, sector *models.Sector) error {
	query := `
		UPDATE sector_classifications SET sector_name = ?, level = ?, parent_code = ?, updated_at = NOW()
		WHERE sector_code = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		sector.SectorName, sector.Level, sector.ParentCode, sector.SectorCode)
	return err
}

// DeleteSector 删除板块信息
func (r *marketRepository) DeleteSector(ctx context.Context, sectorCode string) error {
	query := `DELETE FROM sector_classifications WHERE sector_code = ?`
	_, err := r.db.ExecContext(ctx, query, sectorCode)
	return err
}

// ListSectors 获取板块列表
func (r *marketRepository) ListSectors(ctx context.Context, limit, offset int) ([]*models.Sector, error) {
	query := `
		SELECT id, sector_code, sector_name, level, parent_code, created_at, updated_at
		FROM sector_classifications ORDER BY id LIMIT ? OFFSET ?
	`
	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sectors []*models.Sector
	for rows.Next() {
		sector := &models.Sector{}
		err := rows.Scan(
			&sector.ID, &sector.SectorCode, &sector.SectorName, &sector.Level,
			&sector.ParentCode, &sector.CreatedAt, &sector.UpdatedAt)
		if err != nil {
			return nil, err
		}
		sectors = append(sectors, sector)
	}
	return sectors, nil
}

// BatchCreateSectors 批量创建板块分类
func (r *marketRepository) BatchCreateSectors(ctx context.Context, sectors []*models.Sector) error {
	if len(sectors) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(sectors))
	valueArgs := make([]interface{}, 0, len(sectors)*4)

	for _, sector := range sectors {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			sector.SectorCode, sector.SectorName, sector.Level, sector.ParentCode)
	}

	query := fmt.Sprintf(`
		INSERT INTO sector_classifications (sector_code, sector_name, level, parent_code, created_at, updated_at)
		VALUES %s
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateSectorConstituent 创建板块成分股
func (r *marketRepository) CreateSectorConstituent(ctx context.Context, constituent *models.SectorConstituent) error {
	query := `
		INSERT INTO sector_stocks (sector_code, stock_code, stock_name, weight, in_date, out_date, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		constituent.SectorCode, constituent.StockCode, constituent.StockName,
		constituent.Weight, constituent.InDate, constituent.OutDate)
	return err
}

// GetSectorConstituents 获取板块成分股
func (r *marketRepository) GetSectorConstituents(ctx context.Context, sectorCode string) ([]*models.SectorConstituent, error) {
	query := `
		SELECT id, sector_code, stock_code, stock_name, weight, in_date, out_date, created_at, updated_at
		FROM sector_stocks WHERE sector_code = ? ORDER BY weight DESC
	`
	rows, err := r.db.QueryContext(ctx, query, sectorCode)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var constituents []*models.SectorConstituent
	for rows.Next() {
		constituent := &models.SectorConstituent{}
		err := rows.Scan(
			&constituent.ID, &constituent.SectorCode, &constituent.StockCode, &constituent.StockName,
			&constituent.Weight, &constituent.InDate, &constituent.OutDate,
			&constituent.CreatedAt, &constituent.UpdatedAt)
		if err != nil {
			return nil, err
		}
		constituents = append(constituents, constituent)
	}
	return constituents, nil
}

// GetStockSectors 获取股票所属板块
func (r *marketRepository) GetStockSectors(ctx context.Context, stockCode string) ([]*models.SectorConstituent, error) {
	query := `
		SELECT id, sector_code, stock_code, stock_name, weight, in_date, out_date, created_at, updated_at
		FROM sector_stocks WHERE stock_code = ? ORDER BY sector_code
	`
	rows, err := r.db.QueryContext(ctx, query, stockCode)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var constituents []*models.SectorConstituent
	for rows.Next() {
		constituent := &models.SectorConstituent{}
		err := rows.Scan(
			&constituent.ID, &constituent.SectorCode, &constituent.StockCode, &constituent.StockName,
			&constituent.Weight, &constituent.InDate, &constituent.OutDate,
			&constituent.CreatedAt, &constituent.UpdatedAt)
		if err != nil {
			return nil, err
		}
		constituents = append(constituents, constituent)
	}
	return constituents, nil
}

// UpdateSectorConstituent 更新板块成分股
func (r *marketRepository) UpdateSectorConstituent(ctx context.Context, constituent *models.SectorConstituent) error {
	query := `
		UPDATE sector_stocks SET stock_name = ?, weight = ?, in_date = ?, out_date = ?, updated_at = NOW()
		WHERE sector_code = ? AND stock_code = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		constituent.StockName, constituent.Weight, constituent.InDate, constituent.OutDate,
		constituent.SectorCode, constituent.StockCode)
	return err
}

// DeleteSectorConstituent 删除板块成分股
func (r *marketRepository) DeleteSectorConstituent(ctx context.Context, sectorCode, stockCode string) error {
	query := `DELETE FROM sector_stocks WHERE sector_code = ? AND stock_code = ?`
	_, err := r.db.ExecContext(ctx, query, sectorCode, stockCode)
	return err
}

// BatchCreateSectorConstituents 批量创建板块成分股
func (r *marketRepository) BatchCreateSectorConstituents(ctx context.Context, constituents []*models.SectorConstituent) error {
	if len(constituents) == 0 {
		return nil
	}

	valueStrings := make([]string, 0, len(constituents))
	valueArgs := make([]interface{}, 0, len(constituents)*6)

	for _, constituent := range constituents {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			constituent.SectorCode, constituent.StockCode, constituent.StockName,
			constituent.Weight, constituent.InDate, constituent.OutDate)
	}

	query := fmt.Sprintf(`
		INSERT INTO sector_stocks (sector_code, stock_code, stock_name, weight, in_date, out_date, created_at, updated_at)
		VALUES %s
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}