package storage

import (
	"database/sql"
	"sync"

	"data-collector/internal/config"

	"github.com/go-redis/redis/v8"
	"go.mongodb.org/mongo-driver/mongo"
)

// 全局数据库管理器实例
var (
	dbManager *DatabaseManager
	once      sync.Once
)

// InitGlobalDatabaseManager 初始化全局数据库管理器
func InitGlobalDatabaseManager(cfg *config.Config) error {
	var err error
	once.Do(func() {
		dbManager = NewDatabaseManager(cfg)
		err = dbManager.InitAll()
	})
	return err
}

// GetGlobalDatabaseManager 获取全局数据库管理器
func GetGlobalDatabaseManager() *DatabaseManager {
	return dbManager
}

// CloseGlobalDatabaseManager 关闭全局数据库管理器
func CloseGlobalDatabaseManager() error {
	if dbManager != nil {
		return dbManager.Close()
	}
	return nil
}

// GetMySQL 获取MySQL连接的便捷方法
func GetMySQL() *sql.DB {
	if dbManager != nil {
		return dbManager.GetMySQL()
	}
	return nil
}

// GetMongoDB 获取MongoDB客户端的便捷方法
func GetMongoDB() *mongo.Client {
	if dbManager != nil {
		return dbManager.GetMongoDB()
	}
	return nil
}

// GetMongoDatabase 获取MongoDB数据库的便捷方法
func GetMongoDatabase() *mongo.Database {
	if dbManager != nil {
		return dbManager.GetMongoDatabase()
	}
	return nil
}

// GetRedis 获取Redis客户端的便捷方法
func GetRedis() *redis.Client {
	if dbManager != nil {
		return dbManager.GetRedis()
	}
	return nil
}

// HealthCheck 数据库健康检查的便捷方法
func HealthCheck() error {
	if dbManager != nil {
		return dbManager.HealthCheck()
	}
	return nil
}