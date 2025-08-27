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

// MarketScheduler 市场数据采集调度器
type MarketScheduler struct {
	indexCollector *market.IndexCollector
	indexValidator *market.IndexValidator
	cron           *cron.Cron
	ctx            context.Context
	cancel         context.CancelFunc
}

// NewMarketScheduler 创建市场数据采集调度器
func NewMarketScheduler(tushareClient *client.TushareClient, marketRepo storage.MarketRepository) *MarketScheduler {
	indexCollector := market.NewIndexCollector(tushareClient, marketRepo)
	indexValidator := market.NewIndexValidator()
	ctx, cancel := context.WithCancel(context.Background())

	return &MarketScheduler{
		indexCollector: indexCollector,
		indexValidator: indexValidator,
		cron:           cron.New(cron.WithSeconds()),
		ctx:            ctx,
		cancel:         cancel,
	}
}

// Start 启动调度器
func (s *MarketScheduler) Start() error {
	logger.Info("启动市场数据采集调度器")

	// 添加定时任务
	if err := s.addScheduledJobs(); err != nil {
		return fmt.Errorf("添加定时任务失败: %w", err)
	}

	// 启动cron调度器
	s.cron.Start()
	logger.Info("市场数据采集调度器启动成功")

	return nil
}

// Stop 停止调度器
func (s *MarketScheduler) Stop() {
	logger.Info("停止市场数据采集调度器")

	// 停止cron调度器
	ctx := s.cron.Stop()
	<-ctx.Done()

	// 取消上下文
	s.cancel()

	logger.Info("市场数据采集调度器已停止")
}

// addScheduledJobs 添加定时任务
func (s *MarketScheduler) addScheduledJobs() error {
	// 每个交易日晚上19:00采集当天指数数据
	_, err := s.cron.AddFunc("0 0 19 * * 1-5", func() {
		s.collectTodayIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加每日指数数据采集任务失败: %w", err)
	}

	// 每个交易日晚上19:30采集当天指数数据（补充采集）
	_, err = s.cron.AddFunc("0 30 19 * * 1-5", func() {
		s.collectTodayIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加每日指数数据补充采集任务失败: %w", err)
	}

	// 每周六上午10:00采集指数基础信息更新
	_, err = s.cron.AddFunc("0 0 10 * * 6", func() {
		s.collectIndexBasicInfo()
	})
	if err != nil {
		return fmt.Errorf("添加周末指数基础信息更新任务失败: %w", err)
	}

	// 每周日上午10:00采集遗漏的指数数据
	_, err = s.cron.AddFunc("0 0 10 * * 0", func() {
		s.collectMissingIndexData()
	})
	if err != nil {
		return fmt.Errorf("添加周末遗漏数据采集任务失败: %w", err)
	}

	logger.Info("市场数据采集定时任务添加完成")
	return nil
}

// collectTodayIndexData 采集当天指数数据
func (s *MarketScheduler) collectTodayIndexData() {
	logger.Info("开始采集当天指数数据")

	// 检查是否为交易日
	today := time.Now()
	if !s.isTradingDay(today) {
		logger.Info("今天不是交易日，跳过指数数据采集")
		return
	}

	// 增量采集指数数据（从今天开始）
	err := s.indexCollector.CollectIncremental(s.ctx, today)
	if err != nil {
		logger.Error("采集当天指数数据失败", "error", err)
		return
	}

	logger.Info("当天指数数据采集完成")
}

// collectIndexBasicInfo 采集指数基础信息
func (s *MarketScheduler) collectIndexBasicInfo() {
	logger.Info("开始采集指数基础信息")

	err := s.indexCollector.CollectIndexBasic(s.ctx)
	if err != nil {
		logger.Error("采集指数基础信息失败", "error", err)
		return
	}

	logger.Info("指数基础信息采集完成")
}

// collectMissingIndexData 采集遗漏的指数数据
func (s *MarketScheduler) collectMissingIndexData() {
	logger.Info("开始采集遗漏的指数数据")

	// 采集最近一周的数据，确保没有遗漏
	since := time.Now().AddDate(0, 0, -7)
	err := s.indexCollector.CollectIncremental(s.ctx, since)
	if err != nil {
		logger.Error("采集遗漏指数数据失败", "error", err)
		return
	}

	logger.Info("遗漏指数数据采集完成")
}

// isTradingDay 判断是否为交易日（简单实现，实际应该查询交易日历）
func (s *MarketScheduler) isTradingDay(date time.Time) bool {
	// 简单判断：周一到周五为交易日
	weekday := date.Weekday()
	return weekday >= time.Monday && weekday <= time.Friday
}

// GetSchedulerInfo 获取调度器信息
func (s *MarketScheduler) GetSchedulerInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "MarketScheduler",
		"description": "市场数据采集调度器",
		"version":     "1.0.0",
		"status":      "running",
		"jobs":        s.getNextRuns(),
		"created_at":  time.Now().Unix(),
	}
}

// getNextRuns 获取下次执行时间
func (s *MarketScheduler) getNextRuns() []map[string]interface{} {
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
func (s *MarketScheduler) TriggerManualCollection(collectionType string, params map[string]interface{}) error {
	logger.Info("手动触发市场数据采集", "type", collectionType, "params", params)

	switch collectionType {
	case "today_index":
		go s.collectTodayIndexData()
	case "index_basic":
		go s.collectIndexBasicInfo()
	case "missing_index":
		go s.collectMissingIndexData()
	case "incremental":
		// 从指定日期开始增量采集
		if sinceStr, ok := params["since"].(string); ok {
			if since, err := time.Parse("2006-01-02", sinceStr); err == nil {
				go func() {
					err := s.indexCollector.CollectIncremental(s.ctx, since)
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
		// 批量采集指定指数的历史数据
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
					err := s.indexCollector.CollectBatch(s.ctx, codes, startDate, endDate)
					if err != nil {
						logger.Error("手动批量采集失败", "error", err)
					}
				}()
			} else {
				return fmt.Errorf("codes参数格式错误")
			}
		} else {
			return fmt.Errorf("缺少codes参数")
		}
	default:
		return fmt.Errorf("不支持的采集类型: %s", collectionType)
	}

	return nil
}