package config

import (
	"fmt"
)

// 定义常见的错误类型
var (
	// ErrInvalidConfig 配置错误
	ErrInvalidConfig = fmt.Errorf("invalid configuration")

	// ErrDatabaseConnection 数据库连接错误
	ErrDatabaseConnection = fmt.Errorf("database connection failed")

	// ErrAPIRequest API请求错误
	ErrAPIRequest = fmt.Errorf("API request failed")

	// ErrDataValidation 数据验证错误
	ErrDataValidation = fmt.Errorf("data validation failed")

	// ErrRateLimit 频率限制错误
	ErrRateLimit = fmt.Errorf("rate limit exceeded")
)

// AppError 应用错误结构
type AppError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Detail  string `json:"detail,omitempty"`
}

// Error 实现error接口
func (e *AppError) Error() string {
	if e.Detail != "" {
		return fmt.Sprintf("[%d] %s: %s", e.Code, e.Message, e.Detail)
	}
	return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

// NewAppError 创建应用错误
func NewAppError(code int, message, detail string) *AppError {
	return &AppError{
		Code:    code,
		Message: message,
		Detail:  detail,
	}
}

// 常用错误代码
const (
	ErrCodeInvalidParam    = 1001
	ErrCodeDatabaseError   = 2001
	ErrCodeAPIError        = 3001
	ErrCodeValidationError = 4001
	ErrCodeRateLimitError  = 5001
)
