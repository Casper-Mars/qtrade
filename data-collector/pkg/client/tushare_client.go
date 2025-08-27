package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"data-collector/pkg/logger"
)

// TushareClient Tushare API客户端
type TushareClient struct {
	token        string          // 单token模式（兼容性）
	tokenManager *TokenManager   // 多token管理器
	baseURL      string
	httpClient   *http.Client
	rateLimiter  *RateLimiter
	maxRetries   int             // 最大重试次数
	retryInterval time.Duration  // 重试间隔
}

// TushareRequest Tushare API请求结构
type TushareRequest struct {
	APIName string                 `json:"api_name"`
	Token   string                 `json:"token"`
	Params  map[string]interface{} `json:"params,omitempty"`
	Fields  string                 `json:"fields,omitempty"`
}

// TushareResponse Tushare API响应结构
type TushareResponse struct {
	RequestID string       `json:"request_id"`
	Code      int          `json:"code"`
	Msg       string       `json:"msg"`
	Data      *TushareData `json:"data"`
}

// TushareData Tushare数据结构
type TushareData struct {
	Fields []string        `json:"fields"`
	Items  [][]interface{} `json:"items"`
}

// TushareError Tushare API错误
type TushareError struct {
	Code    int    `json:"code"`
	Message string `json:"msg"`
}

func (e *TushareError) Error() string {
	return fmt.Sprintf("tushare API error: code=%d, msg=%s", e.Code, e.Message)
}

// IsTokenError 检查是否为token相关错误
func (e *TushareError) IsTokenError() bool {
	return e.Code == 40101 // Token无效
}

// IsRateLimitError 检查是否为频率限制错误
func (e *TushareError) IsRateLimitError() bool {
	return e.Code == 40203 || e.Code == 40202 // 频率限制
}

// IsRetryableError 检查是否为可重试错误
func (e *TushareError) IsRetryableError() bool {
	return e.IsTokenError() || e.IsRateLimitError() || e.Code == 40001 || e.Code == 50001 // 积分不足和服务器错误也可重试
}

// RateLimiter 限流器
type RateLimiter struct {
	tokens   chan struct{}
	interval time.Duration
	quit     chan struct{}
	mu       sync.Mutex
}

// NewRateLimiter 创建限流器
func NewRateLimiter(rate int, interval time.Duration) *RateLimiter {
	rl := &RateLimiter{
		tokens:   make(chan struct{}, rate),
		interval: interval,
		quit:     make(chan struct{}),
	}

	// 初始化令牌桶
	for i := 0; i < rate; i++ {
		rl.tokens <- struct{}{}
	}

	// 启动令牌补充协程
	go rl.refillTokens(rate)

	return rl
}

// refillTokens 定期补充令牌
func (rl *RateLimiter) refillTokens(rate int) {
	ticker := time.NewTicker(rl.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// 补充令牌，但不超过桶容量
			for i := 0; i < rate; i++ {
				select {
				case rl.tokens <- struct{}{}:
				default:
					// 桶已满，停止补充
					break
				}
			}
		case <-rl.quit:
			return
		}
	}
}

// Allow 检查是否允许请求
func (rl *RateLimiter) Allow() bool {
	select {
	case <-rl.tokens:
		return true
	default:
		return false
	}
}

// Wait 等待直到可以发送请求
func (rl *RateLimiter) Wait(ctx context.Context) error {
	for {
		select {
		case <-rl.tokens:
			return nil
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(100 * time.Millisecond):
			// 继续等待
		}
	}
}

// Close 关闭限流器
func (rl *RateLimiter) Close() {
	close(rl.quit)
}

// NewTushareClient 创建Tushare客户端（单token模式）
func NewTushareClient(token, baseURL string) *TushareClient {
	return &TushareClient{
		token:   token,
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		rateLimiter: NewRateLimiter(200, time.Minute), // 每分钟200次
		maxRetries:  3,
		retryInterval: time.Second,
	}
}

// NewTushareClientWithTokenManager 创建带Token管理器的Tushare客户端
func NewTushareClientWithTokenManager(tokens []string, baseURL string) *TushareClient {
	tokenManager := NewTokenManager(tokens)
	
	return &TushareClient{
		tokenManager: tokenManager,
		baseURL:      baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		rateLimiter: NewRateLimiter(200, time.Minute), // 每分钟200次
		maxRetries:  3,
		retryInterval: time.Second,
	}
}

// SetMaxRetries 设置最大重试次数
func (c *TushareClient) SetMaxRetries(maxRetries int) {
	c.maxRetries = maxRetries
}

// SetRetryInterval 设置重试间隔
func (c *TushareClient) SetRetryInterval(interval time.Duration) {
	c.retryInterval = interval
}

// Call 调用Tushare API
func (c *TushareClient) Call(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*TushareResponse, error) {
	return c.CallWithRetry(ctx, apiName, params, fields)
}

// CallWithRetry 带重试机制的API调用
func (c *TushareClient) CallWithRetry(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*TushareResponse, error) {
	var lastErr error
	var currentToken string

	for attempt := 0; attempt < c.maxRetries; attempt++ {
		// 获取token
		if c.tokenManager != nil && c.tokenManager.IsEnabled() {
			currentToken = c.tokenManager.GetToken()
			if currentToken == "" {
				return nil, fmt.Errorf("no available tokens")
			}
		} else {
			currentToken = c.token
		}

		// 执行API调用
		resp, err := c.callWithToken(ctx, apiName, params, fields, currentToken)
		if err == nil {
			// 成功：记录统计
			if c.tokenManager != nil {
				c.tokenManager.RecordSuccess(currentToken)
			}
			return resp, nil
		}

		// 错误处理
		lastErr = err
		if tushareErr, ok := err.(*TushareError); ok {
			// 记录错误统计
			if c.tokenManager != nil {
				c.tokenManager.RecordError(currentToken, tushareErr.Code)
			}

			// Token错误：立即切换token
			if tushareErr.IsTokenError() {
				logger.Warnf("Token error detected (code: %d), switching to next token", tushareErr.Code)
				if c.tokenManager != nil {
					c.tokenManager.NextToken()
				}
				continue
			}

			// 频率限制错误：切换token并等待
			if tushareErr.IsRateLimitError() {
				logger.Warnf("Rate limit error detected (code: %d), switching token and retrying", tushareErr.Code)
				if c.tokenManager != nil {
					c.tokenManager.NextToken()
				}
				// 等待重试间隔
				time.Sleep(c.retryInterval * time.Duration(attempt+1))
				continue
			}

			// 其他API错误：根据是否可重试决定
			if !tushareErr.IsRetryableError() {
				logger.Errorf("Non-retryable API error: %v", tushareErr)
				break
			}
		}

		// 网络错误等：指数退避重试
		logger.Warnf("Request failed (attempt %d/%d): %v", attempt+1, c.maxRetries, err)
		if attempt < c.maxRetries-1 {
			backoffDuration := c.retryInterval * time.Duration(1<<uint(attempt)) // 指数退避
			logger.Debugf("Retrying in %v...", backoffDuration)
			time.Sleep(backoffDuration)
		}
	}

	return nil, fmt.Errorf("max retries (%d) exceeded, last error: %w", c.maxRetries, lastErr)
}

// callWithToken 使用指定token进行API调用
func (c *TushareClient) callWithToken(ctx context.Context, apiName string, params map[string]interface{}, fields string, token string) (*TushareResponse, error) {
	req := &TushareRequest{
		APIName: apiName,
		Token:   token,
		Params:  params,
		Fields:  fields,
	}

	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request failed: %w", err)
	}

	logger.Debugf("Tushare API request: %s %s", apiName, string(reqBody))

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.baseURL, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("create request failed: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("http request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response failed: %w", err)
	}

	logger.Debugf("Tushare API response: %s", string(respBody))

	var tushareResp TushareResponse
	if err := json.Unmarshal(respBody, &tushareResp); err != nil {
		return nil, fmt.Errorf("unmarshal response failed: %w", err)
	}

	if tushareResp.Code != 0 {
		return nil, &TushareError{
			Code:    tushareResp.Code,
			Message: tushareResp.Msg,
		}
	}

	return &tushareResp, nil
}

// call 实际的API调用（保持向后兼容）
func (c *TushareClient) call(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*TushareResponse, error) {
	// 如果启用了TokenManager，使用CallWithRetry
	if c.tokenManager != nil && c.tokenManager.IsEnabled() {
		return c.CallWithRetry(ctx, apiName, params, fields)
	}
	
	// 否则使用原有逻辑
	return c.callWithToken(ctx, apiName, params, fields, c.token)
}

// isRetryableError 判断是否是可重试的错误
func (c *TushareClient) isRetryableError(err error) bool {
	// 超时错误可以重试
	if err == context.DeadlineExceeded {
		return true
	}

	// Tushare特定错误码判断
	errorStr := err.Error()
	if errorStr == "tushare API error: code=40203" { // 频率限制
		return true
	}
	if errorStr == "tushare API error: code=40001" { // 积分不足，不重试
		return false
	}
	if errorStr == "tushare API error: code=40101" { // Token无效，不重试
		return false
	}

	return false
}

// Close 关闭客户端
func (c *TushareClient) Close() {
	if c.rateLimiter != nil {
		c.rateLimiter.Close()
	}
}
