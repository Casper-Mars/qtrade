package middleware

import (
	"net/http"
	"runtime/debug"

	"github.com/gin-gonic/gin"
	"data-collector/pkg/logger"
)

// RecoveryMiddleware 异常捕获中间件
func RecoveryMiddleware() gin.HandlerFunc {
	return gin.CustomRecovery(func(c *gin.Context, recovered interface{}) {
		// 记录panic信息
		logger.WithFields(map[string]interface{}{
			"panic":      recovered,
			"stack":      string(debug.Stack()),
			"path":       c.Request.URL.Path,
			"method":     c.Request.Method,
			"client_ip":  c.ClientIP(),
			"user_agent": c.Request.UserAgent(),
		}).Error("Panic recovered")

		// 返回统一的错误响应
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "Internal server error",
			"data":    nil,
		})
	})
}
