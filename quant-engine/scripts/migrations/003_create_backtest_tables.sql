-- 创建回测相关数据库表
-- 迁移脚本: 003_create_backtest_tables.sql
-- 创建时间: 2024-01-01
-- 描述: 创建回测结果、任务和批次管理表


-- 创建回测任务表
CREATE TABLE IF NOT EXISTS backtest_tasks (
    id CHAR(36) PRIMARY KEY COMMENT '任务ID',
    batch_id CHAR(36) COMMENT '所属批次ID',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    config JSON NOT NULL COMMENT '回测配置',
    result_id CHAR(36) COMMENT '关联的结果ID',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_result_id (result_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回测任务表';

-- 创建回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id CHAR(36) PRIMARY KEY COMMENT '结果ID',
    task_id CHAR(36) COMMENT '关联的任务ID',
    batch_id CHAR(36) COMMENT '关联的批次ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    start_date DATE NOT NULL COMMENT '回测开始日期',
    end_date DATE NOT NULL COMMENT '回测结束日期',
    backtest_mode ENUM('historical_simulation', 'model_validation') NOT NULL COMMENT '回测模式',
    
    -- 基础配置信息
    initial_capital DECIMAL(15,2) NOT NULL COMMENT '初始资金',
    transaction_cost DECIMAL(8,6) DEFAULT 0.001 COMMENT '交易成本',
    
    -- 因子配置
    factor_config JSON NOT NULL COMMENT '因子配置信息',
    
    -- 核心绩效指标
    total_return DECIMAL(10,6) COMMENT '总收益率',
    annual_return DECIMAL(10,6) COMMENT '年化收益率',
    sharpe_ratio DECIMAL(10,6) COMMENT '夏普比率',
    sortino_ratio DECIMAL(10,6) COMMENT '索提诺比率',
    max_drawdown DECIMAL(10,6) COMMENT '最大回撤',
    volatility DECIMAL(10,6) COMMENT '波动率',
    
    -- 交易统计
    total_trades INT DEFAULT 0 COMMENT '总交易次数',
    winning_trades INT DEFAULT 0 COMMENT '盈利交易次数',
    losing_trades INT DEFAULT 0 COMMENT '亏损交易次数',
    win_rate DECIMAL(5,4) COMMENT '胜率',
    avg_win DECIMAL(10,6) COMMENT '平均盈利',
    avg_loss DECIMAL(10,6) COMMENT '平均亏损',
    profit_loss_ratio DECIMAL(10,6) COMMENT '盈亏比',
    
    -- 风险指标
    var_95 DECIMAL(10,6) COMMENT '95% VaR',
    var_99 DECIMAL(10,6) COMMENT '99% VaR',
    calmar_ratio DECIMAL(10,6) COMMENT 'Calmar比率',
    
    -- 详细数据
    daily_returns JSON COMMENT '每日收益率序列',
    equity_curve JSON COMMENT '资金曲线数据',
    trade_history JSON COMMENT '交易历史记录',
    position_history JSON COMMENT '持仓历史记录',
    
    -- 元数据
    execution_time DECIMAL(10,3) COMMENT '执行时间(秒)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_task_id (task_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_date_range (start_date, end_date),
    INDEX idx_backtest_mode (backtest_mode),
    INDEX idx_created_at (created_at),
    INDEX idx_total_return (total_return),
    INDEX idx_sharpe_ratio (sharpe_ratio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='回测结果表';
