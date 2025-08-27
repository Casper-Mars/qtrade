package models

import (
	"time"
)

// IndexBasic 大盘指数基础信息模型
type IndexBasic struct {
	ID        int64     `json:"id" db:"id"`                   // 主键ID
	IndexCode string    `json:"index_code" db:"index_code"`   // 指数代码
	IndexName string    `json:"index_name" db:"index_name"`   // 指数名称
	Market    string    `json:"market" db:"market"`           // 市场类型
	Publisher string    `json:"publisher" db:"publisher"`     // 发布方
	Category  string    `json:"category" db:"category"`       // 指数类别
	BaseDate  time.Time `json:"base_date" db:"base_date"`     // 基期日期
	BasePoint string    `json:"base_point" db:"base_point"`   // 基点
	ListDate  time.Time `json:"list_date" db:"list_date"`     // 发布日期
	CreatedAt time.Time `json:"created_at" db:"created_at"`   // 创建时间
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`   // 更新时间
}

// IndexQuote 指数行情数据模型
type IndexQuote struct {
	ID           int64     `json:"id" db:"id"`                       // 主键ID
	IndexCode    string    `json:"index_code" db:"index_code"`       // 指数代码
	TradeDate    time.Time `json:"trade_date" db:"trade_date"`       // 交易日期
	Open         string    `json:"open" db:"open"`                   // 开盘点数
	High         string    `json:"high" db:"high"`                   // 最高点数
	Low          string    `json:"low" db:"low"`                     // 最低点数
	Close        string    `json:"close" db:"close"`                 // 收盘点数
	PreClose     string    `json:"pre_close" db:"pre_close"`         // 昨收点数
	ChangeAmount string    `json:"change_amount" db:"change_amount"` // 涨跌点数
	PctChg       string    `json:"pct_chg" db:"pct_chg"`             // 涨跌幅(%)
	Vol          string    `json:"vol" db:"vol"`                     // 成交量(手)
	Amount       string    `json:"amount" db:"amount"`               // 成交额(千元)
	CreatedAt    time.Time `json:"created_at" db:"created_at"`       // 创建时间
	UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`       // 更新时间
}

// IndustryIndex 行业指数数据模型
type IndustryIndex struct {
	ID            int64     `json:"id" db:"id"`                         // 主键ID
	IndexCode     string    `json:"index_code" db:"index_code"`         // 指数代码
	IndexName     string    `json:"index_name" db:"index_name"`         // 指数名称
	IndustryLevel string    `json:"industry_level" db:"industry_level"` // 行业级别(一级/二级/三级)
	ParentCode    string    `json:"parent_code" db:"parent_code"`       // 父级行业代码
	TradeDate     time.Time `json:"trade_date" db:"trade_date"`         // 交易日期
	Open          string    `json:"open" db:"open"`                     // 开盘点数
	High          string    `json:"high" db:"high"`                     // 最高点数
	Low           string    `json:"low" db:"low"`                       // 最低点数
	Close         string    `json:"close" db:"close"`                   // 收盘点数
	PreClose      string    `json:"pre_close" db:"pre_close"`           // 昨收点数
	ChangeAmount  string    `json:"change_amount" db:"change_amount"`   // 涨跌点数
	PctChg        string    `json:"pct_chg" db:"pct_chg"`               // 涨跌幅(%)
	CreatedAt     time.Time `json:"created_at" db:"created_at"`         // 创建时间
	UpdatedAt     time.Time `json:"updated_at" db:"updated_at"`         // 更新时间
}

// Sector 板块分类数据模型
type Sector struct {
	ID         int64     `json:"id" db:"id"`                   // 主键ID
	SectorCode string    `json:"sector_code" db:"sector_code"` // 板块代码
	SectorName string    `json:"sector_name" db:"sector_name"` // 板块名称
	SectorType string    `json:"sector_type" db:"sector_type"` // 板块类型(概念/地域/风格)
	ParentCode string    `json:"parent_code" db:"parent_code"` // 父级板块代码
	Level      int       `json:"level" db:"level"`             // 板块层级
	IsActive   bool      `json:"is_active" db:"is_active"`     // 是否有效
	CreatedAt  time.Time `json:"created_at" db:"created_at"`   // 创建时间
	UpdatedAt  time.Time `json:"updated_at" db:"updated_at"`   // 更新时间
}

// SectorConstituent 板块成分股数据模型
type SectorConstituent struct {
	ID         int64      `json:"id" db:"id"`                   // 主键ID
	SectorCode string     `json:"sector_code" db:"sector_code"` // 板块代码
	StockCode  string     `json:"stock_code" db:"stock_code"`   // 股票代码
	StockName  string     `json:"stock_name" db:"stock_name"`   // 股票名称
	Weight     string     `json:"weight" db:"weight"`           // 权重(%)
	InDate     time.Time  `json:"in_date" db:"in_date"`         // 纳入日期
	OutDate    *time.Time `json:"out_date" db:"out_date"`       // 剔除日期
	IsActive   bool       `json:"is_active" db:"is_active"`     // 是否有效
	CreatedAt  time.Time  `json:"created_at" db:"created_at"`   // 创建时间
	UpdatedAt  time.Time  `json:"updated_at" db:"updated_at"`   // 更新时间
}

// TableName 返回表名
func (IndexBasic) TableName() string {
	return "indices"
}

func (IndexQuote) TableName() string {
	return "index_quotes"
}

func (IndustryIndex) TableName() string {
	return "industry_indices"
}

func (Sector) TableName() string {
	return "sectors"
}

func (SectorConstituent) TableName() string {
	return "sector_constituents"
}