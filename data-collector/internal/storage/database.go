package storage

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"data-collector/internal/config"
	"data-collector/pkg/logger"

	"github.com/go-redis/redis/v8"
	_ "github.com/go-sql-driver/mysql"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// DatabaseManager 数据库管理器
type DatabaseManager struct {
	MySQL   *sql.DB
	MongoDB *mongo.Client
	Redis   *redis.Client
	config  *config.Config
}

// NewDatabaseManager 创建数据库管理器
func NewDatabaseManager(cfg *config.Config) *DatabaseManager {
	return &DatabaseManager{
		config: cfg,
	}
}

// InitMySQL 初始化MySQL连接
func (dm *DatabaseManager) InitMySQL() error {
	mysqlCfg := dm.config.Database.MySQL
	dsn := mysqlCfg.GetDSN()

	// 创建数据库连接
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return fmt.Errorf("failed to open mysql connection: %w", err)
	}

	// 配置连接池参数
	db.SetMaxOpenConns(mysqlCfg.MaxOpenConns)
	db.SetMaxIdleConns(mysqlCfg.MaxIdleConns)
	db.SetConnMaxLifetime(mysqlCfg.ConnMaxLifetime)

	// 测试连接
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		return fmt.Errorf("failed to ping mysql: %w", err)
	}

	dm.MySQL = db
	logger.Info("MySQL connection initialized successfully")
	return nil
}

// InitMongoDB 初始化MongoDB连接
func (dm *DatabaseManager) InitMongoDB() error {
	mongoCfg := dm.config.Database.MongoDB

	// 创建客户端选项
	clientOptions := options.Client().ApplyURI(mongoCfg.URI)
	clientOptions.SetConnectTimeout(mongoCfg.Timeout)
	clientOptions.SetServerSelectionTimeout(mongoCfg.Timeout)

	// 创建MongoDB客户端
	ctx, cancel := context.WithTimeout(context.Background(), mongoCfg.Timeout)
	defer cancel()

	client, err := mongo.Connect(ctx, clientOptions)
	if err != nil {
		return fmt.Errorf("failed to connect to mongodb: %w", err)
	}

	// 测试连接
	if err := client.Ping(ctx, nil); err != nil {
		return fmt.Errorf("failed to ping mongodb: %w", err)
	}

	dm.MongoDB = client
	logger.Info("MongoDB connection initialized successfully")
	return nil
}

// InitRedis 初始化Redis连接
func (dm *DatabaseManager) InitRedis() error {
	redisCfg := dm.config.Database.Redis

	// 创建Redis客户端
	rdb := redis.NewClient(&redis.Options{
		Addr:         redisCfg.Addr,
		Password:     redisCfg.Password,
		DB:           redisCfg.DB,
		PoolSize:     redisCfg.PoolSize,
		MinIdleConns: redisCfg.MinIdleConns,
		DialTimeout:  redisCfg.DialTimeout,
		ReadTimeout:  redisCfg.ReadTimeout,
		WriteTimeout: redisCfg.WriteTimeout,
		PoolTimeout:  redisCfg.PoolTimeout,
		IdleTimeout:  redisCfg.IdleTimeout,
	})

	// 测试连接
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := rdb.Ping(ctx).Err(); err != nil {
		return fmt.Errorf("failed to ping redis: %w", err)
	}

	dm.Redis = rdb
	logger.Info("Redis connection initialized successfully")
	return nil
}

// InitAll 初始化所有数据库连接
func (dm *DatabaseManager) InitAll() error {
	// 初始化MySQL
	if err := dm.InitMySQL(); err != nil {
		return fmt.Errorf("mysql initialization failed: %w", err)
	}

	// 初始化MongoDB
	if err := dm.InitMongoDB(); err != nil {
		return fmt.Errorf("mongodb initialization failed: %w", err)
	}

	// 初始化Redis
	if err := dm.InitRedis(); err != nil {
		return fmt.Errorf("redis initialization failed: %w", err)
	}

	logger.Info("All database connections initialized successfully")
	return nil
}

// HealthCheck 数据库健康检查
func (dm *DatabaseManager) HealthCheck() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 检查MySQL连接
	if dm.MySQL != nil {
		if err := dm.MySQL.PingContext(ctx); err != nil {
			return fmt.Errorf("mysql health check failed: %w", err)
		}
	}

	// 检查MongoDB连接
	if dm.MongoDB != nil {
		if err := dm.MongoDB.Ping(ctx, nil); err != nil {
			return fmt.Errorf("mongodb health check failed: %w", err)
		}
	}

	// 检查Redis连接
	if dm.Redis != nil {
		if err := dm.Redis.Ping(ctx).Err(); err != nil {
			return fmt.Errorf("redis health check failed: %w", err)
		}
	}

	return nil
}

// Close 关闭所有数据库连接
func (dm *DatabaseManager) Close() error {
	var errors []error

	// 关闭MySQL连接
	if dm.MySQL != nil {
		if err := dm.MySQL.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close mysql: %w", err))
		} else {
			logger.Info("MySQL connection closed")
		}
	}

	// 关闭MongoDB连接
	if dm.MongoDB != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := dm.MongoDB.Disconnect(ctx); err != nil {
			errors = append(errors, fmt.Errorf("failed to close mongodb: %w", err))
		} else {
			logger.Info("MongoDB connection closed")
		}
	}

	// 关闭Redis连接
	if dm.Redis != nil {
		if err := dm.Redis.Close(); err != nil {
			errors = append(errors, fmt.Errorf("failed to close redis: %w", err))
		} else {
			logger.Info("Redis connection closed")
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("errors occurred while closing databases: %v", errors)
	}

	logger.Info("All database connections closed successfully")
	return nil
}

// GetMySQL 获取MySQL连接
func (dm *DatabaseManager) GetMySQL() *sql.DB {
	return dm.MySQL
}

// GetMongoDB 获取MongoDB客户端
func (dm *DatabaseManager) GetMongoDB() *mongo.Client {
	return dm.MongoDB
}

// GetMongoDatabase 获取MongoDB数据库
func (dm *DatabaseManager) GetMongoDatabase() *mongo.Database {
	if dm.MongoDB == nil {
		return nil
	}
	return dm.MongoDB.Database(dm.config.Database.MongoDB.Database)
}

// GetRedis 获取Redis客户端
func (dm *DatabaseManager) GetRedis() *redis.Client {
	return dm.Redis
}