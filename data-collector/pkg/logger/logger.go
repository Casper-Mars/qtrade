package logger

import (
	"os"

	"github.com/sirupsen/logrus"
)

// 全局日志实例
var globalLogger *logrus.Logger

// InitLogger 初始化全局日志配置
func InitLogger(level, format, output string) {
	globalLogger = logrus.New()

	// 设置日志级别
	switch level {
	case "debug":
		globalLogger.SetLevel(logrus.DebugLevel)
	case "info":
		globalLogger.SetLevel(logrus.InfoLevel)
	case "warn":
		globalLogger.SetLevel(logrus.WarnLevel)
	case "error":
		globalLogger.SetLevel(logrus.ErrorLevel)
	default:
		globalLogger.SetLevel(logrus.InfoLevel)
	}

	// 设置日志格式
	switch format {
	case "json":
		globalLogger.SetFormatter(&logrus.JSONFormatter{
			TimestampFormat: "2006-01-02 15:04:05",
		})
	case "text":
		globalLogger.SetFormatter(&logrus.TextFormatter{
			FullTimestamp:   true,
			TimestampFormat: "2006-01-02 15:04:05",
		})
	default:
		globalLogger.SetFormatter(&logrus.JSONFormatter{
			TimestampFormat: "2006-01-02 15:04:05",
		})
	}

	// 设置输出目标
	switch output {
	case "stdout":
		globalLogger.SetOutput(os.Stdout)
	default:
		globalLogger.SetOutput(os.Stdout)
	}
}

// GetLogger 获取全局日志实例
func GetLogger() *logrus.Logger {
	if globalLogger == nil {
		InitLogger("info", "json", "stdout")
	}
	return globalLogger
}

// SetLogger 设置全局日志实例（用于依赖注入）
func SetLogger(logger *logrus.Logger) {
	globalLogger = logger
}

// 包级别的日志方法

// Debug 输出调试级别日志
func Debug(args ...interface{}) {
	GetLogger().Debug(args...)
}

// Debugf 输出格式化调试级别日志
func Debugf(format string, args ...interface{}) {
	GetLogger().Debugf(format, args...)
}

// Info 输出信息级别日志
func Info(args ...interface{}) {
	GetLogger().Info(args...)
}

// Infof 输出格式化信息级别日志
func Infof(format string, args ...interface{}) {
	GetLogger().Infof(format, args...)
}

// Warn 输出警告级别日志
func Warn(args ...interface{}) {
	GetLogger().Warn(args...)
}

// Warnf 输出格式化警告级别日志
func Warnf(format string, args ...interface{}) {
	GetLogger().Warnf(format, args...)
}

// Error 输出错误级别日志
func Error(args ...interface{}) {
	GetLogger().Error(args...)
}

// Errorf 输出格式化错误级别日志
func Errorf(format string, args ...interface{}) {
	GetLogger().Errorf(format, args...)
}

// Fatal 输出致命错误级别日志并退出程序
func Fatal(args ...interface{}) {
	GetLogger().Fatal(args...)
}

// Fatalf 输出格式化致命错误级别日志并退出程序
func Fatalf(format string, args ...interface{}) {
	GetLogger().Fatalf(format, args...)
}

// Panic 输出恐慌级别日志并触发panic
func Panic(args ...interface{}) {
	GetLogger().Panic(args...)
}

// Panicf 输出格式化恐慌级别日志并触发panic
func Panicf(format string, args ...interface{}) {
	GetLogger().Panicf(format, args...)
}

// WithField 添加单个字段
func WithField(key string, value interface{}) *logrus.Entry {
	return GetLogger().WithField(key, value)
}

// WithFields 添加多个字段
func WithFields(fields logrus.Fields) *logrus.Entry {
	return GetLogger().WithFields(fields)
}

// WithError 添加错误字段
func WithError(err error) *logrus.Entry {
	return GetLogger().WithError(err)
}