package services

import (
	"context"
	"fmt"

	"data-collector/internal/scheduler"
	"data-collector/internal/storage"
	newsCleaner "data-collector/internal/cleaners/news"
	newsCollector "data-collector/internal/collectors/news"
	"data-collector/pkg/logger"
)

// NewsService 新闻服务
type NewsService struct {
	collector newsCollector.NewsCollector
	cleaner   newsCleaner.NewsCleaner
	scheduler *scheduler.NewsScheduler
	newsRepo  storage.NewsRepository
}

// NewNewsService 创建新闻服务
func NewNewsService(newsRepo storage.NewsRepository) *NewsService {
	// 创建新闻采集器
	collector := newsCollector.NewCLSNewsCollector(newsRepo)
	
	// 创建新闻清洗器
	cleaner := newsCleaner.NewDefaultNewsCleaner()
	
	// 创建新闻调度器
	newsScheduler := scheduler.NewNewsScheduler(collector, cleaner, newsRepo)

	return &NewsService{
		collector: collector,
		cleaner:   cleaner,
		scheduler: newsScheduler,
		newsRepo:  newsRepo,
	}
}

// Start 启动新闻服务
func (s *NewsService) Start() error {
	logger.Info("启动新闻服务")
	
	// 启动调度器
	if err := s.scheduler.Start(); err != nil {
		return fmt.Errorf("启动新闻调度器失败: %w", err)
	}
	
	logger.Info("新闻服务启动成功")
	return nil
}

// Stop 停止新闻服务
func (s *NewsService) Stop() error {
	logger.Info("停止新闻服务")
	
	// 停止调度器
	if err := s.scheduler.Stop(); err != nil {
		return fmt.Errorf("停止新闻调度器失败: %w", err)
	}
	
	logger.Info("新闻服务已停止")
	return nil
}

// GetStatus 获取服务状态
func (s *NewsService) GetStatus() map[string]interface{} {
	return map[string]interface{}{
		"service":   "news",
		"running":   s.scheduler.IsRunning(),
		"scheduler": s.scheduler.GetStatus(),
	}
}

// TriggerCollection 手动触发采集
func (s *NewsService) TriggerCollection() error {
	return s.scheduler.TriggerCollection()
}

// CollectNews 手动采集新闻
func (s *NewsService) CollectNews(ctx context.Context) (*newsCollector.CollectResult, error) {
	return s.collector.CollectCLSNews(ctx)
}

// GetCollectorInfo 获取采集器信息
func (s *NewsService) GetCollectorInfo() map[string]interface{} {
	return s.collector.GetCollectorInfo()
}

// GetCleanerInfo 获取清洗器信息
func (s *NewsService) GetCleanerInfo() map[string]interface{} {
	return s.cleaner.GetCleanerInfo()
}