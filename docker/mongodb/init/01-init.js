// MongoDB初始化脚本

// 切换到qtrade数据库
db = db.getSiblingDB('qtrade');

// 创建用户
db.createUser({
  user: 'qtrade',
  pwd: 'qtrade123',
  roles: [
    {
      role: 'readWrite',
      db: 'qtrade'
    }
  ]
});

// 创建新闻数据集合并设置索引
db.createCollection('news');
db.news.createIndex({ "publish_time": -1 });
db.news.createIndex({ "source": 1 });
db.news.createIndex({ "related_stocks.code": 1 });
db.news.createIndex({ "related_industries": 1 });
db.news.createIndex({ "created_at": -1 });

// 创建政策数据集合并设置索引
db.createCollection('policies');
db.policies.createIndex({ "publish_time": -1 });
db.policies.createIndex({ "source": 1 });
db.policies.createIndex({ "policy_type": 1 });
db.policies.createIndex({ "related_industries": 1 });
db.policies.createIndex({ "created_at": -1 });

// 创建数据采集日志集合
db.createCollection('collection_logs');
db.collection_logs.createIndex({ "timestamp": -1 });
db.collection_logs.createIndex({ "source": 1 });
db.collection_logs.createIndex({ "status": 1 });

// 创建系统配置集合
db.createCollection('system_configs');
db.system_configs.createIndex({ "key": 1 }, { unique: true });

// 插入初始配置数据
db.system_configs.insertMany([
  {
    key: 'news_collection_enabled',
    value: true,
    description: '新闻采集开关',
    updated_at: new Date()
  },
  {
    key: 'news_collection_interval',
    value: 300,
    description: '新闻采集间隔（秒）',
    updated_at: new Date()
  },
  {
    key: 'policy_collection_enabled',
    value: true,
    description: '政策采集开关',
    updated_at: new Date()
  },
  {
    key: 'policy_collection_interval',
    value: 3600,
    description: '政策采集间隔（秒）',
    updated_at: new Date()
  }
]);

// 显示初始化结果
print('MongoDB初始化完成');
print('数据库: ' + db.getName());
print('集合列表:');
db.getCollectionNames().forEach(function(collection) {
  print('  - ' + collection);
});

print('用户列表:');
db.getUsers().forEach(function(user) {
  print('  - ' + user.user + ' (roles: ' + JSON.stringify(user.roles) + ')');
});