// @title Data Collector API
// @version 1.0
// @description 数据采集服务API文档，提供股票、财务、新闻和政策数据采集功能
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @host localhost:8080
// @BasePath /api/v1
// @schemes http https

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"data-collector/internal/api"
	"data-collector/internal/config"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"
	_ "data-collector/docs" // 导入生成的docs包
)

func main() {
	log.Println("Data Collector Service Starting...")

	// 加载配置
	cfg, err := config.LoadConfig("configs/config.yaml")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// 初始化日志
	logger.InitLogger(cfg.Log.Level, cfg.Log.Format, cfg.Log.Output)

	// 初始化数据库连接
	if err := storage.InitGlobalDatabaseManager(cfg); err != nil {
		logger.Fatal("Failed to initialize database connections: ", err)
	}

	// 创建路由
	router := api.NewRouter()

	// 设置中间件
	router.SetupMiddleware()

	// 设置路由
	router.SetupRoutes()

	// 创建HTTP服务器
	server := &http.Server{
		Addr:    fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler: router.GetEngine(),
		ReadTimeout:  time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.Server.WriteTimeout) * time.Second,
		IdleTimeout:  time.Duration(cfg.Server.IdleTimeout) * time.Second,
	}

	// 启动服务器
	go func() {
		logger.Infof("Server starting on %s", server.Addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("Server failed to start: %v", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// 优雅关闭
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 关闭数据库连接
	if err := storage.CloseGlobalDatabaseManager(); err != nil {
		logger.Errorf("Failed to close database connections: %v", err)
	}

	if err := server.Shutdown(ctx); err != nil {
		logger.Fatalf("Server forced to shutdown: %v", err)
	}

	logger.Info("Server exited")
}
