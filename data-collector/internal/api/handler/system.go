package handler

import (
	"net/http"
	"runtime"
	"time"

	"data-collector/internal/storage"

	"github.com/gin-gonic/gin"
)

// SystemHandler 系统级处理器
type SystemHandler struct {
	version   string
	buildTime string
}

// NewSystemHandler 创建系统处理器
func NewSystemHandler(version, buildTime string) *SystemHandler {
	return &SystemHandler{
		version:   version,
		buildTime: buildTime,
	}
}

// Health 健康检查接口
func (h *SystemHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "ok",
		"timestamp": time.Now().Unix(),
		"service":   "data-collector",
	})
}

// Version 版本信息接口
func (h *SystemHandler) Version(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"version":    h.version,
		"build_time": h.buildTime,
		"go_version": runtime.Version(),
		"service":    "data-collector",
	})
}

// Metrics 系统指标接口
func (h *SystemHandler) Metrics(c *gin.Context) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	c.JSON(http.StatusOK, gin.H{
		"memory": gin.H{
			"alloc":       m.Alloc,
			"total_alloc": m.TotalAlloc,
			"sys":         m.Sys,
			"num_gc":      m.NumGC,
		},
		"goroutines": runtime.NumGoroutine(),
		"timestamp":  time.Now().Unix(),
	})
}

// DatabaseHealth 数据库健康检查接口
func (h *SystemHandler) DatabaseHealth(c *gin.Context) {
	err := storage.HealthCheck()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status":    "error",
			"message":   "Database health check failed",
			"error":     err.Error(),
			"timestamp": time.Now().Unix(),
			"service":   "data-collector",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status":    "ok",
		"message":   "All database connections are healthy",
		"timestamp": time.Now().Unix(),
		"service":   "data-collector",
	})
}
