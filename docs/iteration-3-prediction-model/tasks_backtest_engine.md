# 回测引擎模块 - 任务拆分文档

## 回测引擎模块任务文档

## 项目类型：现有项目（基于现有quant-engine服务扩展）

## 核心业务功能任务（按模块和功能点拆分）

### 模块A：回测引擎模块

#### 功能点A1：数据模型定义
- [x] 任务M001. 实现回测配置数据模型（完整端到端实现）
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
  - 实现BacktestFactorConfig数据模型（参考design_backend.md第2.1.4节）
    * 定义因子列表和权重配置结构
    * 实现按类型分组的因子管理方法
    * 添加权重验证和标准化功能
  - 实现BacktestResult数据模型（参考design_backend.md第2.1.4节）
    * 定义绩效指标字段（收益率、夏普比率、最大回撤等）
    * 实现结果序列化和反序列化方法
    * 添加结果验证和格式化功能
  - 实现TradingSignal数据模型（参考design_backend.md第2.1.3节）
    * 定义交易信号类型、强度、仓位大小等字段
    * 实现信号验证和格式化功能
  - _Requirements: 回测配置管理、结果存储_
  - _Design Reference: design_backend.md 第2.1.4节_
  - _前置条件：无_
  - _集成测试点：配置验证测试、数据序列化测试_

#### 功能点A2：数据回放器实现
- [ ] 任务M002. 实现历史数据回放器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Engine as 回测引擎
        participant Replayer as 数据回放器
        participant FactorService as 因子服务
        participant Cache as 数据缓存
        
        Engine->>Replayer: 启动数据回放(start_date, end_date)
        Replayer->>FactorService: 获取历史数据
        FactorService-->>Replayer: 返回历史数据
        Replayer->>Cache: 缓存数据
        loop 按时间顺序回放
            Replayer->>Replayer: 获取当前时点数据
            Replayer->>Replayer: 验证数据完整性
            Replayer-->>Engine: 返回时点数据快照
        end
    ```
  - 实现DataReplayer类（参考design_backend.md第2.1.2节）
    * 实现replay_data()方法按时间顺序回放历史数据
    * 实现get_snapshot()方法获取指定时点的数据快照
    * 实现数据完整性检查，防止未来信息泄露
    * 支持历史模拟和模型验证两种回测模式
  - 集成现有因子服务（参考design_backend.md第0.2节）
    * 复用现有的FactorService获取历史因子数据
    * 支持批量数据获取和缓存机制
    * 实现数据格式标准化处理
  - 实现数据完整性验证（参考design_backend.md第2.1.2节）
    * 验证数据时间序列的连续性
    * 检查关键字段的缺失值和异常值
    * 实现数据质量报告生成
  - _Requirements: 历史数据回放、数据完整性保证_
  - _Design Reference: design_backend.md 第2.1.2节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据回放测试、时间序列验证、因子数据获取测试_

#### 功能点A3：交易信号生成器实现
- [ ] 任务M003. 实现交易信号生成器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Engine as 回测引擎
        participant Generator as 信号生成器
        participant Scorer as 评分计算器
        participant Config as 因子配置
        
        Engine->>Generator: 生成交易信号(factor_data, factor_combination)
        Generator->>Scorer: 计算因子综合评分
        Scorer->>Config: 获取因子权重配置
        Config-->>Scorer: 返回权重信息
        Scorer->>Scorer: 计算加权综合评分
        Scorer-->>Generator: 返回综合评分
        Generator->>Generator: 根据评分生成交易信号
        Generator-->>Engine: 返回交易信号
    ```
  - 实现SignalGenerator类（参考design_backend.md第2.1.3节）
    * 实现generate_signals()方法基于因子组合生成交易信号
    * 实现_calculate_composite_score()方法计算因子综合评分
    * 实现_generate_signal_from_score()方法根据评分生成信号
    * 支持动态因子权重配置和信号阈值调整
  - 实现TradingSignal数据模型（参考design_backend.md第2.1.3节）
    * 定义信号类型（BUY/SELL/HOLD）和强度字段
    * 实现信号验证和格式化方法
    * 添加信号历史记录和统计功能
  - 实现信号过滤和优化（参考design_backend.md第2.1.3节）
    * 实现基于阈值的信号过滤机制
    * 添加信号平滑和去噪功能
    * 实现仓位大小计算逻辑
    * 添加风险控制机制
  - _Requirements: 交易信号生成、因子组合评分_
  - _Design Reference: design_backend.md 第2.1.3节_
  - _前置条件：任务M001、M002完成_
  - _集成测试点：信号生成测试、评分计算验证_

#### 功能点A4：收益计算器实现
- [ ] 任务M004. 实现收益计算器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Engine as 回测引擎
        participant Calculator as 收益计算器
        participant Portfolio as 投资组合
        participant PriceData as 价格数据
        
        Engine->>Calculator: 计算投资组合收益(positions, prices)
        Calculator->>Portfolio: 获取持仓信息
        Portfolio-->>Calculator: 返回持仓数据
        Calculator->>PriceData: 获取价格数据
        PriceData-->>Calculator: 返回价格信息
        Calculator->>Calculator: 计算收益率和绩效指标
        Calculator-->>Engine: 返回收益分析结果
    ```
  - 实现ReturnCalculator类（参考design_backend.md第2.1.2节）
    * 实现calculate_portfolio_returns()方法计算投资组合收益
    * 实现calculate_transaction_costs()方法计算交易成本
    * 实现apply_risk_controls()方法应用风险控制
    * 支持多种收益计算模式和基准比较
  - 实现绩效指标计算（参考design_backend.md第2.1.2节）
    * 计算总收益率、年化收益率、最大回撤等核心指标
    * 实现夏普比率、索提诺比率等风险调整收益指标
    * 添加胜率、平均盈亏比等交易统计指标
    * 实现波动率、VaR等风险指标计算
  - 实现交易成本和滑点模拟（参考design_backend.md第2.1.2节）
    * 计算佣金、印花税等交易费用
    * 模拟市场冲击和滑点成本
    * 实现不同交易规模的成本计算
  - _Requirements: 收益计算、绩效分析_
  - _Design Reference: design_backend.md 第2.1.2节_
  - _前置条件：任务M001、M002、M003完成_
  - _集成测试点：收益计算测试、绩效指标验证_

#### 功能点A5：回测引擎核心实现
- [ ] 任务M005. 实现回测引擎核心（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant API as 回测API
        participant Engine as BacktestEngine
        participant Replayer as 数据回放器
        participant Generator as 信号生成器
        participant Calculator as 收益计算器
        participant FactorService as 因子服务
        
        API->>Engine: run_backtest(config)
        Engine->>Engine: 验证回测配置
        Engine->>Replayer: 初始化数据回放器
        
        loop 历史数据回放
            Replayer->>FactorService: 获取当前时点因子数据
            FactorService-->>Replayer: 返回因子数据
            Replayer-->>Engine: 返回数据快照
            Engine->>Generator: 生成交易信号
            Generator-->>Engine: 返回交易信号
            Engine->>Calculator: 计算当期收益
            Calculator-->>Engine: 返回收益数据
        end
        
        Engine->>Calculator: 计算最终绩效指标
        Calculator-->>Engine: 返回绩效分析结果
        Engine-->>API: 返回BacktestResult
    ```
  - 实现BacktestEngine核心类（参考design_backend.md第2.1.2节）
    * 实现run_backtest()方法执行完整回测流程
    * 实现run_factor_combination_test()方法进行因子组合测试
    * 实现get_factor_data()方法获取因子数据
    * 支持历史模拟和模型验证两种回测模式
  - 集成各个组件（参考design_backend.md第2.1.2节）
    * 协调DataReplayer、SignalGenerator、ReturnCalculator组件
    * 实现组件间的数据传递和状态同步
    * 添加异常处理和错误恢复机制
    * 实现回测进度监控和状态报告功能
  - 实现配置验证和参数管理（参考design_backend.md第2.1.4节）
    * 验证回测配置的完整性和有效性
    * 管理回测参数和运行时状态
    * 实现配置缓存和复用机制
  - 实现结果收集和格式化（参考design_backend.md第2.1.4节）
    * 收集各组件的计算结果
    * 格式化为标准BacktestResult格式
    * 实现结果验证和完整性检查
    * 添加结果持久化和缓存功能
  - _Requirements: 回测引擎核心功能、组件协调_
  - _Design Reference: design_backend.md 第2.1.2节、第2.1.4节_
  - _前置条件：任务M001、M002、M003、M004完成_
  - _集成测试点：端到端回测测试、组件集成测试_

### 模块B：数据访问层扩展

#### 功能点B1：回测数据访问层实现
- [ ] 任务M006. 实现回测数据访问层（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant BE as BacktestEngine
        participant DAO as BacktestDAO
        participant DB as MySQL数据库
        
        BE->>DAO: 保存回测结果
        DAO->>DB: 插入回测结果记录
        DB-->>DAO: 返回插入结果
        DAO-->>BE: 返回保存确认
        
        BE->>DAO: 查询历史回测结果
        DAO->>DB: 查询数据库
        DB-->>DAO: 返回查询结果
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
  - _Requirements: 数据持久化、查询优化_
  - _Design Reference: design_backend.md 第3.2节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据库操作测试、查询功能测试_

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
  - 实现回测结果查询API（参考design_backend.md第2.1节）
    * 实现POST /api/v1/backtest/getResults接口
    * 支持基本查询和结果返回
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