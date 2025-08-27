package stock

import (
	"context"
	"fmt"
	"sync"
	"time"

	"data-collector/pkg/logger"
	"github.com/robfig/cron/v3"
)

// AdjFactorScheduler 复权因子采集调度器
type AdjFactorScheduler struct {
	collector *AdjFactorCollector
	cron      *cron.Cron
	mu        sync.RWMutex
	jobs      map[string]cron.EntryID
	running   bool
}

// NewAdjFactorScheduler 创建复权因子采集调度器
func NewAdjFactorScheduler(collector *AdjFactorCollector) *AdjFactorScheduler {
	return &AdjFactorScheduler{
		collector: collector,
		cron:      cron.New(cron.WithSeconds()),
		jobs:      make(map[string]cron.EntryID),
		running:   false,
	}
}

// Start 启动调度器
func (s *AdjFactorScheduler) Start() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return fmt.Errorf("调度器已经在运行中")
	}

	s.cron.Start()
	s.running = true
	logger.Info("复权因子采集调度器已启动")

	return nil
}

// Stop 停止调度器
func (s *AdjFactorScheduler) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.running {
		return
	}

	ctx := s.cron.Stop()
	<-ctx.Done()
	s.running = false
	logger.Info("复权因子采集调度器已停止")
}

// AddDailyJob 添加每日采集任务
func (s *AdjFactorScheduler) AddDailyJob(hour, minute int, symbols []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 构建cron表达式：每天指定时间执行
	cronExpr := fmt.Sprintf("0 %d %d * * *", minute, hour)

	jobName := fmt.Sprintf("daily_%d_%d", hour, minute)

	// 如果任务已存在，先删除
	if entryID, exists := s.jobs[jobName]; exists {
		s.cron.Remove(entryID)
		delete(s.jobs, jobName)
	}

	// 添加新任务
	entryID, err := s.cron.AddFunc(cronExpr, func() {
		s.runDailyCollection(symbols)
	})

	if err != nil {
		return fmt.Errorf("添加每日采集任务失败: %w", err)
	}

	s.jobs[jobName] = entryID
	logger.Infof("已添加每日复权因子采集任务: %s (每天 %02d:%02d)", jobName, hour, minute)

	return nil
}

// AddWeeklyJob 添加每周采集任务
func (s *AdjFactorScheduler) AddWeeklyJob(weekday time.Weekday, hour, minute int, symbols []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 构建cron表达式：每周指定时间执行
	cronExpr := fmt.Sprintf("0 %d %d * * %d", minute, hour, weekday)

	jobName := fmt.Sprintf("weekly_%d_%d_%d", weekday, hour, minute)

	// 如果任务已存在，先删除
	if entryID, exists := s.jobs[jobName]; exists {
		s.cron.Remove(entryID)
		delete(s.jobs, jobName)
	}

	// 添加新任务
	entryID, err := s.cron.AddFunc(cronExpr, func() {
		s.runWeeklyCollection(symbols)
	})

	if err != nil {
		return fmt.Errorf("添加每周采集任务失败: %w", err)
	}

	s.jobs[jobName] = entryID
	logger.Infof("已添加每周复权因子采集任务: %s (每周%s %02d:%02d)", jobName, weekday.String(), hour, minute)

	return nil
}

// AddMonthlyJob 添加每月采集任务
func (s *AdjFactorScheduler) AddMonthlyJob(day, hour, minute int, symbols []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 构建cron表达式：每月指定时间执行
	cronExpr := fmt.Sprintf("0 %d %d %d * *", minute, hour, day)

	jobName := fmt.Sprintf("monthly_%d_%d_%d", day, hour, minute)

	// 如果任务已存在，先删除
	if entryID, exists := s.jobs[jobName]; exists {
		s.cron.Remove(entryID)
		delete(s.jobs, jobName)
	}

	// 添加新任务
	entryID, err := s.cron.AddFunc(cronExpr, func() {
		s.runMonthlyCollection(symbols)
	})

	if err != nil {
		return fmt.Errorf("添加每月采集任务失败: %w", err)
	}

	s.jobs[jobName] = entryID
	logger.Infof("已添加每月复权因子采集任务: %s (每月%d日 %02d:%02d)", jobName, day, hour, minute)

	return nil
}

// TriggerManualCollection 手动触发采集
func (s *AdjFactorScheduler) TriggerManualCollection(symbols []string) {
	go func() {
		logger.Info("开始手动触发复权因子采集")
		ctx := context.Background()
		if err := s.collector.CollectLatest(ctx, symbols); err != nil {
			logger.Errorf("手动复权因子采集失败: %v", err)
		} else {
			logger.Info("手动复权因子采集完成")
		}
	}()
}

// RemoveJob 删除指定任务
func (s *AdjFactorScheduler) RemoveJob(jobName string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	entryID, exists := s.jobs[jobName]
	if !exists {
		return fmt.Errorf("任务 %s 不存在", jobName)
	}

	s.cron.Remove(entryID)
	delete(s.jobs, jobName)
	logger.Infof("已删除复权因子采集任务: %s", jobName)

	return nil
}

// GetJobs 获取所有任务信息
func (s *AdjFactorScheduler) GetJobs() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	jobList := make([]map[string]interface{}, 0, len(s.jobs))
	for jobName, entryID := range s.jobs {
		entry := s.cron.Entry(entryID)
		jobInfo := map[string]interface{}{
			"name":      jobName,
			"entry_id":  entryID,
			"next_run":  entry.Next,
			"prev_run":  entry.Prev,
		}
		jobList = append(jobList, jobInfo)
	}

	return map[string]interface{}{
		"running":    s.running,
		"job_count":  len(s.jobs),
		"jobs":       jobList,
		"scheduler":  "adj_factor_scheduler",
	}
}

// runDailyCollection 执行每日采集
func (s *AdjFactorScheduler) runDailyCollection(symbols []string) {
	logger.Info("开始执行每日复权因子采集任务")
	ctx := context.Background()

	if err := s.collector.CollectLatest(ctx, symbols); err != nil {
		logger.Errorf("每日复权因子采集失败: %v", err)
	} else {
		logger.Info("每日复权因子采集完成")
	}
}

// runWeeklyCollection 执行每周采集
func (s *AdjFactorScheduler) runWeeklyCollection(symbols []string) {
	logger.Info("开始执行每周复权因子采集任务")
	ctx := context.Background()

	// 采集最近一周的数据
	endDate := time.Now()
	startDate := endDate.AddDate(0, 0, -7)

	if err := s.collector.CollectByDateRange(ctx, startDate, endDate, symbols); err != nil {
		logger.Errorf("每周复权因子采集失败: %v", err)
	} else {
		logger.Info("每周复权因子采集完成")
	}
}

// runMonthlyCollection 执行每月采集
func (s *AdjFactorScheduler) runMonthlyCollection(symbols []string) {
	logger.Info("开始执行每月复权因子采集任务")
	ctx := context.Background()

	// 采集最近一个月的数据
	endDate := time.Now()
	startDate := endDate.AddDate(0, -1, 0)

	if err := s.collector.CollectByDateRange(ctx, startDate, endDate, symbols); err != nil {
		logger.Errorf("每月复权因子采集失败: %v", err)
	} else {
		logger.Info("每月复权因子采集完成")
	}
}