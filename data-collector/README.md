# Data Collector Service

数据采集服务是量化交易系统的核心组件，负责从多个数据源采集股票、财务、新闻和政策数据。

## 功能特性

- **股票数据采集**: 支持A股基础信息、行情数据、复权因子采集
- **财务数据采集**: 支持财务报表和财务指标数据采集
- **新闻数据采集**: 支持财经新闻和快讯采集
- **政策数据采集**: 支持监管政策和央行政策采集
- **数据清洗**: 提供数据验证、去重、标准化功能
- **任务调度**: 支持定时任务和增量更新
- **API服务**: 提供RESTful API接口

## 技术架构

- **开发语言**: Go 1.21+
- **Web框架**: Gin
- **数据库**: MySQL 8.0, MongoDB 7.0, Redis 7.0
- **任务调度**: Cron
- **数据采集**: Colly爬虫框架, Tushare API
- **配置管理**: Viper
- **日志**: Logrus

## 项目结构

```
data-collector/
├── cmd/                    # 应用程序入口
│   └── main.go            # 主程序
├── internal/              # 内部包（不对外暴露）
│   ├── config/            # 配置管理
│   ├── models/            # 数据模型
│   ├── collectors/        # 数据采集模块
│   ├── cleaners/          # 数据清洗模块
│   ├── storage/           # 数据存储模块
│   ├── api/               # API服务模块
│   └── scheduler/         # 任务调度模块
├── pkg/                   # 公共包（可对外暴露）
├── configs/               # 配置文件
├── scripts/               # 脚本文件
├── go.mod                 # Go模块文件
└── README.md              # 项目说明
```

## 快速开始

### 环境要求

- Go 1.21+
- MySQL 8.0+
- MongoDB 7.0+
- Redis 7.0+

### 安装依赖

```bash
go mod tidy
```

### 配置文件

复制配置模板并修改相应参数：

```bash
cp configs/config.yaml configs/config.local.yaml
# 编辑 configs/config.local.yaml 文件
```

### 启动服务

```bash
go run cmd/main.go
```

## API文档

### 健康检查

```
GET /health
```

### 股票数据接口

```
GET /api/v1/stocks                    # 获取股票列表
GET /api/v1/stocks/info               # 获取股票基本信息
GET /api/v1/stocks/quotes             # 获取股票行情数据
GET /api/v1/stocks/adj-factors        # 获取股票复权因子
POST /api/v1/stocks/init              # 全量股票基本数据初始化
```

### 财务数据接口

```
GET /api/v1/financial/reports         # 获取财务报表
GET /api/v1/financial/indicators      # 获取财务指标
```

### 新闻数据接口

```
GET /api/v1/news                      # 获取新闻列表
GET /api/v1/news/detail               # 获取新闻详情
```

### 政策数据接口

```
GET /api/v1/policies                  # 获取政策列表
```

## 开发指南

### 代码规范

- 遵循Go官方编码规范
- 使用gofmt格式化代码
- 添加必要的注释和文档
- 编写单元测试

### 测试

```bash
# 运行所有测试
go test ./...

# 运行测试并生成覆盖率报告
go test -cover ./...
```

### 构建

```bash
# 构建二进制文件
go build -o bin/data-collector cmd/main.go
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t data-collector .

# 运行容器
docker run -d --name data-collector -p 8080:8080 data-collector
```

## 监控和日志

- 日志文件位置: `./logs/data-collector.log`
- 健康检查端点: `GET /health`
- 指标监控端点: `GET /metrics`

## 许可证

本项目仅用于学术研究目的，不得用于商业用途。