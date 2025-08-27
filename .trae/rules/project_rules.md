1. 这是一个纯后端的系统，使用微服务架构。
2. 所有的服务公用同一套基础设施，包括mysql数据、redis、MongoDB。
3. 系统的详细架构信息如下：```markdown
# 系统架构

## 系统工程目录说明

```
./qtrade/
├── docker/                    # docker 相关的文件，例如：docker-compose.yaml，用来在本地启动依赖的redis、mysql和MongoDB。
├── data-collector/            # 数据采集服务
├── quant-engine/              # 量化计算服务
├── ai-service/                # AI分析服务
├── bff-service/                # 业务聚合+API网关服务
├── docs/                      # 项目文档
```

## 服务列表

**bff-service (业务聚合+API网关)**
- **职责**：
  - API网关：统一入口
  - 业务编排：数据聚合、前端适配、业务逻辑编排

**data-collector (数据采集+存储)**
- **职责**：
  - 数据采集：多源数据采集、实时数据流、新闻采集
  - 数据存储：数据清洗、存储管理、缓存管理
  - 数据服务：提供数据访问API

**quant-engine (量化计算引擎)**
- **职责**：
  - 因子计算：技术指标、基本面因子、市场因子
  - 预测模型：机器学习训练、预测服务、模型管理
  - 回测引擎：策略回测、性能评估、参数优化

**ai-service (AI分析服务)**
- **职责**：
  - NLP分析：新闻情感分析、关键词提取、文本分类
  - 智能报告：投资报告生成、策略解释
  - LLM服务：大模型调用、智能问答

## 服务间通信设计

同步通信，使用HTTP协议。


## data-colletor 服务工程结构

### 项目目录结构

```
./data-collector/
├── cmd/                    # 应用程序入口
│   └── server/            # 服务器启动程序
├── internal/              # 内部包（不对外暴露）
│   ├── collectors/        # 数据采集模块
│   │   ├── stock/         # 股票数据采集器
│   │   ├── financial/     # 财务数据采集器
│   │   ├── market/        # 市场数据采集器
│   │   ├── news/          # 新闻数据采集器
│   │   └── policy/        # 政策数据采集器
│   ├── cleaners/          # 数据清洗模块
│   │   ├── stock/         # 股票数据清洗器
│   │   ├── financial/     # 财务数据清洗器
│   │   ├── news/          # 新闻数据清洗器
│   │   └── policy/        # 政策数据清洗器
│   ├── storage/           # 数据存储模块
│   │   ├── mysql/         # MySQL适配器
│   │   ├── mongodb/       # MongoDB适配器
│   │   └── redis/         # Redis适配器
│   ├── services/          # 业务服务模块
│   │   ├── news/          # 新闻服务编排
│   │   ├── stock/         # 股票服务编排
│   │   └── financial/     # 财务服务编排
│   ├── api/               # API服务模块
│   │   ├── handler/       # HTTP处理器
│   │   └── middleware/    # 中间件
│   ├── scheduler/         # 任务调度模块
│   ├── models/            # 数据模型
│   ├── config/            # 配置管理
│   └── common/            # 通用组件
│       ├── http/          # HTTP客户端
│       ├── validator/     # 数据验证器
│       └── logger/        # 日志组件
├── pkg/                   # 公共包（可对外暴露）
│   ├── client/            # 客户端SDK
│   └── types/             # 公共类型定义
├── configs/               # 配置文件
├── scripts/               # 脚本文件
├── docs/                  # 文档
├── test/                  # 测试文件
│   ├── integration/       # 集成测试
│   └── unit/              # 单元测试
├── go.mod                 # Go模块文件
├── go.sum                 # Go依赖校验文件
├── Dockerfile             # Docker构建文件
├── docker-compose.yml     # 本地开发环境
└── README.md              # 项目说明
```

### 目录职责说明

**cmd/**: 应用程序入口点，包含main函数和启动逻辑
**internal/**: 内部业务逻辑，不对外暴露
- **collectors/**: 数据采集模块，按数据类型分包
- **cleaners/**: 数据清洗模块，对应采集器进行清洗
- **storage/**: 数据存储模块，封装不同存储引擎
- **services/**: 业务服务模块，负责业务编排和服务集成
- **api/**: HTTP API服务，提供RESTful接口
- **scheduler/**: 任务调度模块，管理定时任务
- **models/**: 数据模型定义，统一数据结构
- **config/**: 配置管理，支持多环境配置
- **common/**: 通用组件，可被多个模块复用

**pkg/**: 公共包，可被其他服务引用
**configs/**: 配置文件存放目录
**scripts/**: 构建、部署等脚本
**docs/**: 项目文档
**test/**: 测试代码，分为单元测试和集成测试




```