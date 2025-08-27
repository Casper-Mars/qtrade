package market

import (
	"fmt"
	"math"
	"strconv"
	"time"

	"data-collector/internal/models"
	"data-collector/pkg/logger"
)

// IndustryIndexValidator 行业指数数据验证器
type IndustryIndexValidator struct{}

// NewIndustryIndexValidator 创建行业指数数据验证器
func NewIndustryIndexValidator() *IndustryIndexValidator {
	return &IndustryIndexValidator{}
}

// ValidateIndustryIndex 验证行业指数数据
func (v *IndustryIndexValidator) ValidateIndustryIndex(index *models.IndustryIndex) error {
	if index == nil {
		return fmt.Errorf("行业指数数据不能为空")
	}

	// 验证行业指数代码
	if index.IndexCode == "" {
		return fmt.Errorf("行业指数代码不能为空")
	}

	// 验证行业指数名称
	if index.IndexName == "" {
		return fmt.Errorf("行业指数名称不能为空")
	}

	// 验证行业级别
	if index.IndustryLevel == "" {
		return fmt.Errorf("行业级别不能为空")
	}

	// 验证行业级别格式（一级/二级/三级）
	if index.IndustryLevel != "一级" && index.IndustryLevel != "二级" && index.IndustryLevel != "三级" {
		return fmt.Errorf("行业级别格式错误，应为一级/二级/三级")
	}

	// 验证交易日期
	if index.TradeDate.IsZero() {
		return fmt.Errorf("交易日期不能为空")
	}

	// 验证交易日期不能晚于当前时间
	if index.TradeDate.After(time.Now()) {
		return fmt.Errorf("交易日期不能晚于当前时间")
	}

	// 验证价格数据
	if err := v.validateIndustryPriceData(index); err != nil {
		return fmt.Errorf("价格数据验证失败: %w", err)
	}

	// 验证涨跌幅计算
	if err := v.validateIndustryPctChange(index); err != nil {
		return fmt.Errorf("涨跌幅验证失败: %w", err)
	}

	return nil
}

// validateIndustryPriceData 验证行业指数价格数据合理性
func (v *IndustryIndexValidator) validateIndustryPriceData(index *models.IndustryIndex) error {
	// 解析价格数据
	open, err := v.parseFloat(index.Open, "开盘价")
	if err != nil {
		return err
	}

	high, err := v.parseFloat(index.High, "最高价")
	if err != nil {
		return err
	}

	low, err := v.parseFloat(index.Low, "最低价")
	if err != nil {
		return err
	}

	close, err := v.parseFloat(index.Close, "收盘价")
	if err != nil {
		return err
	}

	preClose, err := v.parseFloat(index.PreClose, "前收盘价")
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

	// 验证价格波动合理性（行业指数单日涨跌幅不超过30%）
	changeRate := math.Abs((close - preClose) / preClose)
	if changeRate > 0.3 {
		logger.Warn(fmt.Sprintf("行业指数 %s 在 %s 的涨跌幅异常: %.2f%%", 
			index.IndexCode, index.TradeDate.Format("2006-01-02"), changeRate*100))
	}

	return nil
}

// validateIndustryPctChange 验证行业指数涨跌幅计算
func (v *IndustryIndexValidator) validateIndustryPctChange(index *models.IndustryIndex) error {
	if index.PctChg == "" || index.ChangeAmount == "" || index.PreClose == "" || index.Close == "" {
		return nil // 如果数据不完整，跳过验证
	}

	// 解析数据
	pctChg, err := strconv.ParseFloat(index.PctChg, 64)
	if err != nil {
		return fmt.Errorf("涨跌幅格式错误: %v", err)
	}

	changeAmount, err := strconv.ParseFloat(index.ChangeAmount, 64)
	if err != nil {
		return fmt.Errorf("涨跌额格式错误: %v", err)
	}

	preClose, err := strconv.ParseFloat(index.PreClose, 64)
	if err != nil {
		return fmt.Errorf("前收盘价格式错误: %v", err)
	}

	close, err := strconv.ParseFloat(index.Close, 64)
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

// ValidateIndustryClassification 验证行业分类一致性
func (v *IndustryIndexValidator) ValidateIndustryClassification(indices []*models.IndustryIndex) error {
	if len(indices) == 0 {
		return nil
	}

	// 按行业级别分组验证
	levelGroups := make(map[string][]*models.IndustryIndex)
	for _, index := range indices {
		levelGroups[index.IndustryLevel] = append(levelGroups[index.IndustryLevel], index)
	}

	// 验证父子级关系
	for level, levelIndices := range levelGroups {
		if level == "一级" {
			// 一级行业不应该有父级代码
			for _, index := range levelIndices {
				if index.ParentCode != "" {
					return fmt.Errorf("一级行业指数 %s 不应该有父级代码", index.IndexCode)
				}
			}
		} else {
			// 二级、三级行业应该有父级代码
			for _, index := range levelIndices {
				if index.ParentCode == "" {
					return fmt.Errorf("%s行业指数 %s 应该有父级代码", level, index.IndexCode)
				}
			}
		}
	}

	return nil
}

// ValidateTimeSeriesContinuity 验证行业指数时间序列完整性
func (v *IndustryIndexValidator) ValidateTimeSeriesContinuity(indices []*models.IndustryIndex) error {
	if len(indices) <= 1 {
		return nil // 数据量不足，跳过验证
	}

	// 按指数代码分组
	indexGroups := make(map[string][]*models.IndustryIndex)
	for _, index := range indices {
		indexGroups[index.IndexCode] = append(indexGroups[index.IndexCode], index)
	}

	// 验证每个指数的时间序列连续性
	for indexCode, indexData := range indexGroups {
		if len(indexData) <= 1 {
			continue
		}

		// 按交易日期排序（假设已排序）
		for i := 1; i < len(indexData); i++ {
			prev := indexData[i-1]
			curr := indexData[i]

			// 验证日期顺序
			if curr.TradeDate.Before(prev.TradeDate) {
				return fmt.Errorf("行业指数 %s 交易日期顺序错误: %s 应该在 %s 之前", 
					indexCode, curr.TradeDate.Format("2006-01-02"), prev.TradeDate.Format("2006-01-02"))
			}

			// 验证前收盘价连续性
			if prev.Close != "" && curr.PreClose != "" {
				prevClose, err1 := strconv.ParseFloat(prev.Close, 64)
				currPreClose, err2 := strconv.ParseFloat(curr.PreClose, 64)
				if err1 == nil && err2 == nil {
					if math.Abs(prevClose-currPreClose) > 0.01 {
						logger.Warn(fmt.Sprintf("行业指数 %s 在 %s 的前收盘价连续性异常: 前一日收盘 %.2f, 当日前收盘 %.2f",
							indexCode, curr.TradeDate.Format("2006-01-02"), prevClose, currPreClose))
					}
				}
			}
		}
	}

	return nil
}

// BatchValidateIndustryIndices 批量验证行业指数数据
func (v *IndustryIndexValidator) BatchValidateIndustryIndices(indices []*models.IndustryIndex) []error {
	var errors []error

	// 逐个验证
	for i, index := range indices {
		if err := v.ValidateIndustryIndex(index); err != nil {
			errors = append(errors, fmt.Errorf("第 %d 条数据验证失败: %w", i+1, err))
		}
	}

	// 验证行业分类一致性
	if err := v.ValidateIndustryClassification(indices); err != nil {
		errors = append(errors, fmt.Errorf("行业分类一致性验证失败: %w", err))
	}

	// 验证时间序列完整性
	if err := v.ValidateTimeSeriesContinuity(indices); err != nil {
		errors = append(errors, fmt.Errorf("时间序列完整性验证失败: %w", err))
	}

	return errors
}

// ValidateIndustryIndexPointReasonableness 验证行业指数点位合理性
func (v *IndustryIndexValidator) ValidateIndustryIndexPointReasonableness(indices []*models.IndustryIndex) error {
	if len(indices) == 0 {
		return nil
	}

	// 按指数代码分组
	indexGroups := make(map[string][]*models.IndustryIndex)
	for _, index := range indices {
		indexGroups[index.IndexCode] = append(indexGroups[index.IndexCode], index)
	}

	// 验证每个指数的点位合理性
	for indexCode, indexData := range indexGroups {
		if len(indexData) == 0 {
			continue
		}

		// 计算价格统计信息
		var prices []float64
		for _, index := range indexData {
			if close, err := strconv.ParseFloat(index.Close, 64); err == nil {
				prices = append(prices, close)
			}
		}

		if len(prices) == 0 {
			continue
		}

		// 计算均值和标准差
		var sum float64
		for _, price := range prices {
			sum += price
		}
		mean := sum / float64(len(prices))

		var variance float64
		for _, price := range prices {
			variance += math.Pow(price-mean, 2)
		}
		stdDev := math.Sqrt(variance / float64(len(prices)))

		// 检查异常值（超过3个标准差的点位）
		for _, index := range indexData {
			if close, err := strconv.ParseFloat(index.Close, 64); err == nil {
				if math.Abs(close-mean) > 3*stdDev {
					logger.Warn(fmt.Sprintf("行业指数 %s 在 %s 的收盘价异常: %.2f (均值: %.2f, 标准差: %.2f)",
						indexCode, index.TradeDate.Format("2006-01-02"), close, mean, stdDev))
				}
			}
		}
	}

	return nil
}

// parseFloat 解析浮点数
func (v *IndustryIndexValidator) parseFloat(value, fieldName string) (float64, error) {
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
func (v *IndustryIndexValidator) GetValidatorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "IndustryIndexValidator",
		"description": "行业指数数据验证器",
		"version":     "1.0.0",
		"validations": []string{
			"行业指数基础信息验证",
			"行业指数价格数据合理性验证",
			"行业指数涨跌幅计算验证",
			"行业分类一致性检查",
			"时间序列完整性验证",
			"行业指数点位合理性验证",
		},
	}
}