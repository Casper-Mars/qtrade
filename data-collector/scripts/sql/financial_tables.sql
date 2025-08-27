-- 财务报表数据表
CREATE TABLE IF NOT EXISTS financial_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
    ts_code VARCHAR(12) NOT NULL COMMENT 'Tushare代码',
    ann_date DATE NOT NULL COMMENT '公告日期',
    f_date DATE NOT NULL COMMENT '报告期',
    end_date DATE NOT NULL COMMENT '报告期结束日期',
    report_type VARCHAR(10) NOT NULL COMMENT '报告类型(1-年报,2-半年报,3-季报)',
    
    -- 资产负债表字段
    total_assets DECIMAL(20,2) COMMENT '总资产(万元)',
    total_liab DECIMAL(20,2) COMMENT '总负债(万元)',
    total_hldr_eqy_exc_min_int DECIMAL(20,2) COMMENT '股东权益合计(万元)',
    total_cur_assets DECIMAL(20,2) COMMENT '流动资产合计(万元)',
    total_cur_liab DECIMAL(20,2) COMMENT '流动负债合计(万元)',
    money_funds DECIMAL(20,2) COMMENT '货币资金(万元)',
    
    -- 利润表字段
    revenue DECIMAL(20,2) COMMENT '营业总收入(万元)',
    oper_cost DECIMAL(20,2) COMMENT '营业总成本(万元)',
    n_income DECIMAL(20,2) COMMENT '净利润(万元)',
    n_income_attr_p DECIMAL(20,2) COMMENT '归属于母公司所有者的净利润(万元)',
    basic_eps DECIMAL(10,4) COMMENT '基本每股收益(元)',
    
    -- 现金流量表字段
    n_cf_fr_oa DECIMAL(20,2) COMMENT '经营活动产生的现金流量净额(万元)',
    n_cf_fr_inv_a DECIMAL(20,2) COMMENT '投资活动产生的现金流量净额(万元)',
    n_cf_fr_fnc_a DECIMAL(20,2) COMMENT '筹资活动产生的现金流量净额(万元)',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_symbol_end_date_type (symbol, end_date, report_type),
    INDEX idx_symbol (symbol),
    INDEX idx_ts_code (ts_code),
    INDEX idx_end_date (end_date),
    INDEX idx_ann_date (ann_date),
    INDEX idx_report_type (report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务报表数据表';

-- 财务指标数据表
CREATE TABLE IF NOT EXISTS financial_indicators (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
    ts_code VARCHAR(12) NOT NULL COMMENT 'Tushare代码',
    ann_date DATE NOT NULL COMMENT '公告日期',
    end_date DATE NOT NULL COMMENT '报告期',
    
    -- 盈利能力指标
    roe DECIMAL(8,4) COMMENT '净资产收益率(%)',
    roa DECIMAL(8,4) COMMENT '总资产收益率(%)',
    roic DECIMAL(8,4) COMMENT '投入资本回报率(%)',
    gross_margin DECIMAL(8,4) COMMENT '毛利率(%)',
    net_margin DECIMAL(8,4) COMMENT '净利率(%)',
    oper_margin DECIMAL(8,4) COMMENT '营业利润率(%)',
    
    -- 成长能力指标
    revenue_yoy DECIMAL(8,4) COMMENT '营业收入同比增长率(%)',
    n_income_yoy DECIMAL(8,4) COMMENT '净利润同比增长率(%)',
    assets_yoy DECIMAL(8,4) COMMENT '总资产同比增长率(%)',
    
    -- 偿债能力指标
    debt_to_assets DECIMAL(8,4) COMMENT '资产负债率(%)',
    current_ratio DECIMAL(8,4) COMMENT '流动比率',
    quick_ratio DECIMAL(8,4) COMMENT '速动比率',
    
    -- 运营能力指标
    asset_turnover DECIMAL(8,4) COMMENT '总资产周转率',
    inventory_turnover DECIMAL(8,4) COMMENT '存货周转率',
    ar_turnover DECIMAL(8,4) COMMENT '应收账款周转率',
    
    -- 估值指标
    pe DECIMAL(10,4) COMMENT '市盈率',
    pb DECIMAL(10,4) COMMENT '市净率',
    ps DECIMAL(10,4) COMMENT '市销率',
    pcf DECIMAL(10,4) COMMENT '市现率',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_symbol_end_date (symbol, end_date),
    INDEX idx_symbol (symbol),
    INDEX idx_ts_code (ts_code),
    INDEX idx_end_date (end_date),
    INDEX idx_ann_date (ann_date),
    INDEX idx_roe (roe),
    INDEX idx_roa (roa),
    INDEX idx_pe (pe),
    INDEX idx_pb (pb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务指标数据表';