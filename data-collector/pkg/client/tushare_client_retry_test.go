package client

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestTushareError(t *testing.T) {
	tests := []struct {
		name     string
		code     int
		message  string
		isToken  bool
		isRate   bool
		isRetry  bool
	}{
		{"Token Invalid", 40101, "token invalid", true, false, true},
		{"Rate Limit", 40202, "rate limit exceeded", false, true, true},
		{"Server Error", 50001, "internal server error", false, false, true},
		{"Client Error", 40001, "bad request", false, false, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := &TushareError{Code: tt.code, Message: tt.message}
			assert.Equal(t, tt.isToken, err.IsTokenError())
			assert.Equal(t, tt.isRate, err.IsRateLimitError())
			assert.Equal(t, tt.isRetry, err.IsRetryableError())
		})
	}
}

func TestTushareClientWithTokenManager(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	// 创建mock服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req TushareRequest
		json.NewDecoder(r.Body).Decode(&req)
		t.Logf("Mock server received request with token: %s", req.Token)

		// 模拟token1总是失败，其他token成功
		if req.Token == "token1" {
			// token1 返回token无效错误
			t.Logf("Returning error for token1")
			resp := TushareResponse{Code: 40101, Msg: "token invalid"}
			json.NewEncoder(w).Encode(resp)
		} else {
			// 其他token返回成功
			t.Logf("Returning success for token: %s", req.Token)
			resp := TushareResponse{
				Code: 0,
				Msg:  "success",
				Data: &TushareData{Fields: []string{"field1"}, Items: [][]interface{}{{"value1"}}},
			}
			json.NewEncoder(w).Encode(resp)
		}
	}))
	defer server.Close()

	client := NewTushareClientWithTokenManager(tokens, server.URL)
	client.SetMaxRetries(3)
	client.SetRetryInterval(10 * time.Millisecond)

	ctx := context.Background()
	resp, err := client.CallWithRetry(ctx, "test_api", map[string]interface{}{}, "")

	// 应该成功，因为会自动切换到token2
	assert.NoError(t, err)
	assert.NotNil(t, resp)
	if resp != nil {
		assert.Equal(t, 0, resp.Code)
	}

	// 检查token统计
	if client.tokenManager != nil {
		stats := client.tokenManager.GetStats()
		// 打印实际统计数据用于调试
		t.Logf("Token1 stats: ErrorCount=%d, SuccessCount=%d, IsHealthy=%v", 
			stats["token1"].ErrorCount, stats["token1"].SuccessCount, stats["token1"].IsHealthy)
		t.Logf("Token2 stats: ErrorCount=%d, SuccessCount=%d, IsHealthy=%v", 
			stats["token2"].ErrorCount, stats["token2"].SuccessCount, stats["token2"].IsHealthy)
		t.Logf("Token3 stats: ErrorCount=%d, SuccessCount=%d, IsHealthy=%v", 
			stats["token3"].ErrorCount, stats["token3"].SuccessCount, stats["token3"].IsHealthy)
		
		// 验证token1有错误记录
		assert.True(t, stats["token1"].ErrorCount > 0, "token1 should have error count > 0")
		// 验证token3有成功记录（因为轮换到了token3）
		assert.True(t, stats["token3"].SuccessCount > 0, "token3 should have success count > 0")
		// 验证token1不健康
		assert.False(t, stats["token1"].IsHealthy, "token1 should be unhealthy")
		// 验证token3健康
		assert.True(t, stats["token3"].IsHealthy, "token3 should be healthy")
	}
}

func TestTushareClientRetryMechanism(t *testing.T) {
	tokens := []string{"token1"}

	callCount := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		callCount++
		if callCount < 3 {
			// 前两次返回服务器错误（可重试）
			resp := TushareResponse{Code: 50001, Msg: "internal server error"}
			json.NewEncoder(w).Encode(resp)
		} else {
			// 第三次返回成功
			resp := TushareResponse{
				Code: 0,
				Msg:  "success",
				Data: &TushareData{Fields: []string{"field1"}, Items: [][]interface{}{{"value1"}}},
			}
			json.NewEncoder(w).Encode(resp)
		}
	}))
	defer server.Close()

	client := NewTushareClientWithTokenManager(tokens, server.URL)
	client.SetMaxRetries(5)
	client.SetRetryInterval(10 * time.Millisecond)

	ctx := context.Background()
	resp, err := client.CallWithRetry(ctx, "test_api", map[string]interface{}{}, "")

	// 应该成功，经过重试
	assert.NoError(t, err)
	assert.NotNil(t, resp)
	assert.Equal(t, 0, resp.Code)
	assert.Equal(t, 3, callCount) // 调用了3次
}

func TestTushareClientMaxRetriesExceeded(t *testing.T) {
	tokens := []string{"token1"}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 总是返回服务器错误
		resp := TushareResponse{Code: 50001, Msg: "internal server error"}
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewTushareClientWithTokenManager(tokens, server.URL)
	client.SetMaxRetries(2)
	client.SetRetryInterval(10 * time.Millisecond)

	ctx := context.Background()
	resp, err := client.CallWithRetry(ctx, "test_api", map[string]interface{}{}, "")

	// 应该失败，超过最大重试次数
	assert.Error(t, err)
	assert.Nil(t, resp)
	assert.Contains(t, err.Error(), "max retries")
}

func TestTushareClientNonRetryableError(t *testing.T) {
	tokens := []string{"token1"}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 返回不可重试的错误（参数错误）
		resp := TushareResponse{Code: 40003, Msg: "parameter error"}
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	client := NewTushareClientWithTokenManager(tokens, server.URL)
	client.SetMaxRetries(3)
	client.SetRetryInterval(10 * time.Millisecond)

	ctx := context.Background()
	resp, err := client.CallWithRetry(ctx, "test_api", map[string]interface{}{}, "")

	// 应该立即失败，不重试
	assert.Error(t, err)
	assert.Nil(t, resp)
	
	// 从包装错误中提取TushareError
	var tushareErr *TushareError
	if !errors.As(err, &tushareErr) {
		t.Fatalf("Expected TushareError in error chain, got %T: %v", err, err)
	}
	assert.Equal(t, 40003, tushareErr.Code)
}

func TestTushareClientBackwardCompatibility(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		resp := TushareResponse{
			Code: 0,
			Msg:  "success",
			Data: &TushareData{Fields: []string{"field1"}, Items: [][]interface{}{{"value1"}}},
		}
		json.NewEncoder(w).Encode(resp)
	}))
	defer server.Close()

	// 使用单token模式
	client := NewTushareClient("single_token", server.URL)

	ctx := context.Background()
	resp, err := client.Call(ctx, "test_api", map[string]interface{}{}, "")

	// 应该正常工作
	assert.NoError(t, err)
	assert.NotNil(t, resp)
	assert.Equal(t, 0, resp.Code)
}

func TestRateLimiterTokenBucket(t *testing.T) {
	rl := NewRateLimiter(2, time.Second) // 每秒2个请求
	defer rl.Close()

	// 前两个请求应该立即通过
	assert.True(t, rl.Allow())
	assert.True(t, rl.Allow())

	// 第三个请求应该被限制
	assert.False(t, rl.Allow())

	// 等待一段时间后应该可以再次请求
	time.Sleep(time.Second + 100*time.Millisecond)
	assert.True(t, rl.Allow())
}

func TestRateLimiterWaitBehavior(t *testing.T) {
	rl := NewRateLimiter(1, time.Second) // 每秒1个请求
	defer rl.Close()

	ctx := context.Background()

	// 第一个请求应该立即通过
	err := rl.Wait(ctx)
	assert.NoError(t, err)

	// 第二个请求应该等待
	start := time.Now()
	err = rl.Wait(ctx)
	assert.NoError(t, err)
	duration := time.Since(start)
	assert.True(t, duration >= time.Second)
}

func TestRateLimiterContextTimeout(t *testing.T) {
	rl := NewRateLimiter(1, time.Second)
	defer rl.Close()

	// 消耗掉token
	rl.Allow()

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// 应该因为context超时而失败
	err := rl.Wait(ctx)
	assert.Error(t, err)
	assert.Equal(t, context.DeadlineExceeded, err)
}