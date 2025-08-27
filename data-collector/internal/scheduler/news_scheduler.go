package scheduler

import (
	"context"
	"fmt"
	"sync"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	newsCleaner "data-collector/internal/cleaners/news"
	newsCollector "data-collector/internal/collectors/news"
	"data-collector/pkg/logger"
)

// NewsScheduler 新闻调度器
type NewsScheduler struct {
	collector newsCollector.NewsCollector
	cleaner   newsCleaner.NewsCleaner
	newsRepo  storage.NewsRepository
	running   bool
	mu        sync.RWMutex
	stopCh    chan struct{}
	wg        sync.WaitGroup
}

// NewNewsScheduler 创建新闻调度器
func NewNewsScheduler(
	collector newsCollector.NewsCollector,
	cleaner newsCleaner.NewsCleaner,
	newsRepo storage.NewsRepository,
) *NewsScheduler {
	return &NewsScheduler{
		collector: collector,
		cleaner:   cleaner,
		newsRepo:  newsRepo,
		stopCh:    make(chan struct{}),
	}
}

// Start 启动调度器
func (s *NewsScheduler) Start() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return fmt.Errorf("新闻调度器已在运行")
	}

	s.running = true
	logger.Info("新闻调度器启动")

	// 启动定时任务
	s.wg.Add(1)
	go s.scheduleNewsCollection()

	return nil
}

// Stop 停止调度器
func (s *NewsScheduler) Stop() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.running {
		return fmt.Errorf("新闻调度器未在运行")
	}

	s.running = false
	close(s.stopCh)
	s.wg.Wait()

	logger.Info("新闻调度器已停止")
	return nil
}

// IsRunning 检查调度器是否在运行
func (s *NewsScheduler) IsRunning() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.running
}

// scheduleNewsCollection 调度新闻采集任务
func (s *NewsScheduler) scheduleNewsCollection() {
	defer s.wg.Done()

	// 创建定时器，每5分钟执行一次
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	// 立即执行一次
	s.collectNews()

	for {
		select {
		case <-ticker.C:
			s.collectNews()
		case <-s.stopCh:
			logger.Info("新闻采集调度任务停止")
			return
		}
	}
}

// collectNews 执行新闻采集
func (s *NewsScheduler) collectNews() {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	start := time.Now()
	logger.Info("开始新闻采集任务")

	// 采集新闻
	result, err := s.collector.CollectCLSNews(ctx)
	if err != nil {
		logger.Errorf("新闻采集失败: %v", err)
		return
	}

	if !result.Success {
		logger.Errorf("新闻采集失败: %s", result.Message)
		return
	}

	// 从采集结果中获取新闻列表
	newsList := result.NewsList
	if newsList == nil {
		newsList = []*models.News{}
	}

	if result.Total == 0 {
		logger.Info("本次采集未获取到新闻")
		return
	}

	logger.Infof("采集到新闻: %d条", result.Total)

	// 清洗新闻数据
	cleanedNews, err := s.cleaner.BatchCleanNews(ctx, newsList)
	if err != nil {
		logger.Errorf("新闻数据清洗失败: %v", err)
		return
	}

	if len(cleanedNews) == 0 {
		logger.Info("清洗后无有效新闻数据")
		return
	}

	logger.Infof("新闻数据清洗完成: %d条", len(cleanedNews))

	// 保存到数据库
	savedCount := 0
	for _, newsItem := range cleanedNews {
		err := s.newsRepo.Create(ctx, newsItem)
		if err != nil {
			// 如果是重复数据错误，跳过
			if isMongoDBDuplicateError(err) {
				logger.Debugf("新闻已存在，跳过: %s", newsItem.Title)
				continue
			}
			logger.Errorf("保存新闻失败: %s, 错误: %v", newsItem.Title, err)
			continue
		}
		savedCount++
	}

	duration := time.Since(start)
	logger.Infof("新闻采集任务完成 - 采集: %d条, 清洗: %d条, 保存: %d条, 耗时: %v", 
		len(newsList), len(cleanedNews), savedCount, duration)
}

// isMongoDBDuplicateError 检查是否为MongoDB重复键错误
func isMongoDBDuplicateError(err error) bool {
	if err == nil {
		return false
	}
	// 简单的字符串匹配，实际项目中可以使用更精确的错误类型判断
	errorStr := err.Error()
	return contains(errorStr, "duplicate key") || contains(errorStr, "E11000")
}

// contains 检查字符串是否包含子字符串（忽略大小写）
func contains(s, substr string) bool {
	return len(s) >= len(substr) && 
		(s == substr || 
		 len(s) > len(substr) && 
		 (s[:len(substr)] == substr || 
		  s[len(s)-len(substr):] == substr || 
		  containsInMiddle(s, substr)))
}

// containsInMiddle 检查字符串中间是否包含子字符串
func containsInMiddle(s, substr string) bool {
	for i := 1; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// GetStatus 获取调度器状态
func (s *NewsScheduler) GetStatus() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	status := map[string]interface{}{
		"running":        s.running,
		"collector_info": s.collector.GetCollectorInfo(),
		"cleaner_info":   s.cleaner.GetCleanerInfo(),
	}

	return status
}

// TriggerCollection 手动触发一次采集
func (s *NewsScheduler) TriggerCollection() error {
	s.mu.RLock()
	running := s.running
	s.mu.RUnlock()

	if !running {
		return fmt.Errorf("调度器未运行")
	}

	// 异步执行采集任务
	go s.collectNews()
	return nil
}