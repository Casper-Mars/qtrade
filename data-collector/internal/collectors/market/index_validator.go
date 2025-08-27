package market

import (
	"fmt"
	"math"
	"strconv"
	"time"

	"data-collector/internal/models"
	"data-collector/pkg/logger"
)

// IndexValidator 指数数据验证器
type IndexValidator struct{}

// NewIndexValidator 创建指数数据验证器
func NewIndexValidator() *IndexValidator {
	return &IndexValidator{}
}

// ValidateIndexBasic 验证指数基础信息
func (v *IndexValidator) ValidateIndexBasic(index *models.IndexBasic) error {
	if index == nil {
		return fmt.Errorf("指数基础信息不能为空")
	}

	// 验证指数代码
	if index.IndexCode == "" {
		return fmt.Errorf("指数代码不能为空")
	}

	// 验证指数名称
	if index.IndexName == "" {
		return fmt.Errorf("指数名称不能为空")
	}

	// 验证市场
	if index.Market == "" {
		return fmt.Errorf("市场信息不能为空")
	}

	// 验证基准日期
	if !index.BaseDate.IsZero() && index.BaseDate.After(time.Now()) {
		return fmt.Errorf("基准日期不能晚于当前时间")
	}

	// 验证上市日期
	if !index.ListDate.IsZero() && index.ListDate.After(time.Now()) {
		return fmt.Errorf("上市日期不能晚于当前时间")
	}

	// 验证基准点位
	if index.BasePoint != "" {
		if basePoint, err := strconv.ParseFloat(index.BasePoint, 64); err != nil {
			return fmt.Errorf("基准点位格式错误: %v", err)
		} else if basePoint <= 0 {
			return fmt.Errorf("基准点位必须大于0")
		}
	}

	return nil
}

// ValidateIndexQuote 验证指数行情数据
func (v *IndexValidator) ValidateIndexQuote(quote *models.IndexQuote) error {
	if quote == nil {
		return fmt.Errorf("指数行情数据不能为空")
	}

	// 验证指数代码
	if quote.IndexCode == "" {
		return fmt.Errorf("指数代码不能为空")
	}

	// 验证交易日期
	if quote.TradeDate.IsZero() {
		return fmt.Errorf("交易日期不能为空")
	}

	// 验证交易日期不能晚于当前时间
	if quote.TradeDate.After(time.Now()) {
		return fmt.Errorf("交易日期不能晚于当前时间")
	}

	// 验证价格数据
	if err := v.validatePriceData(quote); err != nil {
		return fmt.Errorf("价格数据验证失败: %w", err)
	}

	// 验证涨跌幅计算
	if err := v.validatePctChange(quote); err != nil {
		return fmt.Errorf("涨跌幅验证失败: %w", err)
	}

	// 验证成交量数据
	if err := v.validateVolumeData(quote); err != nil {
		return fmt.Errorf("成交量数据验证失败: %w", err)
	}

	return nil
}

// validatePriceData 验证价格数据合理性
func (v *IndexValidator) validatePriceData(quote *models.IndexQuote) error {
	// 解析价格数据
	open, err := v.parseFloat(quote.Open, "开盘价")
	if err != nil {
		return err
	}

	high, err := v.parseFloat(quote.High, "最高价")
	if err != nil {
		return err
	}

	low, err := v.parseFloat(quote.Low, "最低价")
	if err != nil {
		return err
	}

	close, err := v.parseFloat(quote.Close, "收盘价")
	if err != nil {
		return err
	}

	preClose, err := v.parseFloat(quote.PreClose, "前收盘价")
	if err != nil {
		return err
	}

	// 验证价格必须大于0
	if open <= 0 || high <= 0 || low <= 0 || close <= 0 || preClose <= 0 {
		return fmt.Errorf("价格数据必须大于0")
	}

	// 验证最高价 >= 最低价
	if high < low {
		return fmt.Errorf("最高价不能小于最低价")
	}

	// 验证开盘价在最高价和最低价之间
	if open > high || open < low {
		return fmt.Errorf("开盘价必须在最高价和最低价之间")
	}

	// 验证收盘价在最高价和最低价之间
	if close > high || close < low {
		return fmt.Errorf("收盘价必须在最高价和最低价之间")
	}

	// 验证价格波动合理性（单日涨跌幅不超过50%，这对指数来说是极端情况）
	changeRate := math.Abs((close - preClose) / preClose)
	if changeRate > 0.5 {
		logger.Warn(fmt.Sprintf("指数 %s 在 %s 的涨跌幅异常: %.2f%%", 
			quote.IndexCode, quote.TradeDate.Format("2006-01-02"), changeRate*100))
	}

	return nil
}

// validatePctChange 验证涨跌幅计算
func (v *IndexValidator) validatePctChange(quote *models.IndexQuote) error {
	if quote.PctChg == "" || quote.ChangeAmount == "" || quote.PreClose == "" || quote.Close == "" {
		return nil // 如果数据不完整，跳过验证
	}

	// 解析数据
	pctChg, err := strconv.ParseFloat(quote.PctChg, 64)
	if err != nil {
		return fmt.Errorf("涨跌幅格式错误: %v", err)
	}

	changeAmount, err := strconv.ParseFloat(quote.ChangeAmount, 64)
	if err != nil {
		return fmt.Errorf("涨跌额格式错误: %v", err)
	}

	preClose, err := strconv.ParseFloat(quote.PreClose, 64)
	if err != nil {
		return fmt.Errorf("前收盘价格式错误: %v", err)
	}

	close, err := strconv.ParseFloat(quote.Close, 64)
	if err != nil {
		return fmt.Errorf("收盘价格式错误: %v", err)
	}

	// 验证涨跌额计算
	expectedChangeAmount := close - preClose
	if math.Abs(changeAmount-expectedChangeAmount) > 0.01 {
		return fmt.Errorf("涨跌额计算错误: 期望 %.2f, 实际 %.2f", expectedChangeAmount, changeAmount)
	}

	// 验证涨跌幅计算
	expectedPctChg := (close - preClose) / preClose * 100
	if math.Abs(pctChg-expectedPctChg) > 0.01 {
		return fmt.Errorf("涨跌幅计算错误: 期望 %.2f%%, 实际 %.2f%%", expectedPctChg, pctChg)
	}

	return nil
}

// validateVolumeData 验证成交量数据
func (v *IndexValidator) validateVolumeData(quote *models.IndexQuote) error {
	if quote.Vol == "" && quote.Amount == "" {
		return nil // 如果没有成交量数据，跳过验证
	}

	// 验证成交量
	if quote.Vol != "" {
		vol, err := strconv.ParseFloat(quote.Vol, 64)
		if err != nil {
			return fmt.Errorf("成交量格式错误: %v", err)
		}
		if vol < 0 {
			return fmt.Errorf("成交量不能为负数")
		}
	}

	// 验证成交额
	if quote.Amount != "" {
		amount, err := strconv.ParseFloat(quote.Amount, 64)
		if err != nil {
			return fmt.Errorf("成交额格式错误: %v", err)
		}
		if amount < 0 {
			return fmt.Errorf("成交额不能为负数")
		}
	}

	return nil
}

// ValidateTimeSeriesContinuity 验证时间序列连续性
func (v *IndexValidator) ValidateTimeSeriesContinuity(quotes []*models.IndexQuote) error {
	if len(quotes) <= 1 {
		return nil // 数据量不足，跳过验证
	}

	// 按交易日期排序（假设已排序）
	for i := 1; i < len(quotes); i++ {
		prev := quotes[i-1]
		curr := quotes[i]

		// 验证日期顺序
		if curr.TradeDate.Before(prev.TradeDate) {
			return fmt.Errorf("交易日期顺序错误: %s 应该在 %s 之前", 
				curr.TradeDate.Format("2006-01-02"), prev.TradeDate.Format("2006-01-02"))
		}

		// 验证前收盘价连续性（当前交易日的前收盘价应该等于前一交易日的收盘价）
		if prev.Close != "" && curr.PreClose != "" {
			prevClose, err1 := strconv.ParseFloat(prev.Close, 64)
			currPreClose, err2 := strconv.ParseFloat(curr.PreClose, 64)
			if err1 == nil && err2 == nil {
				if math.Abs(prevClose-currPreClose) > 0.01 {
					logger.Warn(fmt.Sprintf("指数 %s 在 %s 的前收盘价连续性异常: 前一日收盘 %.2f, 当日前收盘 %.2f",
						curr.IndexCode, curr.TradeDate.Format("2006-01-02"), prevClose, currPreClose))
				}
			}
		}
	}

	return nil
}

// BatchValidateIndexQuotes 批量验证指数行情数据
func (v *IndexValidator) BatchValidateIndexQuotes(quotes []*models.IndexQuote) []error {
	var errors []error

	// 逐个验证
	for i, quote := range quotes {
		if err := v.ValidateIndexQuote(quote); err != nil {
			errors = append(errors, fmt.Errorf("第 %d 条数据验证失败: %w", i+1, err))
		}
	}

	// 验证时间序列连续性
	if err := v.ValidateTimeSeriesContinuity(quotes); err != nil {
		errors = append(errors, fmt.Errorf("时间序列连续性验证失败: %w", err))
	}

	return errors
}

// parseFloat 解析浮点数
func (v *IndexValidator) parseFloat(value, fieldName string) (float64, error) {
	if value == "" {
		return 0, fmt.Errorf("%s不能为空", fieldName)
	}

	result, err := strconv.ParseFloat(value, 64)
	if err != nil {
		return 0, fmt.Errorf("%s格式错误: %v", fieldName, err)
	}

	return result, nil
}

// GetValidatorInfo 获取验证器信息
func (v *IndexValidator) GetValidatorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "IndexValidator",
		"description": "指数数据验证器",
		"version":     "1.0.0",
		"validations": []string{
			"基础信息完整性验证",
			"价格数据合理性验证",
			"涨跌幅计算验证",
			"成交量一致性验证",
			"时间序列连续性验证",
		},
	}
}