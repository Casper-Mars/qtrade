-- 因子组合配置表创建脚本
-- 创建时间: 2024-01-28
-- 描述: 创建因子组合配置表，用于存储因子组合的配置信息

-- ==================== 因子组合配置表 ====================
CREATE TABLE IF NOT EXISTS factor_combinations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    combination_id VARCHAR(64) NOT NULL COMMENT '组合唯一标识（UUID）',
    name VARCHAR(100) NOT NULL COMMENT '组合名称',
    description TEXT COMMENT '组合描述',
    factors JSON NOT NULL COMMENT '因子配置列表（JSON格式）',
    total_weight DECIMAL(10,6) NOT NULL DEFAULT 0.000000 COMMENT '总权重',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1-启用，0-停用',
    created_by VARCHAR(100) COMMENT '创建者',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='因子组合配置表';

-- 因子组合配置表索引
CREATE INDEX idx_combination_id ON factor_combinations(combination_id);
CREATE INDEX idx_name ON factor_combinations(name);
CREATE INDEX idx_created_by ON factor_combinations(created_by);
CREATE INDEX idx_created_at ON factor_combinations(created_at);
CREATE INDEX idx_is_active ON factor_combinations(is_active);

-- 因子组合配置表唯一约束
CREATE UNIQUE INDEX uk_combination_id ON factor_combinations(combination_id);

-- ==================== 数据表注释和说明 ====================

/*
表设计说明:

1. 因子组合配置表 (factor_combinations)
   - 存储因子组合的完整配置信息
   - combination_id使用UUID作为业务主键
   - factors字段使用JSON格式存储因子配置列表
   - 支持软删除（通过is_active字段）
   - 支持按创建者查询配置

字段说明:
- id: 数据库自增主键
- combination_id: 业务唯一标识，使用UUID格式
- name: 组合名称，用于显示和搜索
- description: 组合描述，可选字段
- factors: JSON格式存储因子配置列表，包含每个因子的详细信息
- total_weight: 所有因子权重的总和，用于验证
- is_active: 软删除标记，1表示启用，0表示停用
- created_by: 创建者标识，用于权限控制
- created_at: 创建时间
- updated_at: 更新时间

索引策略:
- combination_id: 主要查询字段，建立唯一索引
- name: 支持按名称搜索
- created_by: 支持按创建者查询
- created_at: 支持按时间排序
- is_active: 支持过滤活跃配置

性能优化:
- 使用InnoDB引擎支持事务
- JSON字段存储复杂的因子配置
- 合理的索引设计避免全表扫描
- 唯一约束防止重复配置
*/