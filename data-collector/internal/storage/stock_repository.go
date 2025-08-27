package storage

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"time"

	"data-collector/internal/models"
)

// StockRepository 股票数据仓库接口
type StockRepository interface {
	// 股票基础信息相关操作
	CreateStock(ctx context.Context, stock *models.StockBasic) error
	GetStockBySymbol(ctx context.Context, symbol string) (*models.StockBasic, error)
	GetStockByTSCode(ctx context.Context, tsCode string) (*models.StockBasic, error)
	UpdateStock(ctx context.Context, stock *models.StockBasic) error
	DeleteStock(ctx context.Context, symbol string) error
	ListStocks(ctx context.Context, limit, offset int) ([]*models.StockBasic, error)
	BatchCreateStocks(ctx context.Context, stocks []*models.StockBasic) error

	// 股票行情数据相关操作
	CreateStockQuote(ctx context.Context, quote *models.StockQuote) error
	GetStockQuote(ctx context.Context, symbol string, tradeDate time.Time) (*models.StockQuote, error)
	GetStockQuotesBySymbol(ctx context.Context, symbol string, startDate, endDate time.Time) ([]*models.StockQuote, error)
	GetStockQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.StockQuote, error)
	UpdateStockQuote(ctx context.Context, quote *models.StockQuote) error
	DeleteStockQuote(ctx context.Context, symbol string, tradeDate time.Time) error
	BatchCreateStockQuotes(ctx context.Context, quotes []*models.StockQuote) error

	// 复权因子相关操作
	CreateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error
	GetAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) (*models.AdjFactor, error)
	GetAdjFactorsByTSCode(ctx context.Context, tsCode string, startDate, endDate time.Time) ([]*models.AdjFactor, error)
	UpdateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error
	DeleteAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) error
	BatchCreateAdjFactors(ctx context.Context, adjFactors []*models.AdjFactor) error
}

// stockRepository 股票数据仓库实现
type stockRepository struct {
	db *sql.DB
}

// NewStockRepository 创建股票数据仓库
func NewStockRepository(db *sql.DB) StockRepository {
	return &stockRepository{
		db: db,
	}
}

// CreateStock 创建股票基础信息
func (r *stockRepository) CreateStock(ctx context.Context, stock *models.StockBasic) error {
	query := `
		INSERT INTO stocks (symbol, ts_code, name, area, industry, market, list_date, is_hs, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		stock.Symbol, stock.TSCode, stock.Name, stock.Area,
		stock.Industry, stock.Market, stock.ListDate, stock.IsHS)
	return err
}

// GetStockBySymbol 根据股票代码获取股票信息
func (r *stockRepository) GetStockBySymbol(ctx context.Context, symbol string) (*models.StockBasic, error) {
	query := `
		SELECT id, symbol, ts_code, name, area, industry, market, list_date, is_hs, created_at, updated_at
		FROM stocks WHERE symbol = ?
	`
	stock := &models.StockBasic{}
	err := r.db.QueryRowContext(ctx, query, symbol).Scan(
		&stock.ID, &stock.Symbol, &stock.TSCode, &stock.Name, &stock.Area,
		&stock.Industry, &stock.Market, &stock.ListDate, &stock.IsHS,
		&stock.CreatedAt, &stock.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return stock, nil
}

// GetStockByTSCode 根据Tushare代码获取股票信息
func (r *stockRepository) GetStockByTSCode(ctx context.Context, tsCode string) (*models.StockBasic, error) {
	query := `
		SELECT id, symbol, ts_code, name, area, industry, market, list_date, is_hs, created_at, updated_at
		FROM stocks WHERE ts_code = ?
	`
	stock := &models.StockBasic{}
	err := r.db.QueryRowContext(ctx, query, tsCode).Scan(
		&stock.ID, &stock.Symbol, &stock.TSCode, &stock.Name, &stock.Area,
		&stock.Industry, &stock.Market, &stock.ListDate, &stock.IsHS,
		&stock.CreatedAt, &stock.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return stock, nil
}

// UpdateStock 更新股票信息
func (r *stockRepository) UpdateStock(ctx context.Context, stock *models.StockBasic) error {
	query := `
		UPDATE stocks SET name = ?, area = ?, industry = ?, market = ?, 
		       list_date = ?, is_hs = ?, updated_at = NOW()
		WHERE symbol = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		stock.Name, stock.Area, stock.Industry, stock.Market,
		stock.ListDate, stock.IsHS, stock.Symbol)
	return err
}

// DeleteStock 删除股票信息
func (r *stockRepository) DeleteStock(ctx context.Context, symbol string) error {
	query := `DELETE FROM stocks WHERE symbol = ?`
	_, err := r.db.ExecContext(ctx, query, symbol)
	return err
}

// ListStocks 获取股票列表
func (r *stockRepository) ListStocks(ctx context.Context, limit, offset int) ([]*models.StockBasic, error) {
	query := `
		SELECT id, symbol, ts_code, name, area, industry, market, list_date, is_hs, created_at, updated_at
		FROM stocks ORDER BY symbol LIMIT ? OFFSET ?
	`
	rows, err := r.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var stocks []*models.StockBasic
	for rows.Next() {
		stock := &models.StockBasic{}
		err := rows.Scan(
			&stock.ID, &stock.Symbol, &stock.TSCode, &stock.Name, &stock.Area,
			&stock.Industry, &stock.Market, &stock.ListDate, &stock.IsHS,
			&stock.CreatedAt, &stock.UpdatedAt)
		if err != nil {
			return nil, err
		}
		stocks = append(stocks, stock)
	}
	return stocks, nil
}

// BatchCreateStocks 批量创建股票信息
func (r *stockRepository) BatchCreateStocks(ctx context.Context, stocks []*models.StockBasic) error {
	if len(stocks) == 0 {
		return nil
	}

	// 构建批量插入SQL
	valueStrings := make([]string, 0, len(stocks))
	valueArgs := make([]interface{}, 0, len(stocks)*8)

	for _, stock := range stocks {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			stock.Symbol, stock.TSCode, stock.Name, stock.Area,
			stock.Industry, stock.Market, stock.ListDate, stock.IsHS)
	}

	query := fmt.Sprintf(`
		INSERT INTO stocks (symbol, ts_code, name, area, industry, market, list_date, is_hs, created_at, updated_at)
		VALUES %s
		ON DUPLICATE KEY UPDATE
			name = VALUES(name),
			area = VALUES(area),
			industry = VALUES(industry),
			market = VALUES(market),
			list_date = VALUES(list_date),
			is_hs = VALUES(is_hs),
			updated_at = NOW()
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateStockQuote 创建股票行情数据
func (r *stockRepository) CreateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	query := `
		INSERT INTO stock_quotes (symbol, trade_date, open, high, low, close, pre_close, 
		                         change_amount, pct_chg, vol, amount, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		quote.Symbol, quote.TradeDate, quote.Open, quote.High, quote.Low,
		quote.Close, quote.PreClose, quote.Change, quote.PctChg,
		quote.Vol, quote.Amount)
	return err
}

// GetStockQuote 获取指定股票指定日期的行情数据
func (r *stockRepository) GetStockQuote(ctx context.Context, symbol string, tradeDate time.Time) (*models.StockQuote, error) {
	query := `
		SELECT id, symbol, trade_date, open, high, low, close, pre_close,
		       change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM stock_quotes WHERE symbol = ? AND trade_date = ?
	`
	quote := &models.StockQuote{}
	err := r.db.QueryRowContext(ctx, query, symbol, tradeDate).Scan(
		&quote.ID, &quote.Symbol, &quote.TradeDate, &quote.Open, &quote.High,
		&quote.Low, &quote.Close, &quote.PreClose, &quote.Change,
		&quote.PctChg, &quote.Vol, &quote.Amount,
		&quote.CreatedAt, &quote.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return quote, nil
}

// GetStockQuotesBySymbol 获取指定股票指定时间范围的行情数据
func (r *stockRepository) GetStockQuotesBySymbol(ctx context.Context, symbol string, startDate, endDate time.Time) ([]*models.StockQuote, error) {
	query := `
		SELECT id, symbol, trade_date, open, high, low, close, pre_close,
		       change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM stock_quotes 
		WHERE symbol = ? AND trade_date >= ? AND trade_date <= ?
		ORDER BY trade_date
	`
	rows, err := r.db.QueryContext(ctx, query, symbol, startDate, endDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var quotes []*models.StockQuote
	for rows.Next() {
		quote := &models.StockQuote{}
		err := rows.Scan(
			&quote.ID, &quote.Symbol, &quote.TradeDate, &quote.Open, &quote.High,
			&quote.Low, &quote.Close, &quote.PreClose, &quote.Change,
			&quote.PctChg, &quote.Vol, &quote.Amount,
			&quote.CreatedAt, &quote.UpdatedAt)
		if err != nil {
			return nil, err
		}
		quotes = append(quotes, quote)
	}
	return quotes, nil
}

// GetStockQuotesByDate 获取指定日期所有股票的行情数据
func (r *stockRepository) GetStockQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.StockQuote, error) {
	query := `
		SELECT id, symbol, trade_date, open, high, low, close, pre_close,
		       change_amount, pct_chg, vol, amount, created_at, updated_at
		FROM stock_quotes WHERE trade_date = ? ORDER BY symbol
	`
	rows, err := r.db.QueryContext(ctx, query, tradeDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var quotes []*models.StockQuote
	for rows.Next() {
		quote := &models.StockQuote{}
		err := rows.Scan(
			&quote.ID, &quote.Symbol, &quote.TradeDate, &quote.Open, &quote.High,
			&quote.Low, &quote.Close, &quote.PreClose, &quote.Change,
			&quote.PctChg, &quote.Vol, &quote.Amount,
			&quote.CreatedAt, &quote.UpdatedAt)
		if err != nil {
			return nil, err
		}
		quotes = append(quotes, quote)
	}
	return quotes, nil
}

// UpdateStockQuote 更新股票行情数据
func (r *stockRepository) UpdateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	query := `
		UPDATE stock_quotes SET open = ?, high = ?, low = ?, close = ?, pre_close = ?,
		       change_amount = ?, pct_chg = ?, vol = ?, amount = ?, updated_at = NOW()
		WHERE symbol = ? AND trade_date = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		quote.Open, quote.High, quote.Low, quote.Close, quote.PreClose,
		quote.Change, quote.PctChg, quote.Vol, quote.Amount,
		quote.Symbol, quote.TradeDate)
	return err
}

// DeleteStockQuote 删除股票行情数据
func (r *stockRepository) DeleteStockQuote(ctx context.Context, symbol string, tradeDate time.Time) error {
	query := `DELETE FROM stock_quotes WHERE symbol = ? AND trade_date = ?`
	_, err := r.db.ExecContext(ctx, query, symbol, tradeDate)
	return err
}

// BatchCreateStockQuotes 批量创建股票行情数据
func (r *stockRepository) BatchCreateStockQuotes(ctx context.Context, quotes []*models.StockQuote) error {
	if len(quotes) == 0 {
		return nil
	}

	// 构建批量插入SQL
	valueStrings := make([]string, 0, len(quotes))
	valueArgs := make([]interface{}, 0, len(quotes)*11)

	for _, quote := range quotes {
		valueStrings = append(valueStrings, "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			quote.Symbol, quote.TradeDate, quote.Open, quote.High, quote.Low,
			quote.Close, quote.PreClose, quote.Change, quote.PctChg,
			quote.Vol, quote.Amount)
	}

	query := fmt.Sprintf(`
		INSERT INTO stock_quotes (symbol, trade_date, open, high, low, close, pre_close,
		                         change_amount, pct_chg, vol, amount, created_at, updated_at)
		VALUES %s
		ON DUPLICATE KEY UPDATE
			open = VALUES(open),
			high = VALUES(high),
			low = VALUES(low),
			close = VALUES(close),
			pre_close = VALUES(pre_close),
			change_amount = VALUES(change_amount),
			pct_chg = VALUES(pct_chg),
			vol = VALUES(vol),
			amount = VALUES(amount),
			updated_at = NOW()
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}

// CreateAdjFactor 创建复权因子数据
func (r *stockRepository) CreateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	query := `
		INSERT INTO stock_adj_factors (ts_code, trade_date, adj_factor, created_at, updated_at)
		VALUES (?, ?, ?, NOW(), NOW())
	`
	_, err := r.db.ExecContext(ctx, query,
		adjFactor.TSCode, adjFactor.TradeDate, adjFactor.AdjFactor)
	return err
}

// GetAdjFactor 获取指定股票指定日期的复权因子
func (r *stockRepository) GetAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) (*models.AdjFactor, error) {
	query := `
		SELECT id, ts_code, trade_date, adj_factor, created_at, updated_at
		FROM stock_adj_factors WHERE ts_code = ? AND trade_date = ?
	`
	adjFactor := &models.AdjFactor{}
	err := r.db.QueryRowContext(ctx, query, tsCode, tradeDate).Scan(
		&adjFactor.ID, &adjFactor.TSCode, &adjFactor.TradeDate,
		&adjFactor.AdjFactor, &adjFactor.CreatedAt, &adjFactor.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return adjFactor, nil
}

// GetAdjFactorsByTSCode 获取指定股票指定时间范围的复权因子
func (r *stockRepository) GetAdjFactorsByTSCode(ctx context.Context, tsCode string, startDate, endDate time.Time) ([]*models.AdjFactor, error) {
	query := `
		SELECT id, ts_code, trade_date, adj_factor, created_at, updated_at
		FROM stock_adj_factors 
		WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
		ORDER BY trade_date
	`
	rows, err := r.db.QueryContext(ctx, query, tsCode, startDate, endDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var adjFactors []*models.AdjFactor
	for rows.Next() {
		adjFactor := &models.AdjFactor{}
		err := rows.Scan(
			&adjFactor.ID, &adjFactor.TSCode, &adjFactor.TradeDate,
			&adjFactor.AdjFactor, &adjFactor.CreatedAt, &adjFactor.UpdatedAt)
		if err != nil {
			return nil, err
		}
		adjFactors = append(adjFactors, adjFactor)
	}
	return adjFactors, nil
}

// UpdateAdjFactor 更新复权因子数据
func (r *stockRepository) UpdateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	query := `
		UPDATE stock_adj_factors SET adj_factor = ?, updated_at = NOW()
		WHERE ts_code = ? AND trade_date = ?
	`
	_, err := r.db.ExecContext(ctx, query,
		adjFactor.AdjFactor, adjFactor.TSCode, adjFactor.TradeDate)
	return err
}

// DeleteAdjFactor 删除复权因子数据
func (r *stockRepository) DeleteAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) error {
	query := `DELETE FROM stock_adj_factors WHERE ts_code = ? AND trade_date = ?`
	_, err := r.db.ExecContext(ctx, query, tsCode, tradeDate)
	return err
}

// BatchCreateAdjFactors 批量创建复权因子数据
func (r *stockRepository) BatchCreateAdjFactors(ctx context.Context, adjFactors []*models.AdjFactor) error {
	if len(adjFactors) == 0 {
		return nil
	}

	// 构建批量插入SQL
	valueStrings := make([]string, 0, len(adjFactors))
	valueArgs := make([]interface{}, 0, len(adjFactors)*3)

	for _, adjFactor := range adjFactors {
		valueStrings = append(valueStrings, "(?, ?, ?, NOW(), NOW())")
		valueArgs = append(valueArgs,
			adjFactor.TSCode, adjFactor.TradeDate, adjFactor.AdjFactor)
	}

	query := fmt.Sprintf(`
		INSERT INTO stock_adj_factors (ts_code, trade_date, adj_factor, created_at, updated_at)
		VALUES %s
		ON DUPLICATE KEY UPDATE
			adj_factor = VALUES(adj_factor),
			updated_at = NOW()
	`, strings.Join(valueStrings, ","))

	_, err := r.db.ExecContext(ctx, query, valueArgs...)
	return err
}