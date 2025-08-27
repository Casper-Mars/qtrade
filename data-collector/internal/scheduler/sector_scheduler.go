package scheduler

import (
	"context"
	"time"

	"data-collector/internal/collectors/market"
	"data-collector/pkg/logger"

	"github.com/robfig/cron/v3"
)

// SectorScheduler 板块分类数据定时调度器
type SectorScheduler struct {
	cron            *cron.Cron
	sectorCollector *market.SectorCollector
	isRunning       bool
}

// NewSectorScheduler 创建板块分类定时调度器
func NewSectorScheduler(sectorCollector *market.SectorCollector) *SectorScheduler {
	return &SectorScheduler{
		cron:            cron.New(cron.WithSeconds()),
		sectorCollector: sectorCollector,
		isRunning:       false,
	}
}

// Start 启动定时调度
func (s *SectorScheduler) Start() error {
	if s.isRunning {
		logger.Warn("板块分类调度器已在运行中")
		return nil
	}

	// 每周一晚上8点采集板块分类更新
	// cron表达式: 秒 分 时 日 月 周
	// 0 0 20 * * 1 表示每周一晚上8点
	_, err := s.cron.AddFunc("0 0 20 * * 1", s.collectSectorClassification)
	if err != nil {
		logger.Error("添加板块分类采集任务失败", "error", err)
		return err
	}

	// 每月第一个交易日全量更新成分股信息
	// 每月1号早上9点执行（简化处理，实际应该考虑交易日历）
	// 0 0 9 1 * * 表示每月1号早上9点
	_, err = s.cron.AddFunc("0 0 9 1 * *", s.collectAllSectorConstituents)
	if err != nil {
		logger.Error("添加板块成分股采集任务失败", "error", err)
		return err
	}

	// 每日增量更新（每个交易日收盘后21点执行）
	// 0 0 21 * * 1-5 表示周一到周五晚上9点
	_, err = s.cron.AddFunc("0 0 21 * * 1-5", s.collectIncrementalUpdate)
	if err != nil {
		logger.Error("添加板块增量更新任务失败", "error", err)
		return err
	}

	s.cron.Start()
	s.isRunning = true

	logger.Info("板块分类定时调度器启动成功")
	return nil
}

// Stop 停止定时调度
func (s *SectorScheduler) Stop() {
	if !s.isRunning {
		logger.Warn("板块分类调度器未在运行")
		return
	}

	s.cron.Stop()
	s.isRunning = false
	logger.Info("板块分类定时调度器已停止")
}

// IsRunning 检查调度器是否在运行
func (s *SectorScheduler) IsRunning() bool {
	return s.isRunning
}

// GetSchedulerInfo 获取调度器信息
func (s *SectorScheduler) GetSchedulerInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "SectorScheduler",
		"description": "板块分类数据定时调度器",
		"is_running":  s.isRunning,
		"tasks": []map[string]interface{}{
			{
				"name":        "板块分类采集",
				"schedule":    "每周一晚上8点",
				"cron":        "0 0 20 * * 1",
				"description": "采集板块分类信息更新",
			},
			{
				"name":        "板块成分股全量采集",
				"schedule":    "每月第一个交易日早上9点",
				"cron":        "0 0 9 1 * *",
				"description": "全量更新板块成分股信息",
			},
			{
				"name":        "板块增量更新",
				"schedule":    "每个交易日晚上9点",
				"cron":        "0 0 21 * * 1-5",
				"description": "增量更新板块数据",
			},
		},
		"created_at": time.Now().Unix(),
	}
}

// collectSectorClassification 采集板块分类信息
func (s *SectorScheduler) collectSectorClassification() {
	logger.Info("开始执行板块分类采集任务")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()

	start := time.Now()
	err := s.sectorCollector.CollectSectorClassification(ctx)
	duration := time.Since(start)

	if err != nil {
		logger.Error("板块分类采集任务执行失败", "error", err, "duration", duration)
		return
	}

	logger.Info("板块分类采集任务执行成功", "duration", duration)
}

// collectAllSectorConstituents 全量采集板块成分股
func (s *SectorScheduler) collectAllSectorConstituents() {
	logger.Info("开始执行板块成分股全量采集任务")

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Hour)
	defer cancel()

	start := time.Now()
	err := s.sectorCollector.CollectAllSectors(ctx)
	duration := time.Since(start)

	if err != nil {
		logger.Error("板块成分股全量采集任务执行失败", "error", err, "duration", duration)
		return
	}

	logger.Info("板块成分股全量采集任务执行成功", "duration", duration)
}

// collectIncrementalUpdate 增量更新板块数据
func (s *SectorScheduler) collectIncrementalUpdate() {
	logger.Info("开始执行板块数据增量更新任务")

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Hour)
	defer cancel()

	// 从7天前开始增量更新
	since := time.Now().AddDate(0, 0, -7)

	start := time.Now()
	err := s.sectorCollector.CollectIncremental(ctx, since)
	duration := time.Since(start)

	if err != nil {
		logger.Error("板块数据增量更新任务执行失败", "error", err, "duration", duration, "since", since)
		return
	}

	logger.Info("板块数据增量更新任务执行成功", "duration", duration, "since", since)
}

// TriggerSectorClassification 手动触发板块分类采集
func (s *SectorScheduler) TriggerSectorClassification() error {
	logger.Info("手动触发板块分类采集任务")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
	defer cancel()

	return s.sectorCollector.CollectSectorClassification(ctx)
}

// TriggerAllSectorConstituents 手动触发全量板块成分股采集
func (s *SectorScheduler) TriggerAllSectorConstituents() error {
	logger.Info("手动触发全量板块成分股采集任务")

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Hour)
	defer cancel()

	return s.sectorCollector.CollectAllSectors(ctx)
}

// TriggerIncrementalUpdate 手动触发增量更新
func (s *SectorScheduler) TriggerIncrementalUpdate(since time.Time) error {
	logger.Info("手动触发板块数据增量更新任务", "since", since)

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Hour)
	defer cancel()

	return s.sectorCollector.CollectIncremental(ctx, since)
}