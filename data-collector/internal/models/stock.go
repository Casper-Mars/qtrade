package models

import (
	"time"
)

// StockBasic 股票基础信息模型
type StockBasic struct {
	ID        int64     `json:"id" db:"id"`                   // 主键ID
	Symbol    string    `json:"symbol" db:"symbol"`           // 股票代码
	TSCode    string    `json:"ts_code" db:"ts_code"`         // Tushare代码
	Name      string    `json:"name" db:"name"`               // 股票名称
	Area      string    `json:"area" db:"area"`               // 地域
	Industry  string    `json:"industry" db:"industry"`       // 行业
	Market    string    `json:"market" db:"market"`           // 市场类型
	ListDate  time.Time `json:"list_date" db:"list_date"`     // 上市日期
	IsHS      string    `json:"is_hs" db:"is_hs"`             // 是否沪深港通
	CreatedAt time.Time `json:"created_at" db:"created_at"`   // 创建时间
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`   // 更新时间
}

// StockQuote 股票行情数据模型
type StockQuote struct {
	ID           int64     `json:"id" db:"id"`                       // 主键ID
	Symbol       string    `json:"symbol" db:"symbol"`               // 股票代码
	TradeDate    time.Time `json:"trade_date" db:"trade_date"`       // 交易日期
	Open         string    `json:"open" db:"open"`                   // 开盘价
	High         string    `json:"high" db:"high"`                   // 最高价
	Low          string    `json:"low" db:"low"`                     // 最低价
	Close        string    `json:"close" db:"close"`                 // 收盘价
	PreClose     string    `json:"pre_close" db:"pre_close"`         // 昨收价
	Change       string    `json:"change" db:"change_amount"`        // 涨跌额
	PctChg       string    `json:"pct_chg" db:"pct_chg"`             // 涨跌幅
	Vol          string    `json:"vol" db:"vol"`                     // 成交量
	Amount       string    `json:"amount" db:"amount"`               // 成交额
	CreatedAt    time.Time `json:"created_at" db:"created_at"`       // 创建时间
	UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`       // 更新时间
}

// AdjFactor 复权因子数据模型
type AdjFactor struct {
	ID        int64     `json:"id" db:"id"`                   // 主键ID
	TSCode    string    `json:"ts_code" db:"ts_code"`         // 股票代码
	TradeDate time.Time `json:"trade_date" db:"trade_date"`   // 交易日期
	AdjFactor string    `json:"adj_factor" db:"adj_factor"`   // 复权因子
	CreatedAt time.Time `json:"created_at" db:"created_at"`   // 创建时间
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`   // 更新时间
}

// TableName 返回表名
func (StockBasic) TableName() string {
	return "stocks"
}

func (StockQuote) TableName() string {
	return "stock_quotes"
}

func (AdjFactor) TableName() string {
	return "stock_adj_factors"
}