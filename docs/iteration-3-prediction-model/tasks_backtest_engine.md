# 回测引擎模块 - 任务拆分文档

## 项目类型：现有项目（基于quant-engine服务扩展）

## 核心业务功能任务（按功能点拆分）

### 模块A：回测引擎核心功能

#### 功能点A1：数据模型定义
- [ ] 任务M001. 实现回测配置数据模型（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as API层
        participant Model as 数据模型
        participant Validator as 验证器
        
        Client->>API: 提交回测配置
        API->>Model: 创建BacktestConfig实例
        Model->>Validator: 验证配置参数
        Validator-->>Model: 返回验证结果
        Model-->>API: 返回配置对象
        API-->>Client: 返回配置确认
    ```
  - 实现BacktestConfig数据模型（参考design_backend.md第2.1.4节）
    * 定义股票代码、日期范围、因子组合等核心字段
    * 实现回测模式枚举（历史模拟、模型验证）
    * 添加配置验证逻辑和默认值设置
  - 实现FactorCombination数据模型（参考design_backend.md第2.1.4节）
    * 定义因子列表和权重配置结构
    * 实现按类型分组的因子管理方法
    * 添加权重验证和标准化功能
  - 实现BacktestResult数据模型（参考design_backend.md第2.1.4节）
    * 定义绩效指标字段（收益率、夏普比率、最大回撤等）
    * 实现结果序列化和反序列化方法
    * 添加结果验证和格式化功能
  - _Requirements: 回测配置管理、结果存储_
  - _Design Reference: design_backend.md 第2.1.4节_
  - _前置条件：无_
  - _集成测试点：配置验证测试、数据序列化测试_

#### 功能点A2：数据回放器实现
- [ ] 任务M002. 实现历史数据回放器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant BE as BacktestEngine
        participant DR as DataReplayer
        participant FS as FactorService
        participant DS as DataService
        
        BE->>DR: 初始化回放器(start_date, end_date)
        loop 每个交易日
            DR->>DS: 获取基础市场数据
            DS-->>DR: 返回价格、成交量数据
            DR->>FS: 获取因子数据
            FS-->>DR: 返回因子计算结果
            DR->>DR: 组装数据快照
            DR-->>BE: 返回当日完整数据
        end
    ```
  - 实现DataReplayer类（参考design_backend.md第2.1.2节）
    * 实现按时间顺序的数据回放逻辑
    * 实现数据快照生成和缓存机制
    * 添加未来函数检测和防止数据泄露功能
  - 集成现有因子服务接口（参考design_backend.md第2.1.3节）
    * 调用calculate_all_factors接口获取因子数据
    * 实现因子数据的时间对齐和缺失值处理
    * 支持历史模拟和模型验证两种数据获取模式
  - 实现数据完整性验证（参考design_backend.md第2.1.2节）
    * 验证数据时间序列的连续性
    * 检查关键字段的缺失值和异常值
    * 实现数据质量报告生成
  - _Requirements: 历史数据回放、数据完整性保证_
  - _Design Reference: design_backend.md 第2.1.2节、第2.1.3节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据回放测试、时间序列验证、因子数据获取测试_

#### 功能点A3：交易信号生成器实现
- [ ] 任务M003. 实现交易信号生成器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant BE as BacktestEngine
        participant SG as SignalGenerator
        participant FC as FactorCombination
        
        BE->>SG: 传入因子数据和组合配置
        SG->>FC: 获取因子权重配置
        FC-->>SG: 返回权重信息
        SG->>SG: 计算因子综合评分
        SG->>SG: 根据阈值生成交易信号
        SG-->>BE: 返回交易信号
    ```
  - 实现SignalGenerator类（参考design_backend.md第2.1.3节）
    * 实现基于因子组合的综合评分计算
    * 实现动态权重配置的信号生成逻辑
    * 添加信号强度和置信度计算功能
  - 实现TradingSignal数据模型（参考design_backend.md第2.1.3节）
    * 定义信号类型（BUY/SELL/HOLD）和强度字段
    * 实现信号验证和格式化方法
    * 添加信号历史记录和统计功能
  - 实现信号过滤和优化（参考design_backend.md第2.1.3节）
    * 实现基于阈值的信号过滤机制
    * 添加信号平滑和去噪功能
    * 实现仓位大小计算和风险控制
  - _Requirements: 交易信号生成、因子组合评分_
  - _Design Reference: design_backend.md 第2.1.3节_
  - _前置条件：任务M001、M002完成_
  - _集成测试点：信号生成测试、评分计算验证、阈值过滤测试_

#### 功能点A4：收益计算器实现
- [ ] 任务M004. 实现收益计算器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant BE as BacktestEngine
        participant RC as ReturnCalculator
        participant Portfolio as 投资组合
        
        BE->>RC: 传入交易信号和价格数据
        RC->>Portfolio: 更新持仓状态
        Portfolio-->>RC: 返回持仓信息
        RC->>RC: 计算交易成本
        RC->>RC: 计算当日收益
        RC->>RC: 更新累计收益和绩效指标
        RC-->>BE: 返回收益数据
    ```
  - 实现ReturnCalculator类（参考design_backend.md第2.1.2节）
    * 实现基于交易信号的投资组合收益计算
    * 实现交易成本和滑点的模拟计算
    * 添加风险控制和仓位管理功能
  - 实现绩效指标计算（参考design_backend.md第2.1.4节）
    * 计算年化收益率、夏普比率、最大回撤等核心指标
    * 实现索提诺比率、VaR等高级风险指标
    * 添加胜率、交易次数等统计指标
  - 实现投资组合管理（参考design_backend.md第2.1.2节）
    * 实现持仓状态的动态更新和跟踪
    * 添加资金管理和杠杆控制功能
    * 实现投资组合净值曲线生成
  - _Requirements: 收益计算、绩效评估、风险控制_
  - _Design Reference: design_backend.md 第2.1.2节、第2.1.4节_
  - _前置条件：任务M001、M002、M003完成_
  - _集成测试点：收益计算测试、绩效指标验证、风险控制测试_

#### 功能点A5：回测引擎核心实现
- [ ] 任务M005. 实现回测引擎核心逻辑（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant API as API接口
        participant BE as BacktestEngine
        participant DR as DataReplayer
        participant SG as SignalGenerator
        participant RC as ReturnCalculator
        
        API->>BE: run_backtest(config)
        BE->>BE: 验证配置参数
        BE->>DR: 初始化数据回放器
        
        loop 历史数据回放
            DR-->>BE: 返回当日数据
            BE->>SG: 生成交易信号
            SG-->>BE: 返回信号
            BE->>RC: 计算收益
            RC-->>BE: 返回收益数据
        end
        
        BE->>RC: 计算最终绩效指标
        RC-->>BE: 返回完整绩效报告
        BE-->>API: 返回回测结果
    ```
  - 实现BacktestEngine主类（参考design_backend.md第2.1.1节）
    * 实现run_backtest主流程控制逻辑
    * 集成数据回放器、信号生成器、收益计算器
    * 添加异常处理和错误恢复机制
  - 实现因子组合测试功能（参考design_backend.md第2.1.3节）
    * 实现run_factor_combination_test方法
    * 支持多因子组合的批量测试和比较
    * 添加测试结果的排序和筛选功能
  - 实现回测模式支持（参考design_backend.md第2.1.1节）
    * 支持历史模拟模式和模型验证模式
    * 实现不同模式下的数据获取策略
    * 添加模式切换和配置验证功能
  - _Requirements: 回测流程控制、模式支持、异常处理_
  - _Design Reference: design_backend.md 第2.1.1节、第2.1.3节_
  - _前置条件：任务M001、M002、M003、M004完成_
  - _集成测试点：完整回测流程测试、多模式测试、异常场景测试_

### 模块B：数据访问层扩展

#### 功能点B1：回测数据访问层实现
- [ ] 任务M006. 实现回测数据访问层（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant BE as BacktestEngine
        participant DAO as BacktestDAO
        participant DB as MySQL数据库
        participant Cache as Redis缓存
        
        BE->>DAO: 保存回测结果
        DAO->>DB: 插入回测结果记录
        DB-->>DAO: 返回插入结果
        DAO->>Cache: 缓存热点数据
        DAO-->>BE: 返回保存确认
        
        BE->>DAO: 查询历史回测结果
        DAO->>Cache: 查询缓存
        alt 缓存命中
            Cache-->>DAO: 返回缓存数据
        else 缓存未命中
            DAO->>DB: 查询数据库
            DB-->>DAO: 返回查询结果
            DAO->>Cache: 更新缓存
        end
        DAO-->>BE: 返回查询结果
    ```
  - 实现BacktestDAO类（参考design_backend.md第3.2节）
    * 实现回测结果的CRUD操作
    * 实现批量数据插入和查询优化
    * 添加数据库连接池管理和事务处理
  - 创建数据库表结构（参考design_backend.md第3.2节）
    * 创建backtest_results表存储回测结果
    * 添加必要的索引和约束
    * 实现数据库迁移脚本
  - 实现缓存策略（参考design_backend.md第3.2节）
    * 实现Redis缓存的读写操作
    * 添加缓存失效和更新机制
    * 实现缓存预热和清理功能
  - _Requirements: 数据持久化、查询优化、缓存管理_
  - _Design Reference: design_backend.md 第3.2节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据库操作测试、缓存功能测试、性能测试_

### 模块C：API接口层

#### 功能点C1：回测API接口实现
- [ ] 任务M007. 实现回测API接口（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Client as 客户端
        participant API as BacktestAPI
        participant BE as BacktestEngine
        participant DAO as BacktestDAO
        
        Client->>API: POST /api/v1/backtest/run
        API->>API: 参数验证
        API->>BE: 执行回测
        BE->>DAO: 保存结果
        DAO-->>BE: 保存确认
        BE-->>API: 返回回测结果
        API-->>Client: 返回API响应
        
        Client->>API: POST /api/v1/backtest/getResults
        API->>DAO: 查询结果
        DAO-->>API: 返回结果数据
        API-->>Client: 返回查询结果
    ```
  - 实现回测执行API（参考design_backend.md第2.1节）
    * 实现POST /api/v1/backtest/run接口
    * 添加请求参数验证和错误处理
    * 实现异步回测任务支持
  - 实现回测结果查询API（参考design_backend.md第2.1节）
    * 实现POST /api/v1/backtest/getResults接口
    * 支持分页查询和条件过滤
    * 添加结果格式化和数据导出功能
  - 实现因子组合测试API（参考design_backend.md第2.1.3节）
    * 实现POST /api/v1/backtest/testCombinations接口
    * 支持批量因子组合测试
    * 添加测试结果比较和排序功能
  - _Requirements: API接口、参数验证、错误处理_
  - _Design Reference: design_backend.md 第2.1节_
  - _前置条件：任务M005、M006完成_
  - _集成测试点：API接口测试、参数验证测试、错误处理测试_

## 任务执行顺序说明

**第一阶段：基础数据模型（优先级最高）**
- 任务M001：数据模型定义是所有功能的基础

**第二阶段：核心组件实现（按依赖关系执行）**
- 任务M002：数据回放器（依赖M001）
- 任务M003：信号生成器（依赖M001、M002）
- 任务M004：收益计算器（依赖M001、M002、M003）
- 任务M006：数据访问层（依赖M001，可与M002-M004并行）

**第三阶段：集成和接口（最后执行）**
- 任务M005：回测引擎核心（依赖M001-M004）
- 任务M007：API接口（依赖M005、M006）

## 验收标准

**功能验收：**
- [ ] 支持单股票回测，包含历史模拟和模型验证两种模式
- [ ] 支持动态因子组合配置和权重调整
- [ ] 生成完整的绩效报告，包含核心风险收益指标
- [ ] 提供RESTful API接口，支持异步回测任务

**性能验收：**
- [ ] 单股票一年期回测任务在5分钟内完成
- [ ] 支持并发回测任务，不影响系统稳定性
- [ ] 数据库查询响应时间在100ms以内

**质量验收：**
- [ ] 代码覆盖率达到80%以上
- [ ] 通过集成测试，无关键功能缺陷
- [ ] 符合现有代码规范和架构约束