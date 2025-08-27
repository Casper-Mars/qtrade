package client

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewTokenManager(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)

	assert.NotNil(t, tm)
	assert.True(t, tm.IsEnabled())
	assert.Equal(t, 3, tm.GetTokenCount())
	assert.Equal(t, 3, tm.GetHealthyTokenCount())
}

func TestNewTokenManagerEmpty(t *testing.T) {
	tokens := []string{}

	tm := NewTokenManager(tokens)

	assert.NotNil(t, tm)
	assert.False(t, tm.IsEnabled())
	assert.Equal(t, 0, tm.GetTokenCount())
	assert.Equal(t, 0, tm.GetHealthyTokenCount())
}

func TestTokenManagerRoundRobin(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)

	// 测试轮询获取token
	token1 := tm.GetToken()
	token2 := tm.GetToken()
	token3 := tm.GetToken()
	token4 := tm.GetToken() // 应该回到第一个

	assert.Equal(t, "token1", token1)
	assert.Equal(t, "token2", token2)
	assert.Equal(t, "token3", token3)
	assert.Equal(t, "token1", token4)
}

func TestTokenManagerNextToken(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)

	// 获取第一个token
	token1 := tm.GetToken()
	assert.Equal(t, "token1", token1)

	// 强制切换到下一个
	tm.NextToken()
	token2 := tm.GetToken()
	assert.Equal(t, "token3", token2) // 应该是token3，因为NextToken切换了
}

func TestTokenManagerRecordSuccess(t *testing.T) {
	tokens := []string{"token1", "token2"}

	tm := NewTokenManager(tokens)

	// 记录成功调用
	tm.RecordSuccess("token1")
	tm.RecordSuccess("token1")

	stats := tm.GetStats()
	assert.Equal(t, int64(2), stats["token1"].SuccessCount)
	assert.True(t, stats["token1"].IsHealthy)
}

func TestTokenManagerRecordError(t *testing.T) {
	tokens := []string{"token1", "token2"}

	tm := NewTokenManager(tokens)

	// 记录普通错误
	tm.RecordError("token1", 40001)
	stats := tm.GetStats()
	assert.Equal(t, int64(1), stats["token1"].ErrorCount)
	assert.True(t, stats["token1"].IsHealthy) // 普通错误不影响健康状态

	// 记录token无效错误
	tm.RecordError("token1", 40101)
	stats = tm.GetStats()
	assert.Equal(t, int64(2), stats["token1"].ErrorCount)
	assert.False(t, stats["token1"].IsHealthy) // token无效错误标记为不健康
}

func TestTokenManagerAddToken(t *testing.T) {
	tokens := []string{"token1", "token2"}

	tm := NewTokenManager(tokens)
	assert.Equal(t, 2, tm.GetTokenCount())

	// 添加新token
	err := tm.AddToken("token3")
	assert.NoError(t, err)
	assert.Equal(t, 3, tm.GetTokenCount())

	// 添加重复token
	err = tm.AddToken("token1")
	assert.Error(t, err)
	assert.Equal(t, 3, tm.GetTokenCount())
}

func TestTokenManagerRemoveToken(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)
	assert.Equal(t, 3, tm.GetTokenCount())

	// 移除存在的token
	err := tm.RemoveToken("token2")
	assert.NoError(t, err)
	assert.Equal(t, 2, tm.GetTokenCount())

	// 移除不存在的token
	err = tm.RemoveToken("token4")
	assert.Error(t, err)
	assert.Equal(t, 2, tm.GetTokenCount())

	// 尝试移除倒数第二个token，应该成功
	err = tm.RemoveToken("token1")
	assert.NoError(t, err)
	assert.Equal(t, 1, tm.GetTokenCount())
	assert.True(t, tm.IsEnabled())

	// 尝试移除最后一个token，应该失败（至少保留一个token）
	err = tm.RemoveToken("token3")
	assert.Error(t, err)
	assert.Equal(t, 1, tm.GetTokenCount())
	assert.True(t, tm.IsEnabled())
}

func TestTokenManagerConcurrency(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)

	// 并发获取token
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			for j := 0; j < 100; j++ {
				token := tm.GetToken()
				assert.NotEmpty(t, token)
				tm.RecordSuccess(token)
			}
			done <- true
		}()
	}

	// 等待所有goroutine完成
	for i := 0; i < 10; i++ {
		<-done
	}

	// 验证统计信息
	stats := tm.GetStats()
	totalSuccess := int64(0)
	for _, stat := range stats {
		totalSuccess += stat.SuccessCount
	}
	assert.Equal(t, int64(1000), totalSuccess)
}

func TestTokenManagerGetHealthyTokenCount(t *testing.T) {
	tokens := []string{"token1", "token2", "token3"}

	tm := NewTokenManager(tokens)
	assert.Equal(t, 3, tm.GetHealthyTokenCount())

	// 标记一个token为不健康
	tm.RecordError("token1", 40101)
	assert.Equal(t, 2, tm.GetHealthyTokenCount())

	// 恢复健康状态
	tm.RecordSuccess("token1")
	assert.Equal(t, 3, tm.GetHealthyTokenCount())
}

func TestTokenManagerMaskToken(t *testing.T) {
	tokens := []string{"1234567890abcdef"}

	tm := NewTokenManager(tokens)
	masked := tm.maskToken("1234567890abcdef")
	assert.Equal(t, "1234****cdef", masked)

	// 测试短token
	masked = tm.maskToken("123")
	assert.Equal(t, "****", masked)
}

func TestTokenManagerLogStats(t *testing.T) {
	tokens := []string{"token1", "token2"}

	tm := NewTokenManager(tokens)

	// 添加一些统计数据
	tm.RecordSuccess("token1")
	tm.RecordError("token2", 40001)

	// 测试日志输出（这里只是确保不会panic）
	require.NotPanics(t, func() {
		tm.LogStats()
	})
}