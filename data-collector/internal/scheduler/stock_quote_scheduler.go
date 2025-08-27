package scheduler

import (
	"context"
	"fmt"
	"time"

	"github.com/robfig/cron/v3"

	"data-collector/internal/collectors/stock"
	"data-collector/internal/storage"
	"data-collector/pkg/client"
	"data-collector/pkg/logger"
)

// StockQuoteScheduler 股票行情数据采集调度器
type StockQuoteScheduler struct {
	collector *stock.StockQuoteCollector
	cron      *cron.Cron
	ctx       context.Context
	cancel    context.CancelFunc
}

// NewStockQuoteScheduler 创建股票行情数据采集调度器
func NewStockQuoteScheduler(tushareClient *client.TushareClient, stockRepo storage.StockRepository) *StockQuoteScheduler {
	collector := stock.NewStockQuoteCollector(tushareClient, stockRepo)
	ctx, cancel := context.WithCancel(context.Background())

	return &StockQuoteScheduler{
		collector: collector,
		cron:      cron.New(cron.WithSeconds()),
		ctx:       ctx,
		cancel:    cancel,
	}
}

// Start 启动调度器
func (s *StockQuoteScheduler) Start() error {
	logger.Info("启动股票行情数据采集调度器")

	// 添加定时任务
	if err := s.addScheduledJobs(); err != nil {
		return fmt.Errorf("添加定时任务失败: %w", err)
	}

	// 启动cron调度器
	s.cron.Start()
	logger.Info("股票行情数据采集调度器启动成功")

	return nil
}

// Stop 停止调度器
func (s *StockQuoteScheduler) Stop() {
	logger.Info("停止股票行情数据采集调度器")

	// 停止cron调度器
	ctx := s.cron.Stop()
	<-ctx.Done()

	// 取消上下文
	s.cancel()

	logger.Info("股票行情数据采集调度器已停止")
}

// addScheduledJobs 添加定时任务
func (s *StockQuoteScheduler) addScheduledJobs() error {
	// 每个交易日的15:30采集当日行情数据
	_, err := s.cron.AddFunc("0 30 15 * * 1-5", func() {
		s.collectTodayQuotes()
	})
	if err != nil {
		return fmt.Errorf("添加每日行情采集任务失败: %w", err)
	}

	// 每个交易日的16:00采集当日行情数据（补充采集）
	_, err = s.cron.AddFunc("0 0 16 * * 1-5", func() {
		s.collectTodayQuotes()
	})
	if err != nil {
		return fmt.Errorf("添加补充行情采集任务失败: %w", err)
	}

	// 每周六凌晨2:00采集上周缺失的行情数据
	_, err = s.cron.AddFunc("0 0 2 * * 6", func() {
		s.collectWeeklyMissingQuotes()
	})
	if err != nil {
		return fmt.Errorf("添加周度补充采集任务失败: %w", err)
	}

	// 每月1号凌晨3:00采集上月缺失的行情数据
	_, err = s.cron.AddFunc("0 0 3 1 * *", func() {
		s.collectMonthlyMissingQuotes()
	})
	if err != nil {
		return fmt.Errorf("添加月度补充采集任务失败: %w", err)
	}

	logger.Info("股票行情采集定时任务添加成功")
	return nil
}

// collectTodayQuotes 采集今日行情数据
func (s *StockQuoteScheduler) collectTodayQuotes() {
	logger.Info("开始执行今日股票行情数据采集任务")

	// 检查是否为交易日
	today := time.Now()
	if !s.isTradingDay(today) {
		logger.Info("今日非交易日，跳过行情数据采集")
		return
	}

	// 执行采集
	if err := s.collector.CollectLatest(s.ctx, nil); err != nil {
		logger.Errorf("采集今日股票行情数据失败: %v", err)
		return
	}

	logger.Info("今日股票行情数据采集完成")
}

// collectWeeklyMissingQuotes 采集上周缺失的行情数据
func (s *StockQuoteScheduler) collectWeeklyMissingQuotes() {
	logger.Info("开始执行周度股票行情数据补充采集任务")

	// 计算上周的时间范围
	now := time.Now()
	lastWeekStart := now.AddDate(0, 0, -7-int(now.Weekday())+1) // 上周一
	lastWeekEnd := lastWeekStart.AddDate(0, 0, 4)              // 上周五

	// 执行采集
	if err := s.collector.CollectByDateRange(s.ctx, lastWeekStart, lastWeekEnd, nil); err != nil {
		logger.Errorf("采集上周股票行情数据失败: %v", err)
		return
	}

	logger.Infof("上周股票行情数据补充采集完成，时间范围: %s 到 %s",
		lastWeekStart.Format("2006-01-02"),
		lastWeekEnd.Format("2006-01-02"))
}

// collectMonthlyMissingQuotes 采集上月缺失的行情数据
func (s *StockQuoteScheduler) collectMonthlyMissingQuotes() {
	logger.Info("开始执行月度股票行情数据补充采集任务")

	// 计算上月的时间范围
	now := time.Now()
	lastMonthStart := time.Date(now.Year(), now.Month()-1, 1, 0, 0, 0, 0, now.Location())
	lastMonthEnd := lastMonthStart.AddDate(0, 1, -1) // 上月最后一天

	// 执行采集
	if err := s.collector.CollectByDateRange(s.ctx, lastMonthStart, lastMonthEnd, nil); err != nil {
		logger.Errorf("采集上月股票行情数据失败: %v", err)
		return
	}

	logger.Infof("上月股票行情数据补充采集完成，时间范围: %s 到 %s",
		lastMonthStart.Format("2006-01-02"),
		lastMonthEnd.Format("2006-01-02"))
}

// isTradingDay 判断是否为交易日
// 简单实现：周一到周五为交易日，不考虑节假日
// 实际应用中应该查询交易日历
func (s *StockQuoteScheduler) isTradingDay(date time.Time) bool {
	weekday := date.Weekday()
	return weekday >= time.Monday && weekday <= time.Friday
}

// GetSchedulerInfo 获取调度器信息
func (s *StockQuoteScheduler) GetSchedulerInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "股票行情数据采集调度器",
		"type":        "stock_quote",
		"status":      "running",
		"jobs_count":  len(s.cron.Entries()),
		"next_runs":   s.getNextRuns(),
		"description": "定时采集股票行情数据，包括每日采集和补充采集",
	}
}

// getNextRuns 获取下次执行时间
func (s *StockQuoteScheduler) getNextRuns() []map[string]interface{} {
	entries := s.cron.Entries()
	nextRuns := make([]map[string]interface{}, 0, len(entries))

	for i, entry := range entries {
		nextRuns = append(nextRuns, map[string]interface{}{
			"job_id":   i + 1,
			"next_run": entry.Next.Format("2006-01-02 15:04:05"),
			"prev_run": entry.Prev.Format("2006-01-02 15:04:05"),
		})
	}

	return nextRuns
}

// TriggerManualCollection 手动触发采集
func (s *StockQuoteScheduler) TriggerManualCollection(collectionType string, params map[string]interface{}) error {
	logger.Infof("手动触发股票行情数据采集，类型: %s", collectionType)

	switch collectionType {
	case "today":
		s.collectTodayQuotes()
	case "weekly":
		s.collectWeeklyMissingQuotes()
	case "monthly":
		s.collectMonthlyMissingQuotes()
	case "date":
		// 采集指定日期
		if dateStr, ok := params["date"].(string); ok {
			date, err := time.Parse("2006-01-02", dateStr)
			if err != nil {
				return fmt.Errorf("日期格式错误: %w", err)
			}
			if err := s.collector.CollectByDate(s.ctx, date, nil); err != nil {
				return fmt.Errorf("采集指定日期数据失败: %w", err)
			}
		} else {
			return fmt.Errorf("缺少日期参数")
		}
	case "range":
		// 采集指定时间范围
		startDateStr, startOk := params["start_date"].(string)
		endDateStr, endOk := params["end_date"].(string)
		if !startOk || !endOk {
			return fmt.Errorf("缺少时间范围参数")
		}

		startDate, err := time.Parse("2006-01-02", startDateStr)
		if err != nil {
			return fmt.Errorf("开始日期格式错误: %w", err)
		}

		endDate, err := time.Parse("2006-01-02", endDateStr)
		if err != nil {
			return fmt.Errorf("结束日期格式错误: %w", err)
		}

		if err := s.collector.CollectByDateRange(s.ctx, startDate, endDate, nil); err != nil {
			return fmt.Errorf("采集时间范围数据失败: %w", err)
		}
	default:
		return fmt.Errorf("不支持的采集类型: %s", collectionType)
	}

	logger.Infof("手动触发股票行情数据采集完成，类型: %s", collectionType)
	return nil
}