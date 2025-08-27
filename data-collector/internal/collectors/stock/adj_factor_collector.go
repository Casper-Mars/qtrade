package stock

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// AdjFactorCollector 复权因子采集器
type AdjFactorCollector struct {
	tushareClient TushareClientInterface
	stockRepo     storage.StockRepository
}

// NewAdjFactorCollector 创建复权因子采集器
func NewAdjFactorCollector(tushareClient TushareClientInterface, stockRepo storage.StockRepository) *AdjFactorCollector {
	return &AdjFactorCollector{
		tushareClient: tushareClient,
		stockRepo:     stockRepo,
	}
}

// collectAllAdjFactorsByDate 批量采集指定日期所有股票的复权因子数据
func (c *AdjFactorCollector) collectAllAdjFactorsByDate(ctx context.Context, date time.Time) error {
	logger.Infof("开始批量采集 %s 所有股票的复权因子数据", date.Format("2006-01-02"))

	// 调用Tushare API获取指定日期所有股票的复权因子
	params := map[string]interface{}{
		"trade_date": date.Format("20060102"),
		// ts_code为空时，获取该日期所有股票的复权因子
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "adj_factor", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	// 解析响应数据
	adjFactors, err := c.parseAdjFactorData(resp)
	if err != nil {
		return fmt.Errorf("解析复权因子数据失败: %w", err)
	}

	if len(adjFactors) == 0 {
		logger.Warnf("日期 %s 没有复权因子数据", date.Format("2006-01-02"))
		return nil
	}

	// 数据验证
	validAdjFactors := make([]*models.AdjFactor, 0, len(adjFactors))
	for _, adjFactor := range adjFactors {
		if c.isValidAdjFactor(adjFactor) {
			validAdjFactors = append(validAdjFactors, adjFactor)
		} else {
			logger.Warnf("复权因子数据验证失败，跳过: %+v", adjFactor)
		}
	}

	if len(validAdjFactors) == 0 {
		logger.Warnf("日期 %s 没有有效的复权因子数据", date.Format("2006-01-02"))
		return nil
	}

	// 批量保存到数据库
	if err := c.stockRepo.BatchCreateAdjFactors(ctx, validAdjFactors); err != nil {
		return fmt.Errorf("保存复权因子数据失败: %w", err)
	}

	logger.Infof("成功批量采集 %s 的复权因子数据，共 %d 条记录", date.Format("2006-01-02"), len(validAdjFactors))
	return nil
}

// collectAdjFactorsByBatch 批量采集指定股票列表的复权因子数据
func (c *AdjFactorCollector) collectAdjFactorsByBatch(ctx context.Context, date time.Time, symbols []string) error {
	logger.Infof("开始批量采集 %s 指定股票的复权因子数据，股票数量: %d", date.Format("2006-01-02"), len(symbols))

	// 分批处理，每批最多50只股票（避免URL过长）
	batchSize := 50
	var totalCount int

	for i := 0; i < len(symbols); i += batchSize {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		end := i + batchSize
		if end > len(symbols) {
			end = len(symbols)
		}

		batchSymbols := symbols[i:end]
		if err := c.collectBatchAdjFactors(ctx, date, batchSymbols); err != nil {
			logger.Errorf("批量采集股票复权因子失败: %v, 股票: %v", err, batchSymbols)
			// 如果批量失败，回退到逐个采集
			for _, symbol := range batchSymbols {
				if err := c.CollectBySymbol(ctx, symbol, date, date); err != nil {
					logger.Errorf("采集股票 %s 的复权因子数据失败: %v", symbol, err)
					continue
				}
				totalCount++
				time.Sleep(100 * time.Millisecond)
			}
		} else {
			totalCount += len(batchSymbols)
		}

		// 添加延迟，避免API限流
		time.Sleep(200 * time.Millisecond)
	}

	logger.Infof("完成 %s 指定股票的复权因子数据采集，成功处理 %d/%d 只股票",
		date.Format("2006-01-02"), totalCount, len(symbols))
	return nil
}

// collectBatchAdjFactors 批量采集指定日期股票的复权因子
func (c *AdjFactorCollector) collectBatchAdjFactors(ctx context.Context, date time.Time, symbols []string) error {
	// 构建API参数
	params := map[string]interface{}{
		"trade_date": date.Format("20060102"),
	}

	// 如果指定了股票列表，则传递ts_code参数；否则获取全部股票
	if len(symbols) > 0 {
		params["ts_code"] = strings.Join(symbols, ",")
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "adj_factor", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	// 解析响应数据
	adjFactors, err := c.parseAdjFactorData(resp)
	if err != nil {
		return fmt.Errorf("解析复权因子数据失败: %w", err)
	}

	if len(adjFactors) == 0 {
		if len(symbols) == 0 {
			logger.Warnf("日期 %s 没有复权因子数据", date.Format("2006-01-02"))
		} else {
			logger.Warnf("股票 %v 在日期 %s 没有复权因子数据", symbols, date.Format("2006-01-02"))
		}
		return nil
	}

	// 数据验证
	validAdjFactors := make([]*models.AdjFactor, 0, len(adjFactors))
	for _, adjFactor := range adjFactors {
		if c.isValidAdjFactor(adjFactor) {
			validAdjFactors = append(validAdjFactors, adjFactor)
		} else {
			logger.Warnf("复权因子数据验证失败，跳过: %+v", adjFactor)
		}
	}

	if len(validAdjFactors) == 0 {
		if len(symbols) == 0 {
			logger.Warnf("日期 %s 没有有效的复权因子数据", date.Format("2006-01-02"))
		} else {
			logger.Warnf("股票 %v 在日期 %s 没有有效的复权因子数据", symbols, date.Format("2006-01-02"))
		}
		return nil
	}

	// 批量保存到数据库
	if err := c.stockRepo.BatchCreateAdjFactors(ctx, validAdjFactors); err != nil {
		return fmt.Errorf("保存复权因子数据失败: %w", err)
	}

	if len(symbols) == 0 {
		logger.Infof("成功批量采集 %s 全部股票的复权因子数据，共 %d 条记录", date.Format("2006-01-02"), len(validAdjFactors))
	} else {
		logger.Infof("成功批量采集股票 %v 在 %s 的复权因子数据，共 %d 条记录", symbols, date.Format("2006-01-02"), len(validAdjFactors))
	}
	return nil
}

// CollectBySymbol 采集指定股票的复权因子数据
func (c *AdjFactorCollector) CollectBySymbol(ctx context.Context, symbol string, startDate, endDate time.Time) error {
	logger.Infof("开始采集股票 %s 的复权因子数据，时间范围: %s 到 %s",
		symbol, startDate.Format("20060102"), endDate.Format("20060102"))

	// 构建请求参数
	params := map[string]interface{}{
		"ts_code":    symbol,
		"trade_date": "", // 空表示查询时间范围内的所有数据
		"start_date": startDate.Format("20060102"),
		"end_date":   endDate.Format("20060102"),
	}

	// 调用Tushare API
	resp, err := c.tushareClient.Call(ctx, "adj_factor", params, "")
	if err != nil {
		return fmt.Errorf("调用Tushare API失败: %w", err)
	}

	// 解析响应数据
	adjFactors, err := c.parseAdjFactorData(resp)
	if err != nil {
		return fmt.Errorf("解析复权因子数据失败: %w", err)
	}

	if len(adjFactors) == 0 {
		logger.Warnf("股票 %s 在指定时间范围内没有复权因子数据", symbol)
		return nil
	}

	// 数据验证
	validAdjFactors := make([]*models.AdjFactor, 0, len(adjFactors))
	for _, adjFactor := range adjFactors {
		if c.isValidAdjFactor(adjFactor) {
			validAdjFactors = append(validAdjFactors, adjFactor)
		} else {
			logger.Warnf("复权因子数据验证失败，跳过: %+v", adjFactor)
		}
	}

	if len(validAdjFactors) == 0 {
		logger.Warnf("股票 %s 没有有效的复权因子数据", symbol)
		return nil
	}

	// 批量保存到数据库
	if err := c.stockRepo.BatchCreateAdjFactors(ctx, validAdjFactors); err != nil {
		return fmt.Errorf("保存复权因子数据失败: %w", err)
	}

	logger.Infof("成功采集并保存股票 %s 的复权因子数据，共 %d 条", symbol, len(validAdjFactors))
	return nil
}

// CollectByDate 采集指定日期的复权因子数据
func (c *AdjFactorCollector) CollectByDate(ctx context.Context, date time.Time, symbols []string) error {
	logger.Infof("开始采集 %s 的复权因子数据，股票数量: %d", date.Format("2006-01-02"), len(symbols))

	// 如果没有指定股票代码，使用批量采集获取所有股票的复权因子
	if len(symbols) == 0 {
		return c.collectAllAdjFactorsByDate(ctx, date)
	}

	// 如果指定了股票代码，按批次采集
	return c.collectAdjFactorsByBatch(ctx, date, symbols)
}

// CollectByDateRange 采集指定时间范围的复权因子数据
func (c *AdjFactorCollector) CollectByDateRange(ctx context.Context, startDate, endDate time.Time, symbols []string) error {
	logger.Infof("开始采集 %s 到 %s 的复权因子数据，股票数量: %d",
		startDate.Format("2006-01-02"), endDate.Format("2006-01-02"), len(symbols))

	// 如果没有指定股票代码，使用批量采集
	if len(symbols) == 0 {
		// 按日期逐日采集所有股票的复权因子
		currentDate := startDate
		for !currentDate.After(endDate) {
			select {
			case <-ctx.Done():
				return ctx.Err()
			default:
			}

			if err := c.collectAllAdjFactorsByDate(ctx, currentDate); err != nil {
				logger.Errorf("采集 %s 的复权因子数据失败: %v", currentDate.Format("2006-01-02"), err)
			}

			// 移动到下一个交易日
			currentDate = currentDate.AddDate(0, 0, 1)
			// 添加延迟，避免API限流
			time.Sleep(200 * time.Millisecond)
		}
		return nil
	}

	// 如果指定了股票代码，按股票逐个采集时间范围数据
	var totalCount int
	for _, symbol := range symbols {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		if err := c.CollectBySymbol(ctx, symbol, startDate, endDate); err != nil {
			logger.Errorf("采集股票 %s 的复权因子数据失败: %v", symbol, err)
			continue
		}
		totalCount++

		// 添加延迟，避免API限流
		time.Sleep(100 * time.Millisecond)
	}

	logger.Infof("完成 %s 到 %s 的复权因子数据采集，成功处理 %d/%d 只股票",
		startDate.Format("2006-01-02"), endDate.Format("2006-01-02"), totalCount, len(symbols))
	return nil
}

// CollectLatest 采集最新的复权因子数据
func (c *AdjFactorCollector) CollectLatest(ctx context.Context, symbols []string) error {
	logger.Info("开始采集最新的复权因子数据")

	// 获取最新交易日期
	latestDate, err := c.getLatestTradeDate(ctx)
	if err != nil {
		return fmt.Errorf("获取最新交易日期失败: %w", err)
	}

	return c.CollectByDate(ctx, latestDate, symbols)
}

// parseAdjFactorData 解析复权因子数据
func (c *AdjFactorCollector) parseAdjFactorData(resp *client.TushareResponse) ([]*models.AdjFactor, error) {
	if resp.Data == nil || len(resp.Data.Items) == 0 {
		return nil, nil
	}

	adjFactors := make([]*models.AdjFactor, 0, len(resp.Data.Items))

	for _, item := range resp.Data.Items {
		if len(item) < 3 {
			logger.Warnf("复权因子数据字段不足，跳过: %v", item)
			continue
		}

		adjFactor := &models.AdjFactor{}

		// 解析股票代码
		if tsCode, ok := item[0].(string); ok {
			adjFactor.TSCode = tsCode
		} else {
			logger.Warnf("无效的股票代码: %v", item[0])
			continue
		}

		// 解析交易日期
		if tradeDateStr, ok := item[1].(string); ok {
			tradeDate, err := time.Parse("20060102", tradeDateStr)
			if err != nil {
				logger.Warnf("无效的交易日期: %v", tradeDateStr)
				continue
			}
			adjFactor.TradeDate = tradeDate
		} else {
			logger.Warnf("无效的交易日期: %v", item[1])
			continue
		}

		// 解析复权因子
		if adjFactorValue, err := c.parseFloatField(item[2]); err == nil {
			adjFactor.AdjFactor = fmt.Sprintf("%.6f", adjFactorValue)
		} else {
			logger.Warnf("无效的复权因子: %v", item[2])
			continue
		}

		// 设置创建和更新时间
		now := time.Now()
		adjFactor.CreatedAt = now
		adjFactor.UpdatedAt = now

		adjFactors = append(adjFactors, adjFactor)
	}

	return adjFactors, nil
}

// isValidAdjFactor 验证复权因子数据
func (c *AdjFactorCollector) isValidAdjFactor(adjFactor *models.AdjFactor) bool {
	// 检查必填字段
	if adjFactor.TSCode == "" {
		return false
	}

	if adjFactor.TradeDate.IsZero() {
		return false
	}

	// 检查交易日期不能是未来日期
	if adjFactor.TradeDate.After(time.Now()) {
		return false
	}

	return true
}

// parseFloatField 解析浮点数字段
func (c *AdjFactorCollector) parseFloatField(value interface{}) (float64, error) {
	switch v := value.(type) {
	case float64:
		return v, nil
	case float32:
		return float64(v), nil
	case string:
		if v == "" || v == "null" || v == "NULL" {
			return 0, fmt.Errorf("空值")
		}
		return strconv.ParseFloat(v, 64)
	case int:
		return float64(v), nil
	case int64:
		return float64(v), nil
	default:
		return 0, fmt.Errorf("不支持的数据类型: %T", value)
	}
}

// getLatestTradeDate 获取最新交易日期
func (c *AdjFactorCollector) getLatestTradeDate(ctx context.Context) (time.Time, error) {
	// 简单实现：获取最近的工作日
	now := time.Now()
	for i := 0; i < 7; i++ {
		date := now.AddDate(0, 0, -i)
		weekday := date.Weekday()
		if weekday >= time.Monday && weekday <= time.Friday {
			return date, nil
		}
	}
	return now, nil
}

// GetCollectorInfo 获取采集器信息
func (c *AdjFactorCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "复权因子数据采集器",
		"type":        "adj_factor",
		"version":     "1.0.0",
		"description": "采集股票复权因子数据，支持按日期、时间范围和最新数据采集",
		"data_source": "Tushare API",
		"features": []string{
			"按股票代码采集",
			"按日期采集",
			"按时间范围采集",
			"最新数据采集",
			"数据验证",
			"批量处理",
		},
		"api_endpoint": "adj_factor",
		"rate_limit":   "120次/分钟",
	}
}