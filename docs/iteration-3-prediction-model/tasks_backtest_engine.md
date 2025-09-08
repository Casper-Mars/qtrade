# 基于Backtrader的回测引擎模块 - 任务拆分文档

## 回测引擎模块任务文档

## 项目类型：现有项目（基于现有quant-engine服务扩展，采用Backtrader框架）

## 核心业务功能任务（按模块和功能点拆分）

### 模块A：基于Backtrader的回测引擎模块

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
    * 添加initial_capital、transaction_cost等Backtrader配置字段
    * 添加配置验证逻辑和默认值设置
  - 实现BacktestFactorConfig数据模型（参考design_backend.md第2.1.4节）
    * 定义因子列表和权重配置结构
    * 实现按类型分组的因子管理方法（技术、基本面、市场、情绪）
    * 添加权重验证和标准化功能
    * 支持动态因子组合配置
  - 实现BacktestResult数据模型（参考design_backend.md第2.1.4节）
    * 定义绩效指标字段（收益率、夏普比率、最大回撤等）
    * 兼容Backtrader分析器输出格式
    * 实现结果序列化和反序列化方法
    * 添加结果验证和格式化功能
  - 实现BacktestMode枚举（参考design_backend.md第2.1.3节）
    * 定义历史模拟和模型验证两种回测模式
    * 支持不同模式下的因子数据获取策略
  - _Requirements: 回测配置管理、Backtrader集成、结果存储_
  - _Design Reference: design_backend.md 第2.1.4节_
  - _前置条件：无_
  - _集成测试点：配置验证测试、数据序列化测试、Backtrader兼容性测试_

#### 功能点A2：因子数据源实现
- [ ] 任务M002. 实现FactorDataFeed数据源（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Cerebro as bt.Cerebro
        participant DataFeed as FactorDataFeed
        participant FS as FactorService
        participant TushareClient as Tushare客户端
        
        Cerebro->>DataFeed: 初始化数据源
        DataFeed->>TushareClient: 获取历史价格数据
        TushareClient-->>DataFeed: 返回OHLCV数据
        DataFeed->>FS: 获取因子数据
        FS-->>DataFeed: 返回因子数据
        DataFeed->>DataFeed: 数据格式转换和同步
        DataFeed-->>Cerebro: 提供标准化数据流
    ```
  - 实现FactorDataFeed类（继承bt.feeds.DataBase）
    * 继承Backtrader数据源基类，实现_load()和_getdata()方法
    * 集成TushareClient获取历史价格数据（OHLCV）
    * 集成FactorService获取因子数据
    * 实现价格数据和因子数据的时间同步
    * 支持数据缓存和增量加载
  - 实现数据格式转换（参考design_backend.md第2.1.3节）
    * 将Tushare数据格式转换为Backtrader标准格式
    * 处理数据缺失和异常值
    * 实现数据质量检查和验证
  - 实现数据同步机制（参考design_backend.md第2.1.2节）
    * 确保价格数据和因子数据的时间对齐
    * 处理交易日历和数据频率差异
    * 实现数据完整性验证
  - _Requirements: 数据源集成、Backtrader兼容、数据同步_
  - _Design Reference: design_backend.md 第2.1.3节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据加载测试、格式转换测试、时间同步验证_

#### 功能点A3：因子策略实现
- [ ] 任务M003. 实现FactorStrategy策略（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Cerebro as bt.Cerebro
        participant Strategy as FactorStrategy
        participant FS as FactorService
        participant Broker as bt.Broker
        
        loop 每个交易日
            Cerebro->>Strategy: 调用next()方法
            Strategy->>Strategy: 获取当前日期和股票代码
            Strategy->>FS: 获取当前时点因子数据
            FS-->>Strategy: 返回因子数据
            Strategy->>Strategy: 计算因子综合评分
            
            alt 买入信号
                Strategy->>Strategy: 计算仓位大小
                Strategy->>Broker: self.buy(size)
            else 卖出信号
                Strategy->>Broker: self.sell(size)
            else 持有信号
                Strategy->>Strategy: 不执行交易
            end
            
            Strategy->>Strategy: 记录交易统计
        end
    ```
  - 实现FactorStrategy类（继承bt.Strategy）
    * 继承Backtrader策略基类，实现next()方法
    * 实现因子数据获取逻辑，支持历史模拟和模型验证模式
    * 实现因子综合评分计算算法
    * 实现交易信号生成逻辑（买入/卖出/持有）
    * 实现仓位管理和风险控制
  - 实现因子评分计算（参考design_backend.md第2.1.3节）
    * 根据因子组合权重计算加权综合评分
    * 支持动态因子权重配置
    * 实现评分标准化和归一化
    * 添加评分历史记录和统计
  - 实现交易信号生成（参考design_backend.md第2.1.3节）
    * 基于评分阈值生成买卖信号
    * 实现信号过滤和平滑机制
    * 支持可配置的信号参数（买入阈值、卖出阈值等）
    * 实现信号强度和置信度计算
  - 实现仓位管理（参考design_backend.md第2.1.3节）
    * 计算合理的仓位大小
    * 实现风险控制机制（最大仓位、止损等）
    * 支持资金管理策略
  - 实现策略参数管理
    * 使用Backtrader的params机制管理策略参数
    * 支持因子组合、回测模式、阈值等参数配置
    * 实现参数验证和默认值设置
  - _Requirements: 策略实现、因子集成、信号生成、风险控制_
  - _Design Reference: design_backend.md 第2.1.3节_
  - _前置条件：任务M001、M002完成_
  - _集成测试点：策略逻辑测试、信号生成测试、仓位管理测试_

#### 功能点A4：绩效分析器实现
- [ ] 任务M004. 实现PerformanceAnalyzer分析器（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant Cerebro as bt.Cerebro
        participant Analyzer as PerformanceAnalyzer
        participant Strategy as FactorStrategy
        participant Broker as bt.Broker
        
        Cerebro->>Analyzer: 初始化分析器
        
        loop 回测过程中
            Broker->>Analyzer: notify_cashvalue(cash, value)
            Strategy->>Analyzer: notify_trade(trade)
            Analyzer->>Analyzer: 更新绩效数据
        end
        
        Cerebro->>Analyzer: get_analysis()
        Analyzer->>Analyzer: 计算最终绩效指标
        Analyzer-->>Cerebro: 返回绩效分析结果
    ```
  - 实现PerformanceAnalyzer类（继承bt.Analyzer）
    * 继承Backtrader分析器基类，实现create_analysis()方法
    * 实现notify_cashvalue()和notify_trade()回调方法
    * 实现get_analysis()方法返回绩效分析结果
    * 集成Backtrader内置分析器功能
  - 实现绩效指标计算（参考design_backend.md第2.1.4节）
    * 计算总收益率、年化收益率、最大回撤等核心指标
    * 实现夏普比率、索提诺比率等风险调整收益指标
    * 添加胜率、平均盈亏比等交易统计指标
    * 实现波动率、VaR等风险指标计算
  - 实现实时监控功能
    * 实时更新绩效数据和统计信息
    * 记录交易历史和持仓变化
    * 实现绩效数据的缓存和持久化
  - 实现自定义指标扩展
    * 扩展Backtrader内置分析器功能
    * 支持自定义绩效指标计算
    * 实现指标数据的标准化输出
  - _Requirements: 绩效分析、实时监控、指标计算_
  - _Design Reference: design_backend.md 第2.1.4节_
  - _前置条件：任务M001、M002、M003完成_
  - _集成测试点：绩效计算测试、指标验证测试、实时监控测试_

#### 功能点A5：回测引擎核心实现
- [ ] 任务M005. 实现BacktestEngine核心（完整端到端实现）
  - **时序图描述**：
    ```mermaid
    sequenceDiagram
        participant API as 回测API
        participant BE as BacktestEngine
        participant Cerebro as bt.Cerebro
        participant Strategy as FactorStrategy
        participant DataFeed as FactorDataFeed
        participant Analyzer as PerformanceAnalyzer
        
        API->>BE: run_backtest(config)
        BE->>BE: 验证回测配置
        
        BE->>Cerebro: 创建bt.Cerebro实例
        BE->>Cerebro: 设置初始资金和交易成本
        
        BE->>DataFeed: 创建FactorDataFeed
        BE->>Cerebro: adddata(data_feed)
        
        BE->>Cerebro: addstrategy(FactorStrategy)
        BE->>Cerebro: addanalyzer(内置+自定义分析器)
        
        BE->>Cerebro: cerebro.run()
        
        Note over Cerebro: Backtrader自动执行回测
        
        Cerebro-->>BE: 返回策略和分析器结果
        BE->>BE: 提取和格式化结果
        BE-->>API: 返回BacktestResult
    ```
  - 实现BacktestEngine核心类（参考design_backend.md第2.1.3节）
    * 封装Backtrader的Cerebro引擎，提供业务层接口
    * 实现run_backtest()方法执行完整回测流程
    * 实现run_factor_combination_test()方法进行因子组合测试
    * 支持历史模拟和模型验证两种回测模式
  - 实现Cerebro引擎配置（参考design_backend.md第2.1.3节）
    * 配置初始资金、交易成本、滑点等参数
    * 添加数据源、策略、分析器到Cerebro
    * 设置Broker参数和交易规则
    * 配置回测执行参数
  - 实现组件集成和协调（参考design_backend.md第2.1.2节）
    * 协调FactorDataFeed、FactorStrategy、PerformanceAnalyzer组件
    * 实现组件间的参数传递和配置同步
    * 添加异常处理和错误恢复机制
    * 实现回测进度监控和状态报告功能
  - 实现结果提取和格式化（参考design_backend.md第2.1.4节）
    * 从Backtrader策略和分析器中提取结果
    * 格式化为标准BacktestResult格式
    * 实现结果验证和完整性检查
    * 添加结果持久化和缓存功能
  - 实现配置验证和参数管理（参考design_backend.md第2.1.4节）
    * 验证回测配置的完整性和有效性
    * 管理回测参数和运行时状态
    * 实现配置缓存和复用机制
  - _Requirements: 回测引擎核心功能、Backtrader集成、组件协调_
  - _Design Reference: design_backend.md 第2.1.2节、第2.1.3节、第2.1.4节_
  - _前置条件：任务M001、M002、M003、M004完成_
  - _集成测试点：端到端回测测试、Backtrader集成测试、组件协调测试_

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
    * 支持Backtrader结果格式的存储
  - 创建数据库表结构（参考design_backend.md第3.2节）
    * 创建backtest_results表存储回测结果
    * 创建backtest_tasks表存储任务信息
    * 创建backtest_batches表支持批次管理
    * 添加必要的索引和约束
    * 实现数据库迁移脚本
  - 实现数据模型映射
    * 实现BacktestResult到数据库记录的映射
    * 支持JSON字段存储复杂数据结构
    * 实现数据序列化和反序列化
  - _Requirements: 数据持久化、查询优化、批次管理_
  - _Design Reference: design_backend.md 第3.2节_
  - _前置条件：任务M001完成_
  - _集成测试点：数据库操作测试、查询功能测试、数据一致性测试_

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
  - 实现回测执行API（参考design_backend.md第2.3节）
    * 实现POST /api/v1/backtest/run接口
    * 添加请求参数验证和错误处理
    * 支持同步和异步回测执行
    * 集成BacktestEngine核心功能
  - 实现回测结果查询API（参考design_backend.md第2.3节）
    * 实现POST /api/v1/backtest/getResults接口
    * 支持基本查询和结果返回
    * 实现分页和过滤功能
  - 实现批次管理API（参考design_backend.md第2.3节）
    * 实现POST /api/v1/backtest/createBatch接口
    * 实现POST /api/v1/backtest/getBatchStatus接口
    * 支持批量回测任务管理
  - 实现API文档和验证
    * 使用FastAPI自动生成API文档
    * 实现请求参数验证和响应格式标准化
    * 添加错误处理和异常响应
  - _Requirements: API接口、参数验证、错误处理、批次管理_
  - _Design Reference: design_backend.md 第2.3节_
  - _前置条件：任务M005、M006完成_
  - _集成测试点：API接口测试、参数验证测试、错误处理测试_

## 任务执行顺序说明

**第一阶段：基础数据模型（优先级最高）**
- 任务M001：数据模型定义是所有功能的基础，必须首先完成

**第二阶段：Backtrader组件实现（按依赖关系执行）**
- 任务M002：FactorDataFeed数据源（依赖M001）
- 任务M003：FactorStrategy策略（依赖M001、M002）
- 任务M004：PerformanceAnalyzer分析器（依赖M001、M002、M003）
- 任务M006：数据访问层（依赖M001，可与M002-M004并行）

**第三阶段：集成和接口（最后执行）**
- 任务M005：BacktestEngine核心（依赖M001-M004）
- 任务M007：API接口（依赖M005、M006）

## 基于Backtrader的技术要点

**Backtrader框架集成：**
- 所有组件必须遵循Backtrader的架构模式
- 数据源继承bt.feeds.DataBase
- 策略继承bt.Strategy
- 分析器继承bt.Analyzer
- 使用Cerebro作为核心引擎

**数据流设计：**
- FactorDataFeed负责数据获取和格式转换
- FactorStrategy负责策略逻辑和交易决策
- PerformanceAnalyzer负责绩效监控和指标计算
- BacktestEngine负责组件协调和结果提取

**兼容性要求：**
- 与现有FactorService保持兼容
- 复用现有TushareClient数据源
- 遵循现有的数据库设计模式
- 保持API接口的一致性

## 验收标准

**功能验收：**
- [ ] 基于Backtrader框架实现完整回测功能
- [ ] 支持单股票回测，包含历史模拟和模型验证两种模式
- [ ] 支持动态因子组合配置和权重调整
- [ ] 生成完整的绩效报告，包含核心风险收益指标
- [ ] 提供标准化API接口，支持批次回测任务
- [ ] 与现有因子服务完全集成

**技术验收：**
- [ ] 所有组件正确继承Backtrader基类
- [ ] Cerebro引擎配置正确，支持各种回测参数
- [ ] 数据源正确加载价格和因子数据
- [ ] 策略逻辑正确执行，交易信号生成准确
- [ ] 分析器正确计算绩效指标
- [ ] 结果提取和格式化功能完整

**性能验收：**
- [ ] 单股票一年期回测任务在5分钟内完成
- [ ] 支持并发回测任务，不影响系统稳定性
- [ ] 数据库查询响应时间在100ms以内
- [ ] Backtrader引擎内存使用合理

**质量验收：**
- [ ] 代码覆盖率达到80%以上
- [ ] 通过集成测试，无关键功能缺陷
- [ ] 符合现有代码规范和架构约束
- [ ] Backtrader组件集成测试通过
- [ ] 与现有系统兼容性测试通过

## 风险控制和注意事项

**Backtrader学习成本：**
- 开发团队需要熟悉Backtrader框架的使用方法
- 需要理解Backtrader的数据流和事件驱动机制
- 建议先完成Backtrader基础培训和示例学习

**数据兼容性：**
- 确保Tushare数据格式与Backtrader兼容
- 处理数据时间同步和格式转换问题
- 验证因子数据与价格数据的一致性

**性能优化：**
- 合理使用Backtrader的缓存机制
- 优化数据加载和处理性能
- 避免在策略中进行重复计算

**错误处理：**
- 完善Backtrader组件的异常处理
- 实现回测失败的恢复机制
- 添加详细的日志记录和错误追踪