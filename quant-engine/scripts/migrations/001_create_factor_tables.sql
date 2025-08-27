-- 因子数据表创建脚本
-- 创建时间: 2024-01-01
-- 描述: 创建技术因子、基本面因子、市场因子和新闻情绪因子数据表

-- ==================== 技术因子表 ====================
CREATE TABLE IF NOT EXISTS technical_factors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    factor_name VARCHAR(100) NOT NULL COMMENT '因子名称',
    factor_value DECIMAL(20,8) NOT NULL COMMENT '因子值',
    trade_date DATE NOT NULL COMMENT '交易日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技术因子数据表';

-- 技术因子表索引
CREATE INDEX idx_technical_stock_date ON technical_factors(stock_code, trade_date);
CREATE INDEX idx_technical_factor_name ON technical_factors(factor_name);
CREATE INDEX idx_technical_trade_date ON technical_factors(trade_date);
CREATE INDEX idx_technical_created_at ON technical_factors(created_at);

-- 技术因子表唯一约束
CREATE UNIQUE INDEX uk_technical_stock_factor_date ON technical_factors(stock_code, factor_name, trade_date);

-- ==================== 基本面因子表 ====================
CREATE TABLE IF NOT EXISTS fundamental_factors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    factor_name VARCHAR(100) NOT NULL COMMENT '因子名称',
    factor_value DECIMAL(20,8) NOT NULL COMMENT '因子值',
    report_period VARCHAR(20) NOT NULL COMMENT '报告期',
    ann_date DATE NOT NULL COMMENT '公告日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='基本面因子数据表';

-- 基本面因子表索引
CREATE INDEX idx_fundamental_stock_period ON fundamental_factors(stock_code, report_period);
CREATE INDEX idx_fundamental_factor_name ON fundamental_factors(factor_name);
CREATE INDEX idx_fundamental_ann_date ON fundamental_factors(ann_date);
CREATE INDEX idx_fundamental_created_at ON fundamental_factors(created_at);

-- 基本面因子表唯一约束
CREATE UNIQUE INDEX uk_fundamental_stock_factor_period ON fundamental_factors(stock_code, factor_name, report_period);

-- ==================== 市场因子表 ====================
CREATE TABLE IF NOT EXISTS market_factors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    factor_name VARCHAR(100) NOT NULL COMMENT '因子名称',
    factor_value DECIMAL(20,8) NOT NULL COMMENT '因子值',
    trade_date DATE NOT NULL COMMENT '交易日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场因子数据表';

-- 市场因子表索引
CREATE INDEX idx_market_stock_date ON market_factors(stock_code, trade_date);
CREATE INDEX idx_market_factor_name ON market_factors(factor_name);
CREATE INDEX idx_market_trade_date ON market_factors(trade_date);
CREATE INDEX idx_market_created_at ON market_factors(created_at);

-- 市场因子表唯一约束
CREATE UNIQUE INDEX uk_market_stock_factor_date ON market_factors(stock_code, factor_name, trade_date);

-- ==================== 新闻情绪因子表 ====================
CREATE TABLE IF NOT EXISTS news_sentiment_factors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    factor_value DECIMAL(10,6) NOT NULL COMMENT '情绪因子值',
    calculation_date DATE NOT NULL COMMENT '计算日期',
    news_count INT NOT NULL DEFAULT 0 COMMENT '新闻数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻情绪因子数据表';

-- 新闻情绪因子表索引
CREATE INDEX idx_sentiment_stock_date ON news_sentiment_factors(stock_code, calculation_date);
CREATE INDEX idx_sentiment_calculation_date ON news_sentiment_factors(calculation_date);
CREATE INDEX idx_sentiment_created_at ON news_sentiment_factors(created_at);

-- 新闻情绪因子表唯一约束
CREATE UNIQUE INDEX uk_sentiment_stock_date ON news_sentiment_factors(stock_code, calculation_date);

-- ==================== 数据表注释和说明 ====================

/*
表设计说明:

1. 技术因子表 (technical_factors)
   - 存储各种技术指标因子，如MA、RSI、MACD等
   - 按股票代码、因子名称、交易日期建立唯一约束
   - 支持高频查询和时间序列分析

2. 基本面因子表 (fundamental_factors)
   - 存储财务指标相关因子，如ROE、PE、PB等
   - 按股票代码、因子名称、报告期建立唯一约束
   - 支持季度和年度数据查询

3. 市场因子表 (market_factors)
   - 存储市场相关因子，如换手率、成交量等
   - 按股票代码、因子名称、交易日期建立唯一约束
   - 支持市场行为分析

4. 新闻情绪因子表 (news_sentiment_factors)
   - 存储基于新闻文本分析的情绪因子
   - 按股票代码、计算日期建立唯一约束
   - 包含新闻数量统计信息

索引策略:
- 主要查询路径: 股票代码 + 日期/期间
- 因子名称索引: 支持按因子类型查询
- 时间索引: 支持时间序列分析
- 创建时间索引: 支持数据管理和清理

性能优化:
- 使用InnoDB引擎支持事务和外键
- 合理的索引设计避免全表扫描
- 唯一约束防止数据重复
- 适当的字段长度和数据类型
*/