-- 大盘指数基础信息表
CREATE TABLE IF NOT EXISTS market_indexes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    index_code VARCHAR(20) NOT NULL UNIQUE COMMENT '指数代码',
    index_name VARCHAR(100) NOT NULL COMMENT '指数名称',
    market VARCHAR(20) COMMENT '市场类型',
    publisher VARCHAR(50) COMMENT '发布方',
    category VARCHAR(50) COMMENT '指数类别',
    base_date DATE COMMENT '基期日期',
    base_point DECIMAL(10,2) COMMENT '基点',
    list_date DATE COMMENT '发布日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_index_code (index_code),
    INDEX idx_market (market),
    INDEX idx_category (category),
    INDEX idx_publisher (publisher)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='大盘指数基础信息表';

-- 指数行情数据表
CREATE TABLE IF NOT EXISTS index_quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    index_code VARCHAR(20) NOT NULL COMMENT '指数代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,2) COMMENT '开盘点数',
    high DECIMAL(10,2) COMMENT '最高点数',
    low DECIMAL(10,2) COMMENT '最低点数',
    close DECIMAL(10,2) COMMENT '收盘点数',
    pre_close DECIMAL(10,2) COMMENT '昨收点数',
    change_amount DECIMAL(10,2) COMMENT '涨跌点数',
    pct_chg DECIMAL(8,4) COMMENT '涨跌幅(%)',
    vol BIGINT COMMENT '成交量(手)',
    amount DECIMAL(15,2) COMMENT '成交额(千元)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_index_code_date (index_code, trade_date),
    INDEX idx_index_code (index_code),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数行情数据表';

-- 行业指数数据表
CREATE TABLE IF NOT EXISTS industry_indexes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    index_code VARCHAR(20) NOT NULL COMMENT '指数代码',
    index_name VARCHAR(100) NOT NULL COMMENT '指数名称',
    industry_level VARCHAR(20) COMMENT '行业级别(一级/二级/三级)',
    parent_code VARCHAR(20) COMMENT '父级行业代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10,2) COMMENT '开盘点数',
    high DECIMAL(10,2) COMMENT '最高点数',
    low DECIMAL(10,2) COMMENT '最低点数',
    close DECIMAL(10,2) COMMENT '收盘点数',
    pre_close DECIMAL(10,2) COMMENT '昨收点数',
    change_amount DECIMAL(10,2) COMMENT '涨跌点数',
    pct_chg DECIMAL(8,4) COMMENT '涨跌幅(%)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_index_code_date (index_code, trade_date),
    INDEX idx_index_code (index_code),
    INDEX idx_industry_level (industry_level),
    INDEX idx_parent_code (parent_code),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行业指数数据表';

-- 板块分类表
CREATE TABLE IF NOT EXISTS sectors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sector_code VARCHAR(20) NOT NULL UNIQUE COMMENT '板块代码',
    sector_name VARCHAR(100) NOT NULL COMMENT '板块名称',
    sector_type VARCHAR(20) COMMENT '板块类型(概念/地域/风格)',
    parent_code VARCHAR(20) COMMENT '父级板块代码',
    level INT COMMENT '板块层级',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sector_code (sector_code),
    INDEX idx_sector_type (sector_type),
    INDEX idx_parent_code (parent_code),
    INDEX idx_level (level),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='板块分类表';

-- 板块成分股表
CREATE TABLE IF NOT EXISTS sector_constituents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sector_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(50) COMMENT '股票名称',
    weight DECIMAL(8,4) COMMENT '权重(%)',
    in_date DATE COMMENT '纳入日期',
    out_date DATE COMMENT '剔除日期',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sector_stock (sector_code, stock_code),
    INDEX idx_sector_code (sector_code),
    INDEX idx_stock_code (stock_code),
    INDEX idx_in_date (in_date),
    INDEX idx_out_date (out_date),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='板块成分股表';