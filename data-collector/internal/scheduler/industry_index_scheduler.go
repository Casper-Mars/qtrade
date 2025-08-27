package scheduler

import (
	"context"
	"fmt"
	"time"

	"github.com/robfig/cron/v3"

	"data-collector/internal/collectors/market"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// IndustryIndexScheduler 行业指数数据采集调度器
type IndustryIndexScheduler struct {
	industryIndexCollector *market.IndustryIndexCollector
	industryIndexValidator *market.IndustryIndexValidator
	cron                   *cron.Cron
	ctx                    context.Context
	cancel                 context.CancelFunc
}

// NewIndustryIndexScheduler 创建行业指数数据采集调度器
func NewIndustryIndexScheduler(tushareClient *client.TushareClient, marketRepo storage.MarketRepository) *IndustryIndexScheduler {
	industryIndexCollector := market.NewIndustryIndexCollector(tushareClient, marketRepo)
	industryIndexValidator := market.NewIndustryIndexValidator()
	ctx, cancel := context.WithCancel(context.Background())

	return &IndustryIndexScheduler{
		industryIndexCollector: industryIndexCollector,
		industryIndexValidator: industryIndexValidator,
		cron:                   cron.New(cron.WithSeconds()),
		ctx:                    ctx,
		cancel:                 cancel,
	}
}

// Start 启动调度器
func (s *IndustryIndexScheduler) Start() error {
	logger.Info("启动行业指数数据采集调度器")

	// 添加定时任务
	if err := s.addScheduledJobs(); err != nil {
		return fmt.Errorf("添加定时任务失败: %w", err)
	}

	// 启动cron调度器
	s.cron.Start()
	logger.Info("行业指数数据采集调度器启动成功")

	return nil
}

// Stop 停止调度器
func (s *IndustryIndexScheduler) Stop() {
	logger.Info("停止行业指数数据采集调度器")

	// 停止cron调度器
	ctx := s.cron.Stop()
	<-ctx.Done()

	// 取消上下文
	s.cancel()

	logger.Info("行业指数数据采集调度器已停止")
}

// addScheduledJobs 添加定时任务
func (s *IndustryIndexScheduler) addScheduledJobs() error {
	// 每个交易日晚上19:30采集当天行业指数数据
	_, err := s.cron.AddFunc("0 30 19 * * 1-5", func() {
		s.collectTodayIndustryIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加每日行业指数数据采集任务失败: %w", err)
	}

	// 每个交易日晚上20:00采集当天行业指数数据（补充采集）
	_, err = s.cron.AddFunc("0 0 20 * * 1-5", func() {
		s.collectTodayIndustryIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加每日行业指数数据补充采集任务失败: %w", err)
	}

	// 每月第一个交易日上午10:00更新行业分类信息
	_, err = s.cron.AddFunc("0 0 10 1 * *", func() {
		s.updateIndustryClassification()
	})
	if err != nil {
		return fmt.Errorf("添加月度行业分类信息更新任务失败: %w", err)
	}

	// 每周六上午11:00采集遗漏的行业指数数据
	_, err = s.cron.AddFunc("0 0 11 * * 6", func() {
		s.collectMissingIndustryIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加周末遗漏数据采集任务失败: %w", err)
	}

	logger.Info("行业指数数据采集定时任务添加完成")
	return nil
}

// collectTodayIndustryIndexData 采集当天行业指数数据
func (s *IndustryIndexScheduler) collectTodayIndustryIndexData() {
	logger.Info("开始采集当天行业指数数据")

	// 检查是否为交易日
	today := time.Now()
	if !s.isTradingDay(today) {
		logger.Info("今天不是交易日，跳过行业指数数据采集")
		return
	}

	// 增量采集行业指数数据（从今天开始）
	err := s.industryIndexCollector.CollectIncremental(s.ctx, today)
	if err != nil {
		logger.Error("采集当天行业指数数据失败", "error", err)
		return
	}

	logger.Info("当天行业指数数据采集完成")
}

// updateIndustryClassification 更新行业分类信息
func (s *IndustryIndexScheduler) updateIndustryClassification() {
	logger.Info("开始更新行业分类信息")

	// 检查是否为交易日
	today := time.Now()
	if !s.isTradingDay(today) {
		logger.Info("今天不是交易日，跳过行业分类信息更新")
		return
	}

	// 采集行业分类信息
	err := s.industryIndexCollector.CollectIndustryClassification(s.ctx)
	if err != nil {
		logger.Error("更新行业分类信息失败", "error", err)
		return
	}

	logger.Info("行业分类信息更新完成")
}

// collectMissingIndustryIndexData 采集遗漏的行业指数数据
func (s *IndustryIndexScheduler) collectMissingIndustryIndexData() {
	logger.Info("开始采集遗漏的行业指数数据")

	// 采集最近一周的数据，确保没有遗漏
	startDate := time.Now().AddDate(0, 0, -7)
	endDate := time.Now()

	err := s.industryIndexCollector.CollectAllIndustries(s.ctx, startDate, endDate)
	if err != nil {
		logger.Error("采集遗漏的行业指数数据失败", "error", err)
		return
	}

	logger.Info("遗漏的行业指数数据采集完成")
}

// isTradingDay 判断是否为交易日（简单实现，实际应该查询交易日历）
func (s *IndustryIndexScheduler) isTradingDay(date time.Time) bool {
	// 简单判断：周一到周五为交易日
	weekday := date.Weekday()
	return weekday >= time.Monday && weekday <= time.Friday
}

// GetSchedulerInfo 获取调度器信息
func (s *IndustryIndexScheduler) GetSchedulerInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "IndustryIndexScheduler",
		"description": "行业指数数据采集调度器",
		"version":     "1.0.0",
		"status":      "running",
		"jobs":        s.getNextRuns(),
		"created_at":  time.Now().Unix(),
	}
}

// getNextRuns 获取下次执行时间
func (s *IndustryIndexScheduler) getNextRuns() []map[string]interface{} {
	entries := s.cron.Entries()
	var nextRuns []map[string]interface{}

	for i, entry := range entries {
		nextRuns = append(nextRuns, map[string]interface{}{
			"job_id":   i + 1,
			"next_run": entry.Next.Unix(),
			"prev_run": entry.Prev.Unix(),
		})
	}

	return nextRuns
}

// TriggerManualCollection 手动触发采集任务
func (s *IndustryIndexScheduler) TriggerManualCollection(collectionType string, params map[string]interface{}) error {
	logger.Info("手动触发行业指数数据采集", "type", collectionType, "params", params)

	switch collectionType {
	case "today_industry_index":
		go s.collectTodayIndustryIndexData()
	case "industry_classification":
		go s.updateIndustryClassification()
	case "missing_industry_index":
		go s.collectMissingIndustryIndexData()
	case "incremental":
		// 从指定日期开始增量采集
		if sinceStr, ok := params["since"].(string); ok {
			if since, err := time.Parse("2006-01-02", sinceStr); err == nil {
				go func() {
					err := s.industryIndexCollector.CollectIncremental(s.ctx, since)
					if err != nil {
						logger.Error("手动增量采集失败", "error", err)
					}
				}()
			} else {
				return fmt.Errorf("日期格式错误: %s", sinceStr)
			}
		} else {
			return fmt.Errorf("缺少since参数")
		}
	case "batch":
		// 批量采集指定行业的历史数据
		if codesInterface, ok := params["codes"]; ok {
			if codes, ok := codesInterface.([]string); ok {
				startDate := time.Now().AddDate(0, 0, -30) // 默认最近30天
				endDate := time.Now()

				if startStr, ok := params["start_date"].(string); ok {
					if start, err := time.Parse("2006-01-02", startStr); err == nil {
						startDate = start
					}
				}
				if endStr, ok := params["end_date"].(string); ok {
					if end, err := time.Parse("2006-01-02", endStr); err == nil {
						endDate = end
					}
				}

				go func() {
					// 批量采集指定行业代码的数据
					for _, code := range codes {
						err := s.industryIndexCollector.CollectIndustryIndex(s.ctx, code, startDate, endDate)
						if err != nil {
							logger.Error("手动批量采集失败", "industry_code", code, "error", err)
						}
					}
				}()
			} else {
				return fmt.Errorf("codes参数格式错误")
			}
		} else {
			return fmt.Errorf("缺少codes参数")
		}
	case "all_industries":
		// 全行业批量采集
		startDate := time.Now().AddDate(0, 0, -30) // 默认最近30天
		endDate := time.Now()

		if startStr, ok := params["start_date"].(string); ok {
			if start, err := time.Parse("2006-01-02", startStr); err == nil {
				startDate = start
			}
		}
		if endStr, ok := params["end_date"].(string); ok {
			if end, err := time.Parse("2006-01-02", endStr); err == nil {
				endDate = end
			}
		}

		go func() {
			err := s.industryIndexCollector.CollectAllIndustries(s.ctx, startDate, endDate)
			if err != nil {
				logger.Error("手动全行业采集失败", "error", err)
			}
		}()
	default:
		return fmt.Errorf("不支持的采集类型: %s", collectionType)
	}

	return nil
}