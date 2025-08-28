# 因子计算引擎开发任务文档

## 项目类型：现有项目（基于现有quant-engine服务扩展）

### 项目概述
本项目基于现有的quant-engine服务，实现因子计算引擎功能。quant-engine服务已有基础Python框架，需要在此基础上构建完整的因子计算体系，包括技术因子、基本面因子、市场因子和新闻情绪因子的计算功能。

### 技术栈
- **开发语言**: Python 3.11+
- **Web框架**: FastAPI
- **数据处理**: Pandas、NumPy
- **NLP处理**: transformers、torch（FinBERT）
- **数据库**: MySQL（因子数据存储）+ Redis（缓存）
- **HTTP客户端**: httpx
- **任务调度**: APScheduler

## 第一阶段：基础设施任务（优先级最高，其他任务的前置条件）

### 任务I001. 项目基础架构完善 ✅
- **实现内容**：
  - 完善quant-engine服务的基础架构配置（参考design_backend.md第1.4节）
  - 配置FastAPI应用实例和全局中间件（参考design_backend.md第1.3节）
  - 实现与data-collector服务的HTTP客户端（参考design_backend.md第1.1节）
  - 配置MySQL和Redis连接池（参考design_backend.md第1.4节和第3.1节）
  - 设置全局日志记录和异常处理机制（参考design_backend.md第5.2节）
  - 配置项目依赖管理和开发环境
- **实现边界**：仅搭建服务基础架构，不涉及任何业务逻辑或业务路由
- **禁止内容**：因子计算、数据处理等任何业务相关的实现
- _Requirements: 系统架构需求_
- _Design Reference: design_backend.md 第1.1-1.4节、第6.1节_
- _前置条件：无_
- _后续依赖：所有业务功能任务_
- **状态**：已完成

## 第二阶段：数据模型任务（业务功能的基础）

### 任务D001. 因子数据模型设计与实现 ✅
- **实现内容**：
  - 根据design_backend.md第3.2节设计因子数据表结构
  - 实现因子相关的数据库模型和Pydantic模型（参考design_backend.md第2.1.5节）
  - 创建数据库迁移脚本和索引策略（参考design_backend.md第3.2节和第3.3节）
  - 实现因子数据访问层基础类（参考design_backend.md第2.1.6节）
  - 配置Redis缓存策略和数据结构
- **数据表设计**：
  - technical_factors：技术因子数据表
  - fundamental_factors：基本面因子数据表
  - market_factors：市场因子数据表
  - sentiment_factors：情绪因子数据表
- **实现边界**：仅实现数据模型定义和数据库表结构，不包含业务逻辑处理
- _Requirements: 数据存储需求_
- _Design Reference: design_backend.md 第4.2-4.3节、第2.1.5-2.1.6节_
- _前置条件：任务I001完成_
- _后续依赖：所有因子计算功能_

## 第三阶段：核心业务功能任务（按模块和功能点拆分）

### 模块A：技术因子计算模块

#### 功能点A1：技术因子计算功能
- [x] **任务M001. 实现技术因子计算功能（完整端到端实现）**
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as 技术因子API
        participant Service as 因子服务
        participant Calculator as 技术因子计算器
        participant DataClient as 数据客户端
        participant DAO as 数据访问层
        participant Cache as Redis缓存
        participant DB as MySQL数据库
        
        Client->>API: POST /api/v1/technical/calculate
        API->>API: 参数验证
        API->>Service: 调用因子计算服务
        
        Service->>Cache: 检查缓存
        alt 缓存命中
            Cache-->>Service: 返回缓存结果
            Service-->>API: 返回计算结果
        else 缓存未命中
            Service->>Calculator: 执行因子计算
            Calculator->>DataClient: 获取股票行情数据
            DataClient->>DataClient: 调用data-collector API
            DataClient-->>Calculator: 返回行情数据
            Calculator->>Calculator: 执行技术指标计算
            Calculator-->>Service: 返回计算结果
            
            Service->>DAO: 保存计算结果
            DAO->>DB: 持久化到数据库
            DAO->>Cache: 更新缓存
            
            Service-->>API: 返回计算结果
        end
        
        API-->>Client: 响应计算结果
    ```
  - **实现步骤**：
    1. 实现技术因子API接口层（参考design_backend.md第2.1.3节）
       * 路由定义：POST /api/v1/technical/calculate
       * GET /api/v1/technical/history（历史查询）
       * 请求参数验证和错误处理
    2. 实现技术因子计算器（参考design_backend.md第2.1.4节）
       * MA（移动平均线）计算算法
       * RSI（相对强弱指标）计算算法
       * MACD（指数平滑移动平均线）计算算法
       * 布林带（Bollinger Bands）计算算法
    3. 实现因子服务层（参考design_backend.md第2.1.2节）
       * 统一因子计算服务接口
       * 缓存策略和数据持久化逻辑
       * 批量计算和并发处理
    4. 实现数据访问层（参考design_backend.md第2.1.6节）
       * 因子数据的CRUD操作
       * Redis缓存操作和失效策略
       * 数据库事务处理和错误回滚
  - _Requirements: 技术因子计算需求_
  - _Design Reference: design_backend.md 第2.1节_
  - _前置条件：任务I001、任务D001完成_
  - _集成测试点：API调用测试、数据库数据验证、缓存功能测试、计算准确性验证_

### 模块B：基本面因子计算模块

#### 功能点B1：基本面因子计算功能
- [x] **任务M002. 实现基本面因子计算功能（完整端到端实现）**
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as 基本面因子API
        participant Service as 因子服务
        participant Calculator as 基本面因子计算器
        participant DataClient as 数据客户端
        participant DAO as 数据访问层
        participant Cache as Redis缓存
        participant DB as MySQL数据库
        
        Client->>API: POST /api/v1/fundamental/calculate
        API->>API: 参数验证
        API->>Service: 调用因子计算服务
        
        Service->>Cache: 检查缓存
        alt 缓存命中
            Cache-->>Service: 返回缓存结果
            Service-->>API: 返回计算结果
        else 缓存未命中
            Service->>Calculator: 执行因子计算
            Calculator->>DataClient: 获取财务报表数据
            DataClient->>DataClient: 调用data-collector API
            DataClient-->>Calculator: 返回财务数据
            Calculator->>Calculator: 执行财务指标计算
            Calculator-->>Service: 返回计算结果
            
            Service->>DAO: 保存计算结果
            DAO->>DB: 持久化到数据库
            DAO->>Cache: 更新缓存
            
            Service-->>API: 返回计算结果
        end
        
        API-->>Client: 响应计算结果
    ```
  - **实现步骤**：
    1. 实现基本面因子API接口层（参考design_backend.md第2.2.3节）
       * 路由定义：POST /api/v1/fundamental/calculate
       * GET /api/v1/fundamental/history（历史查询）
       * 支持季度和年度数据查询
    2. 实现基本面因子计算器（参考design_backend.md第2.2.4节）
       * ROE（净资产收益率）计算
       * ROA（总资产收益率）计算
       * 毛利率、净利率计算
       * 资产负债率、流动比率计算
       * 同比和环比增长率计算
    3. 实现财务数据处理逻辑
       * 财务报表数据获取和预处理
       * 数据质量检查和异常处理
       * 多期数据对比分析
    4. 集成数据访问层和缓存策略
       * 基本面因子数据存储
       * 财务数据缓存优化
  - _Requirements: 基本面因子计算需求_
  - _Design Reference: design_backend.md 第2.2节_
  - _前置条件：任务I001、任务D001、任务M001完成_
  - _集成测试点：财务数据获取测试、因子计算准确性验证、历史数据查询测试_

### 模块C：市场因子计算模块

#### 功能点C1：市场因子计算功能
- [x] **任务M003. 实现市场因子计算功能（完整端到端实现）**
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as 市场因子API
        participant Service as 因子服务
        participant Calculator as 市场因子计算器
        participant DataClient as 数据客户端
        participant DAO as 数据访问层
        participant Cache as Redis缓存
        participant DB as MySQL数据库
        
        Client->>API: POST /api/v1/market/calculate
        API->>API: 参数验证
        API->>Service: 调用因子计算服务
        
        Service->>Cache: 检查缓存
        alt 缓存命中
            Cache-->>Service: 返回缓存结果
            Service-->>API: 返回计算结果
        else 缓存未命中
            Service->>Calculator: 执行因子计算
            Calculator->>DataClient: 获取市场数据
            DataClient->>DataClient: 调用data-collector API
            DataClient-->>Calculator: 返回市场数据
            Calculator->>Calculator: 执行市场因子计算
            Calculator-->>Service: 返回计算结果
            
            Service->>DAO: 保存计算结果
            DAO->>DB: 持久化到数据库
            DAO->>Cache: 更新缓存
            
            Service-->>API: 返回计算结果
        end
        
        API-->>Client: 响应计算结果
    ```
  - **实现步骤**：
    1. 实现市场因子API接口层（参考design_backend.md第2.3.3节）
       * 路由定义：POST /api/v1/market/calculate
       * GET /api/v1/market/history（历史查询）
       * 支持实时和历史数据查询
    2. 实现市场因子计算器（参考design_backend.md第2.3.4节）
       * 市值因子计算（总市值、流通市值）
       * 换手率因子计算
       * 成交量因子计算
       * 价格动量因子计算
       * 波动率因子计算
    3. 实现市场数据处理逻辑
       * 实时行情数据获取和处理
       * 历史数据回溯计算
       * 数据异常检测和处理
    4. 集成数据访问层和实时更新机制
       * 市场因子数据存储
       * 实时数据缓存策略
  - _Requirements: 市场因子计算需求_
  - _Design Reference: design_backend.md 第2.3节_
  - _前置条件：任务I001、任务D001、任务M001完成_
  - _集成测试点：实时数据获取测试、因子计算准确性验证、数据更新机制测试_

### 模块D：新闻情绪因子计算模块

#### 功能点D1：新闻情绪因子计算功能
- [x] **任务M004. 实现新闻情绪因子计算功能（完整端到端实现）**
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as 情绪因子API
        participant Service as 因子服务
        participant Calculator as 情绪因子计算器
        participant NLP as NLP模块
        participant DataClient as 数据客户端
        participant DAO as 数据访问层
        participant Cache as Redis缓存
        participant DB as MySQL数据库
        
        Client->>API: POST /api/v1/sentiment/calculate
        API->>API: 参数验证
        API->>Service: 调用因子计算服务
        
        Service->>Cache: 检查缓存
        alt 缓存命中
            Cache-->>Service: 返回缓存结果
            Service-->>API: 返回计算结果
        else 缓存未命中
            Service->>Calculator: 执行因子计算
            Calculator->>DataClient: 获取新闻数据
            DataClient->>DataClient: 调用data-collector API
            DataClient-->>Calculator: 返回新闻数据
            Calculator->>NLP: 执行情绪分析
            NLP->>NLP: FinBERT模型推理
            NLP-->>Calculator: 返回情绪分数
            Calculator->>Calculator: 计算情绪因子
            Calculator-->>Service: 返回计算结果
            
            Service->>DAO: 保存计算结果
            DAO->>DB: 持久化到数据库
            DAO->>Cache: 更新缓存
            
            Service-->>API: 返回计算结果
        end
        
        API-->>Client: 响应计算结果
    ```
  - **实现步骤**：
    1. 实现NLP情绪分析模块（参考design_backend.md第1.3节）
       * 集成FinBERT预训练模型
       * 实现情绪分析器和文本预处理
       * 模型加载和推理优化
    2. 实现情绪因子API接口层（参考design_backend.md第2.4.3节）
       * 路由定义：POST /api/v1/sentiment/calculate
       * GET /api/v1/sentiment/history（历史查询）
       * 支持批量新闻处理
    3. 实现情绪因子计算器（参考design_backend.md第2.4.4节）
       * 新闻情绪分数计算
       * 情绪因子聚合算法
       * 时间窗口情绪趋势分析
    4. 实现新闻数据处理逻辑
       * 新闻数据获取和过滤
       * 文本清洗和预处理
       * 股票关联度分析
    5. 集成数据访问层和模型管理
       * 情绪因子数据存储
       * NLP模型缓存和版本管理
  - _Requirements: 新闻情绪因子计算需求_
  - _Design Reference: design_backend.md 第2.4节、第1.3节_
  - _前置条件：任务I001、任务D001、任务M001完成_
  - _集成测试点：NLP模型推理测试、情绪分析准确性验证、新闻数据处理测试_

### 模块E：统一因子计算模块

#### 功能点E1：统一因子计算功能
- [ ] **任务M005. 实现统一因子计算功能（完整端到端实现）**
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as 统一因子API
        participant UFS as 统一因子服务
        participant FA as 因子聚合器
        participant TC as 技术因子计算器
        participant FC as 基本面因子计算器
        participant MC as 市场因子计算器
        participant SC as 消息面因子计算器
        participant Cache as 缓存管理器
        participant DB as 数据库

        Client->>API: POST /api/v1/factors/unified/calculate
        API->>API: 参数验证
        API->>UFS: 调用统一因子计算服务
        UFS->>Cache: 检查完整因子缓存
        
        alt 缓存命中
            Cache-->>UFS: 返回缓存数据
            UFS-->>API: 返回因子数据
            API-->>Client: 返回结果
        else 缓存未命中
            UFS->>FA: 启动并行因子计算
            
            par 并行计算各类因子
                FA->>TC: 计算技术因子
                TC-->>FA: 返回技术因子结果
            and
                FA->>FC: 计算基本面因子
                FC-->>FA: 返回基本面因子结果
            and
                FA->>MC: 计算市场因子
                MC-->>FA: 返回市场因子结果
            and
                FA->>SC: 计算消息面因子
                SC-->>FA: 返回消息面因子结果
            end
            
            FA->>FA: 聚合所有因子结果
            FA-->>UFS: 返回聚合结果
            
            UFS->>DB: 保存因子数据
            UFS->>Cache: 更新缓存
            
            UFS-->>API: 返回因子数据
            API-->>Client: 返回结果
        end
    ```
  - **实现步骤**：
    1. 实现统一因子计算API接口层（参考design_backend.md第2.5.3节）
       * 路由定义：POST /api/v1/factors/unified/calculate
       * POST /api/v1/factors/unified/batch-calculate（批量计算）
       * GET /api/v1/factors/unified/history（历史查询）
       * 支持选择性因子类型计算和自定义配置参数
    2. 实现统一因子服务（UnifiedFactorService）（参考design_backend.md第2.5.4节）
       * 统一的因子计算入口和协调逻辑
       * 集成所有类型的因子计算器
       * 实现计算结果聚合和数据持久化
       * 错误处理和部分失败容错机制
    3. 实现因子聚合器（FactorAggregator）
       * 并行执行多类型因子计算
       * 计算结果合并和格式化
       * 计算性能监控和优化
    4. 实现缓存管理器（CacheManager）
       * 完整因子数据缓存策略
       * 部分因子缓存和增量更新
       * 多层缓存架构和失效策略
    5. 集成数据访问层和性能优化
       * 批量数据保存和查询优化
       * 并发控制和资源管理
       * 计算超时和限流机制
  - _Requirements: 统一因子计算需求_
  - _Design Reference: design_backend.md 第2.5节_
  - _前置条件：任务M001、M002、M003、M004完成_
  - _集成测试点：统一API调用测试、并行计算性能测试、缓存策略验证、错误容错测试_

## 第四阶段：系统优化任务

### 任务I002. 系统集成测试与性能优化
- **实现内容**：
  - 编写完整的集成测试用例（参考design_backend.md第5.1节错误处理策略）
  - 实现API性能测试和压力测试（参考design_backend.md第6.1-6.2节性能优化）
  - 优化数据库查询性能和索引策略
  - 优化Redis缓存策略和内存使用
  - 实现监控和日志分析功能
  - 编写部署文档和运维指南
- **性能目标**：
  - API响应时间 < 2秒
  - 支持1000+并发请求
  - 批量计算支持10000+股票
- **实现边界**：系统级优化和测试，不涉及新功能开发
- _Requirements: 性能和稳定性需求_
- _Design Reference: design_backend.md 第5节、第6节_
- _前置条件：所有业务功能任务完成_
- _集成测试点：端到端功能测试、性能基准测试、稳定性测试_

## 任务执行顺序

**第一优先级（MVP核心功能）：**
1. 任务I001（基础架构）
2. 任务D001（数据模型）
3. 任务M001（技术因子计算）

**第二优先级（扩展功能）：**
4. 任务M002（基本面因子计算）
5. 任务M003（市场因子计算）

**第三优先级（高级功能）：**
6. 任务M004（新闻情绪因子计算）
7. 任务M005（统一因子计算功能）

**第四优先级（系统优化）：**
8. 任务I002（集成测试与优化）

## 验收标准

### 功能验收标准
1. **API接口**：所有API接口正常响应，返回格式符合设计规范
2. **计算准确性**：因子计算结果与预期值误差 < 0.01%
3. **数据一致性**：数据库和缓存数据保持一致
4. **错误处理**：异常情况下系统能正确处理并返回错误信息

### 性能验收标准
1. **响应时间**：单次因子计算API响应时间 < 2秒
2. **并发能力**：支持100并发用户同时访问
3. **批量处理**：支持1000+股票的批量因子计算
4. **内存使用**：服务内存使用 < 2GB

### 质量验收标准
1. **代码覆盖率**：单元测试覆盖率 > 80%
2. **集成测试**：所有API接口通过集成测试
3. **文档完整性**：API文档和部署文档完整
4. **日志记录**：关键操作有完整的日志记录

## 风险控制

### 技术风险
1. **NLP模型性能**：FinBERT模型推理可能较慢，需要优化或考虑模型量化
2. **数据质量**：外部数据源可能存在异常，需要完善数据验证机制
3. **并发处理**：高并发场景下可能出现资源竞争，需要合理的锁机制

### 进度风险
1. **依赖服务**：依赖data-collector服务的稳定性，需要做好容错处理
2. **复杂度评估**：NLP模块实现复杂度较高，可能需要额外时间
3. **性能调优**：批量计算性能优化可能需要多轮迭代

### 缓解措施
1. **分阶段交付**：按照MVP原则，优先交付核心功能
2. **并行开发**：基础设施和业务功能可以并行开发
3. **充分测试**：每个阶段完成后进行充分的集成测试
4. **文档先行**：API设计文档先行，确保接口稳定