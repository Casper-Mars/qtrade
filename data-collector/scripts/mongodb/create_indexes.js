// MongoDB索引创建脚本
// 用于为新闻和政策数据集合创建必要的索引

// 切换到qtrade数据库
use qtrade;

// ========== 新闻集合索引 ==========
print("Creating indexes for news collection...");

// 1. 发布时间索引（用于时间范围查询和排序）
db.news.createIndex(
    { "publish_time": -1 },
    { name: "idx_publish_time" }
);
print("✓ Created publish_time index for news");

// 2. 文本搜索索引（用于标题和内容的全文搜索）
db.news.createIndex(
    {
        "title": "text",
        "content": "text"
    },
    {
        name: "idx_text_search",
        default_language: "chinese",
        weights: {
            "title": 10,    // 标题权重更高
            "content": 1
        }
    }
);
print("✓ Created text search index for news");

// 3. 关联股票代码索引（用于按股票查询新闻）
db.news.createIndex(
    { "related_stocks.code": 1 },
    { name: "idx_related_stocks_code" }
);
print("✓ Created related_stocks.code index for news");

// 4. 关联行业索引（用于按行业查询新闻）
db.news.createIndex(
    { "related_industries": 1 },
    { name: "idx_related_industries" }
);
print("✓ Created related_industries index for news");

// 5. 来源索引（用于按来源查询新闻）
db.news.createIndex(
    { "source": 1 },
    { name: "idx_source" }
);
print("✓ Created source index for news");

// 6. 创建时间索引（用于数据管理）
db.news.createIndex(
    { "created_at": 1 },
    { name: "idx_created_at" }
);
print("✓ Created created_at index for news");

// 7. 复合索引：发布时间 + 来源（用于高效的时间范围和来源组合查询）
db.news.createIndex(
    {
        "publish_time": -1,
        "source": 1
    },
    { name: "idx_publish_time_source" }
);
print("✓ Created compound index (publish_time, source) for news");

// ========== 政策集合索引 ==========
print("\nCreating indexes for policies collection...");

// 1. 发布时间索引（用于时间范围查询和排序）
db.policies.createIndex(
    { "publish_time": -1 },
    { name: "idx_publish_time" }
);
print("✓ Created publish_time index for policies");

// 2. 生效时间索引（用于查询已生效的政策）
db.policies.createIndex(
    { "effective_time": 1 },
    { name: "idx_effective_time" }
);
print("✓ Created effective_time index for policies");

// 3. 文本搜索索引（用于标题和内容的全文搜索）
db.policies.createIndex(
    {
        "title": "text",
        "content": "text"
    },
    {
        name: "idx_text_search",
        default_language: "chinese",
        weights: {
            "title": 10,    // 标题权重更高
            "content": 1
        }
    }
);
print("✓ Created text search index for policies");

// 4. 政策类型索引（用于按类型查询政策）
db.policies.createIndex(
    { "policy_type": 1 },
    { name: "idx_policy_type" }
);
print("✓ Created policy_type index for policies");

// 5. 影响级别索引（用于按影响级别查询政策）
db.policies.createIndex(
    { "impact_level": 1 },
    { name: "idx_impact_level" }
);
print("✓ Created impact_level index for policies");

// 6. 关键词索引（用于按关键词查询政策）
db.policies.createIndex(
    { "keywords": 1 },
    { name: "idx_keywords" }
);
print("✓ Created keywords index for policies");

// 7. 发布机构索引（用于按发布机构查询政策）
db.policies.createIndex(
    { "source": 1 },
    { name: "idx_source" }
);
print("✓ Created source index for policies");

// 8. 创建时间索引（用于数据管理）
db.policies.createIndex(
    { "created_at": 1 },
    { name: "idx_created_at" }
);
print("✓ Created created_at index for policies");

// 9. 复合索引：政策类型 + 影响级别 + 发布时间（用于高效的组合查询）
db.policies.createIndex(
    {
        "policy_type": 1,
        "impact_level": 1,
        "publish_time": -1
    },
    { name: "idx_policy_type_impact_time" }
);
print("✓ Created compound index (policy_type, impact_level, publish_time) for policies");

// 10. 复合索引：发布机构 + 发布时间（用于按机构查询最新政策）
db.policies.createIndex(
    {
        "source": 1,
        "publish_time": -1
    },
    { name: "idx_source_publish_time" }
);
print("✓ Created compound index (source, publish_time) for policies");

// ========== 显示创建的索引 ==========
print("\n========== News Collection Indexes ==========");
db.news.getIndexes().forEach(function(index) {
    print("Index: " + index.name + " -> " + JSON.stringify(index.key));
});

print("\n========== Policies Collection Indexes ==========");
db.policies.getIndexes().forEach(function(index) {
    print("Index: " + index.name + " -> " + JSON.stringify(index.key));
});

print("\n✅ All indexes created successfully!");