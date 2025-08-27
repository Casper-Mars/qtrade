package models

import (
	"time"
)

// FinancialReport 财务报表数据模型
type FinancialReport struct {
	ID           int64     `json:"id" db:"id"`                       // 主键ID
	Symbol       string    `json:"symbol" db:"symbol"`               // 股票代码
	TSCode       string    `json:"ts_code" db:"ts_code"`             // Tushare代码
	AnnDate      time.Time `json:"ann_date" db:"ann_date"`           // 公告日期
	FDate        time.Time `json:"f_date" db:"f_date"`               // 报告期
	EndDate      time.Time `json:"end_date" db:"end_date"`           // 报告期结束日期
	ReportType   string    `json:"report_type" db:"report_type"`     // 报告类型(1-年报,2-半年报,3-季报)
	
	// 资产负债表字段
	TotalAssets     string `json:"total_assets" db:"total_assets"`         // 总资产
	TotalLiab       string `json:"total_liab" db:"total_liab"`             // 总负债
	TotalHldrEqyExcMinInt string `json:"total_hldr_eqy_exc_min_int" db:"total_hldr_eqy_exc_min_int"` // 股东权益合计(不含少数股东权益)
	TotalCurAssets  string `json:"total_cur_assets" db:"total_cur_assets"`   // 流动资产合计
	TotalCurLiab    string `json:"total_cur_liab" db:"total_cur_liab"`       // 流动负债合计
	MoneyFunds      string `json:"money_funds" db:"money_funds"`             // 货币资金
	
	// 利润表字段
	Revenue         string `json:"revenue" db:"revenue"`                     // 营业总收入
	OperCost        string `json:"oper_cost" db:"oper_cost"`               // 营业总成本
	NIncome         string `json:"n_income" db:"n_income"`                 // 净利润
	NIncomeAttrP    string `json:"n_income_attr_p" db:"n_income_attr_p"`   // 归属于母公司所有者的净利润
	BasicEps        string `json:"basic_eps" db:"basic_eps"`               // 基本每股收益
	
	// 现金流量表字段
	NCfFrOa         string `json:"n_cf_fr_oa" db:"n_cf_fr_oa"`             // 经营活动产生的现金流量净额
	NCfFrInvA       string `json:"n_cf_fr_inv_a" db:"n_cf_fr_inv_a"`       // 投资活动产生的现金流量净额
	NCfFrFncA       string `json:"n_cf_fr_fnc_a" db:"n_cf_fr_fnc_a"`       // 筹资活动产生的现金流量净额
	
	CreatedAt       time.Time `json:"created_at" db:"created_at"`           // 创建时间
	UpdatedAt       time.Time `json:"updated_at" db:"updated_at"`           // 更新时间
}

// FinancialIndicator 财务指标数据模型
type FinancialIndicator struct {
	ID           int64     `json:"id" db:"id"`                       // 主键ID
	Symbol       string    `json:"symbol" db:"symbol"`               // 股票代码
	TSCode       string    `json:"ts_code" db:"ts_code"`             // Tushare代码
	AnnDate      time.Time `json:"ann_date" db:"ann_date"`           // 公告日期
	EndDate      time.Time `json:"end_date" db:"end_date"`           // 报告期
	
	// 盈利能力指标
	ROE          string    `json:"roe" db:"roe"`                     // 净资产收益率
	ROA          string    `json:"roa" db:"roa"`                     // 总资产收益率
	ROIC         string    `json:"roic" db:"roic"`                   // 投入资本回报率
	GrossMargin  string    `json:"gross_margin" db:"gross_margin"`   // 毛利率
	NetMargin    string    `json:"net_margin" db:"net_margin"`       // 净利率
	OperMargin   string    `json:"oper_margin" db:"oper_margin"`     // 营业利润率
	
	// 成长能力指标
	RevenueYoy   string    `json:"revenue_yoy" db:"revenue_yoy"`     // 营业收入同比增长率
	NIncomeYoy   string    `json:"n_income_yoy" db:"n_income_yoy"`   // 净利润同比增长率
	AssetsYoy    string    `json:"assets_yoy" db:"assets_yoy"`       // 总资产同比增长率
	
	// 偿债能力指标
	DebtToAssets string    `json:"debt_to_assets" db:"debt_to_assets"` // 资产负债率
	CurrentRatio string    `json:"current_ratio" db:"current_ratio"`   // 流动比率
	QuickRatio   string    `json:"quick_ratio" db:"quick_ratio"`       // 速动比率
	
	// 运营能力指标
	AssetTurnover     string `json:"asset_turnover" db:"asset_turnover"`         // 总资产周转率
	InventoryTurnover string `json:"inventory_turnover" db:"inventory_turnover"` // 存货周转率
	ArTurnover        string `json:"ar_turnover" db:"ar_turnover"`               // 应收账款周转率
	
	// 估值指标
	PE           string    `json:"pe" db:"pe"`                       // 市盈率
	PB           string    `json:"pb" db:"pb"`                       // 市净率
	PS           string    `json:"ps" db:"ps"`                       // 市销率
	PCF          string    `json:"pcf" db:"pcf"`                     // 市现率
	
	CreatedAt    time.Time `json:"created_at" db:"created_at"`       // 创建时间
	UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`       // 更新时间
}

// TableName 返回表名
func (FinancialReport) TableName() string {
	return "financial_reports"
}

func (FinancialIndicator) TableName() string {
	return "financial_indicators"
}