package market

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"
)

// SectorValidator 板块数据验证器
type SectorValidator struct {
	marketRepo storage.MarketRepository
	stockRepo  storage.StockRepository
}

// NewSectorValidator 创建板块数据验证器
func NewSectorValidator(marketRepo storage.MarketRepository, stockRepo storage.StockRepository) *SectorValidator {
	return &SectorValidator{
		marketRepo: marketRepo,
		stockRepo:  stockRepo,
	}
}

// ValidateSectorClassification 验证板块分类数据
func (v *SectorValidator) ValidateSectorClassification(ctx context.Context, sector *models.Sector) error {
	// 验证板块代码格式
	if err := v.validateSectorCode(sector.SectorCode); err != nil {
		return fmt.Errorf("板块代码验证失败: %w", err)
	}

	// 验证板块名称
	if err := v.validateSectorName(sector.SectorName); err != nil {
		return fmt.Errorf("板块名称验证失败: %w", err)
	}

	// 验证板块层级
	if err := v.validateSectorLevel(sector.Level); err != nil {
		return fmt.Errorf("板块层级验证失败: %w", err)
	}

	// 验证父级板块代码
	if err := v.validateParentCode(ctx, sector.SectorCode, sector.ParentCode, sector.Level); err != nil {
		return fmt.Errorf("父级板块代码验证失败: %w", err)
	}

	return nil
}

// ValidateSectorConstituent 验证板块成分股数据
func (v *SectorValidator) ValidateSectorConstituent(ctx context.Context, constituent *models.SectorConstituent) error {
	// 验证板块代码存在性
	if err := v.validateSectorExists(ctx, constituent.SectorCode); err != nil {
		return fmt.Errorf("板块代码验证失败: %w", err)
	}

	// 验证股票代码存在性
	if err := v.validateStockExists(ctx, constituent.StockCode); err != nil {
		return fmt.Errorf("股票代码验证失败: %w", err)
	}

	// 验证权重数据
	if err := v.validateWeight(constituent.Weight); err != nil {
		return fmt.Errorf("权重数据验证失败: %w", err)
	}

	// 验证日期数据
	if err := v.validateDates(constituent.InDate, constituent.OutDate); err != nil {
		return fmt.Errorf("日期数据验证失败: %w", err)
	}

	return nil
}

// ValidateSectorHierarchy 验证板块分类层级一致性
func (v *SectorValidator) ValidateSectorHierarchy(ctx context.Context) error {
	logger.Info("开始验证板块分类层级一致性")

	// 获取所有板块
	sectors, err := v.marketRepo.ListSectors(ctx, 10000, 0)
	if err != nil {
		return fmt.Errorf("获取板块列表失败: %w", err)
	}

	// 按层级分组
	levelMap := make(map[int][]*models.Sector)
	for _, sector := range sectors {
		levelMap[sector.Level] = append(levelMap[sector.Level], sector)
	}

	// 验证一级板块（无父级）
	for _, sector := range levelMap[1] {
		if sector.ParentCode != "" {
			return fmt.Errorf("一级板块 %s 不应有父级代码", sector.SectorCode)
		}
	}

	// 验证二级和三级板块（必须有父级）
	for level := 2; level <= 3; level++ {
		for _, sector := range levelMap[level] {
			if sector.ParentCode == "" {
				return fmt.Errorf("%d级板块 %s 必须有父级代码", level, sector.SectorCode)
			}

			// 验证父级板块存在且层级正确
			parent, err := v.marketRepo.GetSectorByCode(ctx, sector.ParentCode)
			if err != nil {
				return fmt.Errorf("板块 %s 的父级板块 %s 不存在", sector.SectorCode, sector.ParentCode)
			}

			if parent.Level != level-1 {
				return fmt.Errorf("板块 %s 的父级板块 %s 层级不正确，期望 %d，实际 %d", 
					sector.SectorCode, sector.ParentCode, level-1, parent.Level)
			}
		}
	}

	logger.Info("板块分类层级一致性验证通过")
	return nil
}

// ValidateConstituentAccuracy 验证成分股归属准确性
func (v *SectorValidator) ValidateConstituentAccuracy(ctx context.Context, sectorCode string) error {
	logger.Info(fmt.Sprintf("开始验证板块 %s 的成分股归属准确性", sectorCode))

	// 获取板块成分股
	constituents, err := v.marketRepo.GetSectorConstituents(ctx, sectorCode)
	if err != nil {
		return fmt.Errorf("获取板块成分股失败: %w", err)
	}

	// 验证权重总和
	totalWeight := 0.0
	for _, constituent := range constituents {
		if !constituent.IsActive {
			continue
		}

		weight, err := strconv.ParseFloat(constituent.Weight, 64)
		if err != nil {
			logger.Warn(fmt.Sprintf("解析权重失败: %s", constituent.Weight))
			continue
		}
		totalWeight += weight
	}

	// 权重总和应该接近100%（允许5%的误差）
	if totalWeight < 95.0 || totalWeight > 105.0 {
		logger.Warn(fmt.Sprintf("板块 %s 权重总和异常: %.2f%%", sectorCode, totalWeight))
	}

	// 验证成分股数量合理性
	if len(constituents) == 0 {
		return fmt.Errorf("板块 %s 没有成分股", sectorCode)
	}

	if len(constituents) > 1000 {
		logger.Warn(fmt.Sprintf("板块 %s 成分股数量过多: %d", sectorCode, len(constituents)))
	}

	logger.Info(fmt.Sprintf("板块 %s 成分股归属准确性验证通过，成分股数量: %d，权重总和: %.2f%%", 
		sectorCode, len(constituents), totalWeight))
	return nil
}

// ValidateWeightConsistency 验证板块权重数据合理性
func (v *SectorValidator) ValidateWeightConsistency(ctx context.Context) error {
	logger.Info("开始验证板块权重数据合理性")

	// 获取所有板块
	sectors, err := v.marketRepo.ListSectors(ctx, 1000, 0)
	if err != nil {
		return fmt.Errorf("获取板块列表失败: %w", err)
	}

	errorCount := 0
	for _, sector := range sectors {
		if !sector.IsActive {
			continue
		}

		err := v.ValidateConstituentAccuracy(ctx, sector.SectorCode)
		if err != nil {
			logger.Error(fmt.Sprintf("板块 %s 权重验证失败: %v", sector.SectorCode, err))
			errorCount++
		}
	}

	if errorCount > 0 {
		logger.Warn(fmt.Sprintf("权重数据验证完成，发现 %d 个异常板块", errorCount))
	} else {
		logger.Info("板块权重数据合理性验证通过")
	}

	return nil
}

// validateSectorCode 验证板块代码格式
func (v *SectorValidator) validateSectorCode(sectorCode string) error {
	if sectorCode == "" {
		return fmt.Errorf("板块代码不能为空")
	}

	if len(sectorCode) < 6 || len(sectorCode) > 12 {
		return fmt.Errorf("板块代码长度应在6-12位之间")
	}

	// 申万行业代码格式验证
	if strings.HasPrefix(sectorCode, "801") {
		// 申万一级行业：801010.SI
		// 申万二级行业：801011.SI
		// 申万三级行业：801012.SI
		if !strings.HasSuffix(sectorCode, ".SI") {
			return fmt.Errorf("申万行业代码格式错误，应以.SI结尾")
		}
	}

	return nil
}

// validateSectorName 验证板块名称
func (v *SectorValidator) validateSectorName(sectorName string) error {
	if sectorName == "" {
		return fmt.Errorf("板块名称不能为空")
	}

	if len(sectorName) > 50 {
		return fmt.Errorf("板块名称长度不能超过50个字符")
	}

	return nil
}

// validateSectorLevel 验证板块层级
func (v *SectorValidator) validateSectorLevel(level int) error {
	if level < 1 || level > 3 {
		return fmt.Errorf("板块层级必须在1-3之间")
	}
	return nil
}

// validateParentCode 验证父级板块代码
func (v *SectorValidator) validateParentCode(ctx context.Context, sectorCode, parentCode string, level int) error {
	// 一级板块不应有父级
	if level == 1 {
		if parentCode != "" {
			return fmt.Errorf("一级板块不应有父级代码")
		}
		return nil
	}

	// 二级和三级板块必须有父级
	if parentCode == "" {
		return fmt.Errorf("%d级板块必须有父级代码", level)
	}

	// 不能自己是自己的父级
	if parentCode == sectorCode {
		return fmt.Errorf("板块不能是自己的父级")
	}

	return nil
}

// validateSectorExists 验证板块代码存在性
func (v *SectorValidator) validateSectorExists(ctx context.Context, sectorCode string) error {
	_, err := v.marketRepo.GetSectorByCode(ctx, sectorCode)
	if err != nil {
		return fmt.Errorf("板块代码 %s 不存在", sectorCode)
	}
	return nil
}

// validateStockExists 验证股票代码存在性
func (v *SectorValidator) validateStockExists(ctx context.Context, stockCode string) error {
	_, err := v.stockRepo.GetStockByTSCode(ctx, stockCode)
	if err != nil {
		return fmt.Errorf("股票代码 %s 不存在", stockCode)
	}
	return nil
}

// validateWeight 验证权重数据
func (v *SectorValidator) validateWeight(weight string) error {
	if weight == "" {
		return nil // 权重可以为空
	}

	weightVal, err := strconv.ParseFloat(weight, 64)
	if err != nil {
		return fmt.Errorf("权重格式错误: %s", weight)
	}

	if weightVal < 0 || weightVal > 100 {
		return fmt.Errorf("权重值应在0-100之间: %.2f", weightVal)
	}

	return nil
}

// validateDates 验证日期数据
func (v *SectorValidator) validateDates(inDate time.Time, outDate *time.Time) error {
	// 纳入日期不能为零值
	if inDate.IsZero() {
		return fmt.Errorf("纳入日期不能为空")
	}

	// 纳入日期不能是未来日期
	if inDate.After(time.Now()) {
		return fmt.Errorf("纳入日期不能是未来日期")
	}

	// 如果有剔除日期，剔除日期必须晚于纳入日期
	if outDate != nil && !outDate.IsZero() {
		if outDate.Before(inDate) {
			return fmt.Errorf("剔除日期不能早于纳入日期")
		}
	}

	return nil
}

// GetValidatorInfo 获取验证器信息
func (v *SectorValidator) GetValidatorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "SectorValidator",
		"description": "板块数据验证器",
		"version":     "1.0.0",
		"validations": []string{
			"板块分类层级一致性验证",
			"成分股归属准确性验证",
			"板块权重数据合理性检查",
			"板块代码格式验证",
			"日期数据有效性验证",
		},
	}
}