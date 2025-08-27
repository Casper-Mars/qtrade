package client

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewTushareClient(t *testing.T) {
	client := NewTushareClient("test_token", "https://api.tushare.pro")
	
	assert.NotNil(t, client)
	assert.Equal(t, "test_token", client.token)
	assert.Equal(t, "https://api.tushare.pro", client.baseURL)
	assert.NotNil(t, client.httpClient)
	assert.NotNil(t, client.rateLimiter)

}

// TestTushareClient_Call_Integration 集成测试 - 测试真实API调用
// 注意：需要设置TUSHARE_TOKEN环境变量
func TestTushareClient_Call_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("跳过集成测试（短测试模式）")
	}
	
	token := os.Getenv("TUSHARE_TOKEN")
	if token == "" {
		t.Skip("跳过集成测试，需要设置TUSHARE_TOKEN环境变量")
	}
	
	client := NewTushareClient(token, "https://api.tushare.pro")
	
	ctx := context.Background()
	params := map[string]interface{}{
		"list_status": "L",
		"limit":      3, // 只获取3条记录用于测试
	}
	
	resp, err := client.Call(ctx, "stock_basic", params, "ts_code,symbol,name,area,industry,market,list_date,is_hs")
	
	// 如果API调用失败，记录错误并跳过测试
	if err != nil {
		t.Logf("API调用失败: %v", err)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 检查响应是否为空
	if resp == nil {
		t.Skip("API响应为空，跳过测试")
	}
	
	// 检查API响应状态
	if resp.Code != 0 {
		t.Logf("API返回错误: Code=%d, Msg=%s", resp.Code, resp.Msg)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 只有在成功时才验证数据
	assert.Equal(t, 0, resp.Code)
	assert.NotNil(t, resp.Data)
	
	if resp.Data != nil {
		assert.NotEmpty(t, resp.Data.Items)
		
		// 验证数据结构
		assert.Len(t, resp.Data.Fields, 8)
		assert.LessOrEqual(t, len(resp.Data.Items), 3)
		
		// 验证第一条数据的基本结构
		if len(resp.Data.Items) > 0 {
			firstItem := resp.Data.Items[0]
			assert.Len(t, firstItem, 8) // 应该有8个字段
			assert.NotEmpty(t, firstItem[0]) // ts_code不应为空
			assert.NotEmpty(t, firstItem[1]) // symbol不应为空
			assert.NotEmpty(t, firstItem[2]) // name不应为空
		}
	}
}

// TestTushareClient_CallWithRetry 测试重试功能
func TestTushareClient_CallWithRetry_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("跳过集成测试（短测试模式）")
	}
	
	token := os.Getenv("TUSHARE_TOKEN")
	if token == "" {
		t.Skip("跳过集成测试，需要设置TUSHARE_TOKEN环境变量")
	}
	
	// 创建客户端
	client := NewTushareClient(token, "https://api.tushare.pro")
	
	// 执行测试
	ctx := context.Background()
	params := map[string]interface{}{
		"list_status": "L",
		"limit":      5,
	}
	fields := "ts_code"
	
	resp, err := client.CallWithRetry(ctx, "stock_basic", params, fields)
	
	// 如果API调用失败，记录错误并跳过测试
	if err != nil {
		t.Logf("API调用失败: %v", err)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 检查响应是否为空
	if resp == nil {
		t.Skip("API响应为空，跳过测试")
	}
	
	// 检查API响应状态
	if resp.Code != 0 {
		t.Logf("API返回错误: Code=%d, Msg=%s", resp.Code, resp.Msg)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 只有在成功时才验证数据
	assert.Equal(t, 0, resp.Code)
	assert.NotNil(t, resp.Data)
}

// TestTushareClient_Validation 测试客户端参数验证
func TestTushareClient_Validation(t *testing.T) {
	// 测试空token
	client := NewTushareClient("", "https://api.tushare.pro")
	assert.NotNil(t, client)
	
	// 测试空URL
	client = NewTushareClient("test_token", "")
	assert.NotNil(t, client)
}

func TestRateLimiter(t *testing.T) {
	// 创建限流器，每秒允许2个请求
	rl := NewRateLimiter(2, time.Second)
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

func TestRateLimiter_Wait(t *testing.T) {
	// 创建限流器，每秒允许1个请求
	rl := NewRateLimiter(1, time.Second)
	defer rl.Close()
	
	// 第一个请求立即通过
	ctx := context.Background()
	err := rl.Wait(ctx)
	assert.NoError(t, err)
	
	// 第二个请求需要等待
	start := time.Now()
	err = rl.Wait(ctx)
	assert.NoError(t, err)
	duration := time.Since(start)
	
	// 验证等待时间大约为1秒
	assert.True(t, duration >= 900*time.Millisecond)
	assert.True(t, duration <= 1100*time.Millisecond)
}

func TestRateLimiter_WaitWithTimeout(t *testing.T) {
	// 创建限流器，每秒允许1个请求
	rl := NewRateLimiter(1, time.Second)
	defer rl.Close()
	
	// 消耗一个令牌
	assert.True(t, rl.Allow())
	
	// 创建一个很短的超时上下文
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	
	// 等待应该超时
	err := rl.Wait(ctx)
	assert.Error(t, err)
	assert.Equal(t, context.DeadlineExceeded, err)
}