# Tushare Pro 数据覆盖分析报告

## 1. 调研概述

本报告基于对 Tushare Pro 平台的深入调研，分析其数据接口是否能满足 `design_backend.md` 中设计的数据库表结构需求。

### 1.1 Tushare Pro 平台简介

Tushare Pro 是一个专业的金融数据接口平台，提供：
- **数据丰富性**：股票、基金、期货、数字货币等行情数据，公司财务、基金经理等基本面数据
- **获取简便性**：SDK开发包支持多种语言，同时提供HTTP Restful接口
- **数据稳定性**：相比免费版本，Pro版本在数据稳定性和获取速率上大幅提升

### 1.2 积分机制

- **基础积分**：注册后100积分 + 完善个人信息20积分 = 120积分
- **权限控制**：不同接口需要不同积分等级
- **获取方式**：参与社区维护、贡献代码、捐助等方式获取更多积分

## 2. 数据接口覆盖分析

### 2.1 股票基础数据覆盖

#### 2.1.1 设计需求 vs Tushare Pro 接口

**设计表结构 (stock_info)**：
```sql
symbol VARCHAR(10) NOT NULL UNIQUE COMMENT '股票代码',
name VARCHAR(100) NOT NULL COMMENT '股票名称',
industry VARCHAR(50) COMMENT '所属行业',
market VARCHAR(20) NOT NULL COMMENT '交易市场',
list_date DATE COMMENT '上市日期',
market_cap DECIMAL(20,2) COMMENT '市值',
status TINYINT DEFAULT 1 COMMENT '状态：1-正常，0-停牌'
```

**Tushare Pro 对应接口**：
- **接口名称**：`stock_basic` (股票列表)
- **积分要求**：120积分（基础权限即可）
- **数据字段**：
  - `ts_code`: TS股票代码 ✅ 对应 symbol
  - `symbol`: 股票代码 ✅ 对应 symbol
  - `name`: 股票名称 ✅ 对应 name
  - `area`: 地域 ✅ 可用于地域分析
  - `industry`: 所属行业 ✅ 对应 industry
  - `market`: 市场类型（主板/创业板/科创板/CDR） ✅ 对应 market
  - `exchange`: 交易所代码 ✅ 补充信息
  - `list_date`: 上市日期 ✅ 对应 list_date
  - `list_status`: 上市状态 ✅ 对应 status
  - `is_hs`: 是否沪深港通标的 ✅ 补充信息

**覆盖度评估**：✅ **基础权限即可**
- 所有设计字段都能从 Tushare Pro 获取
- **优势**：仅需120积分即可访问股票基础信息接口
- 市值数据需要通过 `daily_basic` 接口补充获取（需要2000积分）

### 2.2 股票行情数据覆盖

#### 2.2.1 设计需求 vs Tushare Pro 接口

**设计表结构 (stock_quotes)**：
```sql
symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
name VARCHAR(50) NOT NULL COMMENT '股票名称',
trade_date DATE NOT NULL COMMENT '交易日期',
current_price DECIMAL(10,3) NOT NULL COMMENT '当前价格',
open_price DECIMAL(10,3) NOT NULL COMMENT '开盘价',
high_price DECIMAL(10,3) NOT NULL COMMENT '最高价',
low_price DECIMAL(10,3) NOT NULL COMMENT '最低价',
close_price DECIMAL(10,3) NOT NULL COMMENT '收盘价',
volume BIGINT NOT NULL COMMENT '成交量',
amount DECIMAL(20,2) NOT NULL COMMENT '成交额',
change_amount DECIMAL(10,3) COMMENT '涨跌额',
change_percent DECIMAL(8,4) COMMENT '涨跌幅',
turnover_rate DECIMAL(8,4) COMMENT '换手率',
pe_ratio DECIMAL(10,3) COMMENT '市盈率',
pb_ratio DECIMAL(10,3) COMMENT '市净率',
market_cap DECIMAL(20,2) COMMENT '总市值'
```

**Tushare Pro 对应接口**：

1. **主要接口**：`daily` (日线行情)
   - **积分要求**：120积分
   - **数据字段**：
     - `ts_code`: TS代码 ✅ 对应 symbol
     - `trade_date`: 交易日期 ✅ 对应 trade_date
     - `open`: 开盘价 ✅ 对应 open_price
     - `high`: 最高价 ✅ 对应 high_price
     - `low`: 最低价 ✅ 对应 low_price
     - `close`: 收盘价 ✅ 对应 close_price
     - `pre_close`: 昨收价 ✅ 用于计算涨跌额
     - `change`: 涨跌额 ✅ 对应 change_amount
     - `pct_chg`: 涨跌幅 ✅ 对应 change_percent
     - `vol`: 成交量 ✅ 对应 volume
     - `amount`: 成交额 ✅ 对应 amount

2. **补充接口**：`daily_basic` (每日指标)
   - **积分要求**：2000积分
   - **数据字段**：
     - `turnover_rate`: 换手率 ✅ 对应 turnover_rate
     - `turnover_rate_f`: 换手率（自由流通股） ✅ 补充信息
     - `pe`: 市盈率 ✅ 对应 pe_ratio
     - `pb`: 市净率 ✅ 对应 pb_ratio
     - `total_mv`: 总市值 ✅ 对应 market_cap
     - `circ_mv`: 流通市值 ✅ 补充信息

**覆盖度评估**：⚠️ **部分需要高积分权限**
- 基础行情数据（开高低收、成交量等）：120积分即可获取
- 高级指标数据（换手率、市盈率、市净率、市值等）：需要2000积分
- **建议**：可先实现基础行情数据采集，后续补充高级指标
- current_price 可以使用 close_price 或通过实时接口获取

### 2.3 财务数据覆盖

#### 2.3.1 设计需求 vs Tushare Pro 接口

**设计表结构 (financial_data)**：
```sql
symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
report_date DATE NOT NULL COMMENT '报告期',
report_type ENUM('annual', 'quarterly') NOT NULL COMMENT '报告类型',
total_assets DECIMAL(20,2) COMMENT '总资产',
total_liabilities DECIMAL(20,2) COMMENT '总负债',
shareholders_equity DECIMAL(20,2) COMMENT '股东权益',
revenue DECIMAL(20,2) COMMENT '营业收入',
net_profit DECIMAL(20,2) COMMENT '净利润',
operating_cash_flow DECIMAL(20,2) COMMENT '经营活动现金流',
pe_ratio DECIMAL(8,4) COMMENT 'PE比率',
pb_ratio DECIMAL(8,4) COMMENT 'PB比率',
roe DECIMAL(8,4) COMMENT 'ROE',
roa DECIMAL(8,4) COMMENT 'ROA'
```

**Tushare Pro 对应接口**：

1. **利润表接口**：`income`
   - **积分要求**：2000积分
   - **关键字段**：
     - `revenue`: 营业收入 ✅ 对应 revenue
     - `n_income`: 净利润 ✅ 对应 net_profit

2. **资产负债表接口**：`balancesheet`
   - **积分要求**：2000积分
   - **关键字段**：
     - `total_assets`: 资产总计 ✅ 对应 total_assets
     - `total_liab`: 负债合计 ✅ 对应 total_liabilities
     - `total_hldr_eqy_exc_min_int`: 股东权益合计 ✅ 对应 shareholders_equity

3. **现金流量表接口**：`cashflow`
   - **积分要求**：2000积分
   - **关键字段**：
     - `n_cashflow_act`: 经营活动现金流量净额 ✅ 对应 operating_cash_flow

4. **财务指标接口**：`fina_indicator`
   - **积分要求**：2000积分
   - **关键字段**：
     - `roe`: 净资产收益率 ✅ 对应 roe
     - `roa`: 总资产收益率 ✅ 对应 roa
     - `pe`: 市盈率 ✅ 对应 pe_ratio
     - `pb`: 市净率 ✅ 对应 pb_ratio

**覆盖度评估**：⚠️ **需要高积分权限**
- 所有设计字段都能从 Tushare Pro 获取
- **限制**：需要2000积分才能访问财务数据接口
- **解决方案**：
  - 申请学生认证获取免费高级权限
  - 参与社区贡献获取积分
  - 考虑付费获取积分

### 2.4 市场指数数据覆盖

#### 2.4.1 设计需求 vs Tushare Pro 接口

**设计表结构 (market_indices)**：
```sql
index_code VARCHAR(20) NOT NULL COMMENT '指数代码',
index_name VARCHAR(100) NOT NULL COMMENT '指数名称',
trade_date DATE NOT NULL COMMENT '交易日期',
open_price DECIMAL(10,3) NOT NULL COMMENT '开盘点数',
high_price DECIMAL(10,3) NOT NULL COMMENT '最高点数',
low_price DECIMAL(10,3) NOT NULL COMMENT '最低点数',
close_price DECIMAL(10,3) NOT NULL COMMENT '收盘点数',
volume BIGINT COMMENT '成交量',
amount DECIMAL(20,2) COMMENT '成交额',
change_rate DECIMAL(8,4) COMMENT '涨跌幅'
```

**Tushare Pro 对应接口**：
- **接口名称**：`index_daily` (指数日线行情)
- **积分要求**：2000积分
- **数据字段**：完全覆盖所有设计字段

**覆盖度评估**：⚠️ **需要高积分权限**

## 3. 数据获取策略建议

### 3.1 积分获取策略

1. **基础数据（120积分）**：
   - 股票基础信息：`stock_basic` (股票代码、名称、行业、上市日期等)
   - 股票基础行情：`daily` (仅开高低收、成交量等基础数据)
   - 交易日历：`trade_cal` (需要验证积分要求)

2. **高级数据（2000积分）**：
   - 股票高级指标：`daily_basic` (换手率、市盈率、市净率、市值等)
   - 市场指数数据：`index_daily`
   - 财务数据：`income` + `balancesheet` + `cashflow` + `fina_indicator`
   - **获取方式**：
     - 学生认证（推荐）
     - 社区贡献
     - 付费获取

### 3.2 数据采集频率建议

1. **股票基础信息**：每周更新一次
2. **股票行情数据**：每日收盘后更新
3. **财务数据**：季度更新（财报发布后）
4. **市场指数**：每日收盘后更新

### 3.3 API调用限制

- **频率限制**：每分钟调用次数有限制
- **解决方案**：使用 `time.sleep()` 控制调用频率
- **批量获取**：优先使用批量接口减少调用次数

## 4. 设计文档更新建议

### 4.1 行情表分表策略调整

根据用户要求，建议简化 `stock_quotes` 表设计：

```sql
-- 移除分区设计，简化表结构
CREATE TABLE stock_quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL COMMENT '股票代码',
    name VARCHAR(50) NOT NULL COMMENT '股票名称',
    trade_date DATE NOT NULL COMMENT '交易日期',
    -- ... 其他字段保持不变
    UNIQUE KEY uk_symbol_date (symbol, trade_date),
    INDEX idx_symbol (symbol),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票行情数据表';
-- 移除分区定义
```

### 4.2 数据源配置更新

在配置文件中添加 Tushare Pro 相关配置：

```yaml
tushare:
  token: "your_tushare_token"
  base_url: "http://api.tushare.pro"
  timeout: 30
  retry_times: 3
  rate_limit: 200  # 每分钟调用次数限制
```

## 5. 结论

### 5.1 数据覆盖度总结

| 数据类型 | 覆盖度 | 积分要求 | 备注 |
|---------|--------|----------|------|
| 股票基础信息 | ✅ 100% | 120积分 | 基础权限即可 |
| 股票基础行情 | ✅ 100% | 120积分 | 仅开高低收、成交量等 |
| 股票高级指标 | ✅ 100% | 2000积分 | 换手率、市盈率、市值等 |
| 市场指数数据 | ✅ 100% | 2000积分 | 需要高级权限 |
| 财务数据 | ✅ 100% | 2000积分 | 需要高级权限 |

### 5.2 实施建议

1. **立即可实施**：使用基础积分（120积分）获取股票基础信息和基础行情数据（股票列表、开高低收、成交量等）
2. **积分提升**：申请学生认证或参与社区获取2000积分，解锁完整数据权限
3. **分阶段开发**：
   - 第一阶段：实现股票基础信息和基础行情数据采集（120积分）
   - 第二阶段：补充高级指标和指数数据（2000积分）
   - 第三阶段：补充财务数据（2000积分）
4. **表结构简化**：按用户要求移除行情表分区设计

### 5.3 风险评估

- **低风险**：股票基础信息和基础行情数据（股票列表、开高低收、成交量）获取无障碍
- **中高风险**：部分核心数据（高级指标、指数、财务数据）需要2000积分
- **技术风险**：API调用频率限制需要合理控制
- **积分风险**：需要通过学生认证、社区贡献或付费方式获取足够积分

**总体评估**：Tushare Pro 能够满足数据需求，120积分即可获取股票基础信息和行情数据，实施难度较低

## 修改记录

- [2024-01-20] 新增 完成Tushare Pro数据覆盖分析，确认可满足所有数据需求
- [2024-01-20] 修改 移除stock_quotes表分区设计，简化为单表结构
- [2024-01-20] 修正 将daily_basic、index_daily接口积分要求更正为2000积分
- [2024-01-20] 修正 确认stock_basic接口仅需120积分，降低实施难度