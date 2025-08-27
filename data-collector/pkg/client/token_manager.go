package client

import (
	"fmt"
	"sync"
	"time"

	"data-collector/pkg/logger"
)

// TokenStats Token使用统计
type TokenStats struct {
	Token        string    `json:"token"`
	CallCount    int64     `json:"call_count"`
	SuccessCount int64     `json:"success_count"`
	ErrorCount   int64     `json:"error_count"`
	LastUsed     time.Time `json:"last_used"`
	IsHealthy    bool      `json:"is_healthy"`
}

// TokenManager Token管理器
type TokenManager struct {
	tokens     []string
	currentIdx int
	mutex      sync.RWMutex
	stats      map[string]*TokenStats
	enabled    bool
}

// NewTokenManager 创建Token管理器
func NewTokenManager(tokens []string) *TokenManager {
	tm := &TokenManager{
		tokens:     make([]string, len(tokens)),
		currentIdx: 0,
		stats:      make(map[string]*TokenStats),
		enabled:    len(tokens) > 0,
	}

	// 复制tokens并初始化统计
	copy(tm.tokens, tokens)
	for _, token := range tokens {
		tm.stats[token] = &TokenStats{
			Token:     token,
			IsHealthy: true,
		}
	}

	logger.Infof("TokenManager initialized with %d tokens", len(tokens))
	return tm
}

// GetToken 获取当前Token（Round Robin算法）
func (tm *TokenManager) GetToken() string {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if len(tm.tokens) == 0 {
		logger.Warn("No tokens available")
		return ""
	}

	// Round Robin: 获取当前token
	token := tm.tokens[tm.currentIdx]
	
	// 更新统计信息
	if stats, exists := tm.stats[token]; exists {
		stats.CallCount++
		stats.LastUsed = time.Now()
	}

	// 移动到下一个token
	tm.currentIdx = (tm.currentIdx + 1) % len(tm.tokens)

	logger.Debugf("Selected token: %s (index: %d)", tm.maskToken(token), tm.currentIdx-1)
	return token
}

// NextToken 强制切换到下一个Token（用于异常处理）
func (tm *TokenManager) NextToken() {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if len(tm.tokens) == 0 {
		return
	}

	oldIdx := tm.currentIdx
	tm.currentIdx = (tm.currentIdx + 1) % len(tm.tokens)
	logger.Infof("Force switched token from index %d to %d", oldIdx, tm.currentIdx)
}

// RecordSuccess 记录成功调用
func (tm *TokenManager) RecordSuccess(token string) {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if stats, exists := tm.stats[token]; exists {
		stats.SuccessCount++
		stats.IsHealthy = true
	}
}

// RecordError 记录错误调用
func (tm *TokenManager) RecordError(token string, errorCode int) {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if stats, exists := tm.stats[token]; exists {
		stats.ErrorCount++
		
		// 根据错误码判断token健康状态
		if errorCode == 40101 { // Token无效
			stats.IsHealthy = false
			logger.Warnf("Token marked as unhealthy due to invalid token error: %s", tm.maskToken(token))
		}
	}
}

// GetStats 获取所有Token统计信息
func (tm *TokenManager) GetStats() map[string]*TokenStats {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()

	// 创建副本避免并发问题
	stats := make(map[string]*TokenStats)
	for token, stat := range tm.stats {
		stats[token] = &TokenStats{
			Token:        stat.Token,
			CallCount:    stat.CallCount,
			SuccessCount: stat.SuccessCount,
			ErrorCount:   stat.ErrorCount,
			LastUsed:     stat.LastUsed,
			IsHealthy:    stat.IsHealthy,
		}
	}
	return stats
}

// GetHealthyTokenCount 获取健康Token数量
func (tm *TokenManager) GetHealthyTokenCount() int {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()

	count := 0
	for _, stats := range tm.stats {
		if stats.IsHealthy {
			count++
		}
	}
	return count
}

// AddToken 动态添加Token
func (tm *TokenManager) AddToken(token string) error {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if token == "" {
		return fmt.Errorf("token cannot be empty")
	}

	// 检查是否已存在
	for _, existingToken := range tm.tokens {
		if existingToken == token {
			return fmt.Errorf("token already exists")
		}
	}

	// 添加token
	tm.tokens = append(tm.tokens, token)
	tm.stats[token] = &TokenStats{
		Token:     token,
		IsHealthy: true,
	}

	logger.Infof("Added new token: %s", tm.maskToken(token))
	return nil
}

// RemoveToken 动态移除Token
func (tm *TokenManager) RemoveToken(token string) error {
	tm.mutex.Lock()
	defer tm.mutex.Unlock()

	if len(tm.tokens) <= 1 {
		return fmt.Errorf("cannot remove token: at least one token must remain")
	}

	// 查找并移除token
	for i, existingToken := range tm.tokens {
		if existingToken == token {
			// 移除token
			tm.tokens = append(tm.tokens[:i], tm.tokens[i+1:]...)
			
			// 调整当前索引
			if tm.currentIdx >= len(tm.tokens) {
				tm.currentIdx = 0
			} else if i <= tm.currentIdx {
				tm.currentIdx = (tm.currentIdx - 1 + len(tm.tokens)) % len(tm.tokens)
			}
			
			// 删除统计信息
			delete(tm.stats, token)
			
			logger.Infof("Removed token: %s", tm.maskToken(token))
			return nil
		}
	}

	return fmt.Errorf("token not found")
}

// IsEnabled 检查Token管理器是否启用
func (tm *TokenManager) IsEnabled() bool {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	return tm.enabled && len(tm.tokens) > 0
}

// GetTokenCount 获取Token总数
func (tm *TokenManager) GetTokenCount() int {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()
	return len(tm.tokens)
}

// LogStats 输出Token使用统计日志
func (tm *TokenManager) LogStats() {
	tm.mutex.RLock()
	defer tm.mutex.RUnlock()

	logger.Info("=== Token Usage Statistics ===")
	for token, stats := range tm.stats {
		successRate := float64(0)
		if stats.CallCount > 0 {
			successRate = float64(stats.SuccessCount) / float64(stats.CallCount) * 100
		}

		logger.Infof("Token: %s, Calls: %d, Success: %d, Errors: %d, Success Rate: %.2f%%, Healthy: %v, Last Used: %s",
			tm.maskToken(token),
			stats.CallCount,
			stats.SuccessCount,
			stats.ErrorCount,
			successRate,
			stats.IsHealthy,
			stats.LastUsed.Format("2006-01-02 15:04:05"),
		)
	}
}

// maskToken 遮蔽Token用于日志输出（保护敏感信息）
func (tm *TokenManager) maskToken(token string) string {
	if len(token) <= 8 {
		return "****"
	}
	return token[:4] + "****" + token[len(token)-4:]
}