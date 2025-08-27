package validator

import (
	"fmt"
	"regexp"
	"strings"
	"time"

	"data-collector/internal/models"
)

// StockValidator 股票数据验证器
type StockValidator struct {
	tsCodeRegex *regexp.Regexp
	symbolRegex *regexp.Regexp
}

// NewStockValidator 创建股票数据验证器
func NewStockValidator() *StockValidator {
	return &StockValidator{
		tsCodeRegex: regexp.MustCompile(`^\d{6}\.(SH|SZ)$`),
		symbolRegex: regexp.MustCompile(`^\d{6}$`),
	}
}

// ValidateStockBasic 验证股票基础信息
func (v *StockValidator) ValidateStockBasic(stock *models.StockBasic) error {
	if stock == nil {
		return fmt.Errorf("股票信息不能为空")
	}
	
	// 验证Tushare代码
	if err := v.ValidateTSCode(stock.TSCode); err != nil {
		return fmt.Errorf("Tushare代码验证失败: %w", err)
	}
	
	// 验证股票代码
	if err := v.ValidateSymbol(stock.Symbol); err != nil {
		return fmt.Errorf("股票代码验证失败: %w", err)
	}
	
	// 验证股票名称
	if err := v.ValidateName(stock.Name); err != nil {
		return fmt.Errorf("股票名称验证失败: %w", err)
	}
	
	// 验证市场类型
	if err := v.ValidateMarket(stock.Market); err != nil {
		return fmt.Errorf("市场类型验证失败: %w", err)
	}
	
	// 验证上市日期
	if err := v.ValidateListDate(stock.ListDate); err != nil {
		return fmt.Errorf("上市日期验证失败: %w", err)
	}
	
	// 验证沪深港通标识
	if err := v.ValidateIsHS(stock.IsHS); err != nil {
		return fmt.Errorf("沪深港通标识验证失败: %w", err)
	}
	
	return nil
}

// ValidateTSCode 验证Tushare代码
func (v *StockValidator) ValidateTSCode(tsCode string) error {
	if tsCode == "" {
		return fmt.Errorf("Tushare代码不能为空")
	}
	
	if !v.tsCodeRegex.MatchString(tsCode) {
		return fmt.Errorf("Tushare代码格式不正确，应为6位数字.SH或6位数字.SZ格式")
	}
	
	return nil
}

// ValidateSymbol 验证股票代码
func (v *StockValidator) ValidateSymbol(symbol string) error {
	if symbol == "" {
		return fmt.Errorf("股票代码不能为空")
	}
	
	if !v.symbolRegex.MatchString(symbol) {
		return fmt.Errorf("股票代码格式不正确，应为6位数字")
	}
	
	return nil
}

// ValidateName 验证股票名称
func (v *StockValidator) ValidateName(name string) error {
	if name == "" {
		return fmt.Errorf("股票名称不能为空")
	}
	
	name = strings.TrimSpace(name)
	if len(name) == 0 {
		return fmt.Errorf("股票名称不能为空")
	}
	
	if len(name) > 50 {
		return fmt.Errorf("股票名称长度不能超过50个字符")
	}
	
	return nil
}

// ValidateMarket 验证市场类型
func (v *StockValidator) ValidateMarket(market string) error {
	validMarkets := map[string]bool{
		"主板":   true,
		"中小板":  true,
		"创业板":  true,
		"科创板":  true,
		"北交所":  true,
		"主板A":  true,
		"主板B":  true,
		"CDR": true,
		"":     true, // 允许为空
	}
	
	if !validMarkets[market] {
		return fmt.Errorf("不支持的市场类型: %s", market)
	}
	
	return nil
}

// ValidateListDate 验证上市日期
func (v *StockValidator) ValidateListDate(listDate time.Time) error {
	// 检查是否为零值
	if listDate.IsZero() {
		return fmt.Errorf("上市日期不能为空")
	}
	
	// 检查日期是否在合理范围内
	minDate := time.Date(1990, 1, 1, 0, 0, 0, 0, time.UTC)
	maxDate := time.Now().AddDate(1, 0, 0) // 允许未来一年内的日期
	
	if listDate.Before(minDate) {
		return fmt.Errorf("上市日期不能早于1990年1月1日")
	}
	
	if listDate.After(maxDate) {
		return fmt.Errorf("上市日期不能晚于当前时间一年")
	}
	
	return nil
}

// ValidateIsHS 验证沪深港通标识
func (v *StockValidator) ValidateIsHS(isHS string) error {
	validValues := map[string]bool{
		"N": true, // 否
		"H": true, // 沪股通
		"S": true, // 深股通
		"":  true, // 允许为空
	}
	
	if !validValues[isHS] {
		return fmt.Errorf("沪深港通标识值无效: %s，有效值为: N, H, S", isHS)
	}
	
	return nil
}

// ValidateStockQuote 验证股票行情数据
func (v *StockValidator) ValidateStockQuote(quote *models.StockQuote) error {
	if quote == nil {
		return fmt.Errorf("股票行情数据不能为空")
	}
	
	// 验证股票代码
	if err := v.ValidateSymbol(quote.Symbol); err != nil {
		return fmt.Errorf("股票代码验证失败: %w", err)
	}
	
	// 验证交易日期
	if quote.TradeDate.IsZero() {
		return fmt.Errorf("交易日期不能为空")
	}
	
	// 验证价格数据（这里简单检查是否为空，实际应用中可能需要更复杂的验证）
	if quote.Open == "" || quote.High == "" || quote.Low == "" || quote.Close == "" {
		return fmt.Errorf("价格数据不能为空")
	}
	
	return nil
}

// ValidateAdjFactor 验证复权因子数据
func (v *StockValidator) ValidateAdjFactor(adjFactor *models.AdjFactor) error {
	if adjFactor == nil {
		return fmt.Errorf("复权因子数据不能为空")
	}
	
	// 验证Tushare代码
	if err := v.ValidateTSCode(adjFactor.TSCode); err != nil {
		return fmt.Errorf("Tushare代码验证失败: %w", err)
	}
	
	// 验证交易日期
	if adjFactor.TradeDate.IsZero() {
		return fmt.Errorf("交易日期不能为空")
	}
	
	// 验证复权因子
	if adjFactor.AdjFactor == "" {
		return fmt.Errorf("复权因子不能为空")
	}
	
	return nil
}

// BatchValidateStockBasic 批量验证股票基础信息
func (v *StockValidator) BatchValidateStockBasic(stocks []*models.StockBasic) []error {
	var errors []error
	
	for i, stock := range stocks {
		if err := v.ValidateStockBasic(stock); err != nil {
			errors = append(errors, fmt.Errorf("第%d条记录验证失败: %w", i+1, err))
		}
	}
	
	return errors
}

// BatchValidateStockQuote 批量验证股票行情数据
func (v *StockValidator) BatchValidateStockQuote(quotes []*models.StockQuote) []error {
	var errors []error
	
	for i, quote := range quotes {
		if err := v.ValidateStockQuote(quote); err != nil {
			errors = append(errors, fmt.Errorf("第%d条记录验证失败: %w", i+1, err))
		}
	}
	
	return errors
}

// BatchValidateAdjFactor 批量验证复权因子数据
func (v *StockValidator) BatchValidateAdjFactor(adjFactors []*models.AdjFactor) []error {
	var errors []error
	
	for i, adjFactor := range adjFactors {
		if err := v.ValidateAdjFactor(adjFactor); err != nil {
			errors = append(errors, fmt.Errorf("第%d条记录验证失败: %w", i+1, err))
		}
	}
	
	return errors
}