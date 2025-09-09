# 任务管理器模块 - 任务拆分文档

## 项目类型：现有项目（基于quant-engine服务扩展）

## 核心业务功能任务（按功能点拆分）

### 模块A：任务管理核心

#### 功能点A1：数据模型定义
- [ ] 任务M001. 实现任务管理数据模型（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as API层
        participant Model as 数据模型
        participant Validator as 验证器
        
        Client->>API: 提交任务创建请求
        API->>Model: 创建TaskRequest实例
        Model->>Validator: 验证任务参数
        Validator->>Validator: 检查配置有效性
        Validator-->>Model: 返回验证结果
        Model-->>API: 返回任务对象
        API-->>Client: 返回任务确认
    ```
  - 实现TaskRequest数据模型（参考design_backend.md第2.3.3节）
    * 定义任务ID、批次ID（用于分组查询）、股票代码等基础字段
    * 实现任务配置和参数结构
    * 添加任务创建时间、开始时间、结束时间字段
    * 实现任务序列化和反序列化方法
  - 实现TaskInfo数据模型（参考design_backend.md第2.3.3节）
    * 定义任务ID、状态、进度等核心字段
    * 实现任务配置和结果数据结构
    * 添加批次ID字段用于分组查询
    * 实现任务状态转换功能
  - 实现TaskStatus枚举（参考design_backend.md第2.3.3节）
    * 定义任务状态（排队中、执行中、已完成、已失败、已取消）
    * 实现状态转换规则和验证逻辑
    * 添加状态描述和错误信息字段
  - _Requirements: 任务管理、状态跟踪、数据验证_
  - _Design Reference: design_backend.md 第2.3.3节_
  - _前置条件：无_
  - _集成测试点：数据模型创建测试、状态转换测试、验证逻辑测试_

#### 功能点A2：任务管理器实现
- [ ] 任务M002. 实现任务管理器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant API as API接口
        participant TM as TaskManager
        participant DB as 数据库
        
        API->>TM: create_task(request)
        TM->>TM: 生成任务ID和批次ID
        TM->>TM: 基本参数验证
        TM->>DB: 保存任务信息
        TM-->>API: 返回任务创建结果
        
        API->>TM: get_task_status(task_id)
        TM->>DB: 查询任务状态
        TM-->>API: 返回状态信息
    ```
  - 实现TaskManager类（参考design_backend.md第2.3.1节）
    * 实现create_task、get_task_status、cancel_task方法
    * 添加基本的参数验证功能
    * 实现简单的任务状态跟踪
    * 添加按批次ID查询任务列表功能
  - 实现任务创建流程（参考design_backend.md第2.3.4节）
    * 验证任务请求的基本参数
    * 生成唯一的任务ID和批次ID（用于分组）
    * 保存任务信息到数据库（状态为pending）
    * 返回任务创建结果
  - 实现任务查询功能（参考design_backend.md第2.3.1节）
    * 支持按任务ID查询单个任务状态
    * 支持按批次ID查询该批次所有任务
    * 实现基本的任务列表过滤
    * 添加任务结果查询功能
  - _Requirements: 任务管理、状态跟踪、查询功能_
  - _Design Reference: design_backend.md 第2.3.1节、第2.3.4节_
  - _前置条件：任务M001完成_
  - _集成测试点：任务创建测试、状态管理测试、查询功能测试_

#### 功能点A3：任务调度器实现
- [ ] 任务M003. 实现任务调度器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Timer as 定时器
        participant TS as TaskScheduler
        participant DAO as TaskDAO
        participant BE as BacktestEngine
        
        Timer->>TS: 每30秒触发一次
        TS->>DAO: 查询待执行任务
        DAO-->>TS: 返回pending状态任务列表
        loop 处理每个任务
            TS->>DAO: 更新任务状态为running
            TS->>BE: 执行回测任务
            BE-->>TS: 返回执行结果
            TS->>DAO: 更新任务状态为completed/failed
        end
    ```
  - 实现TaskScheduler类（参考design_backend.md第2.3.1节）
    * 实现定时器机制，每30秒检查一次数据库
    * 查询状态为pending的任务
    * 逐个处理任务，更新状态
    * 添加基本的异常处理
  - 实现简单调度逻辑（参考design_backend.md第2.3.1节）
    * 按创建时间顺序处理任务（FIFO）
    * 一次处理一个任务，避免并发复杂性
    * 实现任务状态的及时更新
    * 添加任务执行超时检测
  - 实现定时任务管理（参考design_backend.md第2.3.1节）
    * 使用Python的schedule库或asyncio定时器
    * 实现调度器的启动和停止
    * 添加调度器运行状态监控
    * 实现简单的错误重试机制
  - _Requirements: 定时调度、状态更新、异常处理_
  - _Design Reference: design_backend.md 第2.3.1节_
  - _前置条件：任务M001、M002完成_
  - _集成测试点：定时调度测试、任务执行测试、状态更新测试_

### 模块B：数据存储层

#### 功能点B1：任务数据访问层实现
- [ ] 任务M004. 实现任务数据访问层（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant TM as TaskManager
        participant DAO as TaskDAO
        participant DB as MySQL数据库
        
        TM->>DAO: save_task(task_info)
        DAO->>DB: 插入任务记录
        DB-->>DAO: 返回插入结果
        DAO-->>TM: 返回保存确认
        
        TM->>DAO: get_task(task_id)
        DAO->>DB: 查询数据库
        DB-->>DAO: 返回任务数据
        DAO-->>TM: 返回任务信息
    ```
  - 实现TaskDAO类（参考design_backend.md第3.2节）
    * 实现任务数据的CRUD操作
    * 添加批量数据操作和事务处理
    * 实现数据库连接池管理
    * 添加基础的数据访问监控
  - 创建数据库表结构（参考design_backend.md第3.2节）
    * 创建backtest_tasks表存储任务详情
    * 添加批次ID字段用于分组查询
    * 添加必要的索引和约束
    * 实现数据库迁移脚本
  - 实现查询功能（参考design_backend.md第3.2节）
    * 实现按任务ID查询单个任务
    * 实现按批次ID查询任务列表
    * 添加任务状态过滤功能
    * 实现分页查询支持
  - _Requirements: 数据持久化、查询功能、性能优化_
  - _Design Reference: design_backend.md 第3.2节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据库操作测试、查询功能测试、性能测试_

### 模块C：HTTP API接口层

#### 功能点C1：任务管理API实现
- [ ] 任务M005. 实现任务管理API（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as TaskAPI
        participant TM as TaskManager
        participant Validator as 参数验证器
        
        Client->>API: POST /api/v1/backtest/createTask
        API->>Validator: 验证请求参数
        Validator-->>API: 返回验证结果
        API->>TM: create_task(request)
        TM-->>API: 返回任务信息
        API-->>Client: 返回任务创建结果
        
        Client->>API: GET /api/v1/backtest/getTaskStatus
        API->>TM: get_task_status(task_id)
        TM-->>API: 返回状态信息
        API-->>Client: 返回状态查询结果
    ```
  - 实现任务创建API（参考design_backend.md第2.3.5节）
    * 实现POST /api/v1/backtest/createTask接口
    * 添加请求参数验证和错误处理
    * 实现任务配置的格式化和响应封装
    * 支持批量创建多个股票的任务
  - 实现任务状态查询API（参考design_backend.md第2.3.5节）
    * 实现GET /api/v1/backtest/getTaskStatus接口
    * 支持单个任务状态查询
    * 实现GET /api/v1/backtest/getTasksByBatch接口
    * 支持按批次ID查询该批次所有任务状态
  - 实现任务控制API（参考design_backend.md第2.3.5节）
    * 实现POST /api/v1/backtest/cancelTask接口
    * 支持取消单个任务
    * 实现GET /api/v1/backtest/getTaskResult接口
    * 支持查询任务执行结果
  - _Requirements: RESTful API、参数验证、批次查询_
  - _Design Reference: design_backend.md 第2.3.5节_
  - _前置条件：任务M002完成_
  - _集成测试点：API接口测试、参数验证测试、批次查询测试_



## 任务执行顺序说明

**第一阶段：基础数据模型（优先级最高）**
- 任务M001：数据模型定义是所有功能的基础

**第二阶段：核心组件实现（按依赖关系执行）**
- 任务M004：任务数据访问层（依赖M001）
- 任务M002：任务管理器（依赖M001、M004）
- 任务M003：任务调度器（依赖M001、M002）

**第三阶段：API接口层（最后执行）**
- 任务M005：任务管理API（依赖M002、M003）

## 验收标准

**功能验收：**
- [ ] 支持回测任务的创建和管理
- [ ] 实现任务状态的查询和跟踪
- [ ] 支持基本的任务调度和执行
- [ ] 提供基础的RESTful API接口
- [ ] 支持按批次ID查询任务列表

**性能验收：**
- [ ] 任务创建响应时间在1秒以内
- [ ] 任务状态查询响应时间在500ms以内
- [ ] 支持基本的并发任务处理
- [ ] 数据库操作正常稳定

**质量验收：**
- [ ] 通过基本功能测试，无关键缺陷
- [ ] 符合现有代码规范
- [ ] 核心功能稳定可用