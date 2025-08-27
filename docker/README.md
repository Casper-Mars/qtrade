# qtrade项目Docker环境

本目录包含qtrade项目的Docker基础设施配置，提供MySQL、Redis、MongoDB等服务。

## 目录结构

```
docker/
├── docker-compose.yml     # Docker Compose配置文件
├── start.sh              # 启动脚本
├── stop.sh               # 停止脚本
├── README.md             # 说明文档
├── mysql/
│   └── init/
│       └── 01-init.sql   # MySQL初始化脚本
├── redis/
│   └── redis.conf        # Redis配置文件
└── mongodb/
    └── init/
        └── 01-init.js    # MongoDB初始化脚本
```

## 服务列表

### 核心服务

| 服务 | 端口 | 用户名 | 密码 | 数据库/键空间 |
|------|------|--------|------|---------------|
| MySQL | 3306 | qtrade | qtrade123 | qtrade |
| Redis | 6379 | - | - | - |
| MongoDB | 27017 | qtrade | qtrade123 | qtrade |

## 快速开始

### 1. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
./start.sh

# 方式2: 直接使用docker compose
docker compose up -d
```

### 2. 检查服务状态

```bash
docker compose ps
```

### 3. 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f mysql
docker compose logs -f redis
docker compose logs -f mongodb
```

### 4. 停止服务

```bash
# 方式1: 使用停止脚本（推荐）
./stop.sh

# 方式2: 直接使用docker compose
docker compose down
```

## 数据持久化

所有数据都通过Docker卷进行持久化存储：

- `mysql_data`: MySQL数据目录
- `redis_data`: Redis数据目录
- `mongodb_data`: MongoDB数据目录

## 网络配置

所有服务都在`qtrade-network`网络中，使用子网`172.20.0.0/16`。

## 连接配置

### 应用程序连接配置

```yaml
# MySQL
host: localhost
port: 3306
database: qtrade
username: qtrade
password: qtrade123

# Redis
host: localhost
port: 6379

# MongoDB
host: localhost
port: 27017
database: qtrade
username: qtrade
password: qtrade123
```

### Docker内部服务连接

如果应用程序也运行在Docker中，使用服务名作为主机名：

```yaml
# MySQL
host: mysql
port: 3306

# Redis
host: redis
port: 6379

# MongoDB
host: mongodb
port: 27017
```

## 常用命令

### 数据库操作

```bash
# 连接MySQL
docker compose exec mysql mysql -u qtrade -p qtrade

# 连接Redis
docker compose exec redis redis-cli

# 连接MongoDB
docker compose exec mongodb mongosh -u qtrade -p qtrade123 --authenticationDatabase qtrade
```

### 数据备份

```bash
# MySQL备份
docker compose exec mysql mysqldump -u qtrade -p qtrade > backup_mysql.sql

# MongoDB备份
docker compose exec mongodb mongodump --db qtrade --username qtrade --password qtrade123 --out /tmp/backup
docker cp qtrade-mongodb:/tmp/backup ./backup_mongodb
```

### 数据恢复

```bash
# MySQL恢复
docker compose exec -T mysql mysql -u qtrade -p qtrade < backup_mysql.sql

# MongoDB恢复
docker cp ./backup_mongodb qtrade-mongodb:/tmp/restore
docker compose exec mongodb mongorestore --db qtrade --username qtrade --password qtrade123 /tmp/restore/qtrade
```

## 故障排除

### 常见问题

1. **端口冲突**
   - 确保本地没有其他服务占用相同端口
   - 可以修改`docker-compose.yml`中的端口映射

2. **权限问题**
   - 确保启动脚本有执行权限：`chmod +x start.sh stop.sh`

3. **数据卷问题**
   - 如需重置数据：`docker compose down -v`
   - 注意：这会删除所有数据

4. **网络问题**
   - 清理Docker网络：`docker network prune -f`

### 日志查看

```bash
# 查看容器状态
docker compose ps

# 查看详细日志
docker compose logs --details

# 实时跟踪日志
docker compose logs -f --tail=100
```

## 开发环境配置

### 环境变量

建议在应用程序中使用环境变量配置数据库连接：

```bash
# .env文件示例
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=qtrade
MYSQL_USERNAME=qtrade
MYSQL_PASSWORD=qtrade123

REDIS_HOST=localhost
REDIS_PORT=6379

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=qtrade
MONGODB_USERNAME=qtrade
MONGODB_PASSWORD=qtrade123
```

### 性能调优

根据开发需要，可以调整以下配置：

1. **MySQL配置**：修改`mysql/my.cnf`
2. **Redis配置**：修改`redis/redis.conf`
3. **MongoDB配置**：在`docker-compose.yml`中添加配置参数

## 安全注意事项

⚠️ **重要提醒**：

1. 本配置仅用于开发环境
2. 生产环境请修改默认密码
3. 生产环境请配置防火墙规则
4. 定期备份重要数据

## 更新和维护

### 更新镜像

```bash
# 拉取最新镜像
docker compose pull

# 重新创建容器
docker compose up -d --force-recreate
```

### 清理资源

```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有未使用的资源
docker system prune -a
```