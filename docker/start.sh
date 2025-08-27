#!/bin/bash

# qtrade项目Docker环境启动脚本

set -e

echo "🚀 启动qtrade项目Docker环境..."
echo "======================================"

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装或未启动"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker服务未启动"
    exit 1
fi

# 启动所有服务
echo "📦 启动所有服务..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker compose ps

echo ""
echo "✅ qtrade Docker环境启动完成！"
echo "======================================"
echo "📊 服务访问信息："
echo "  MySQL:     localhost:3306"
echo "  Redis:     localhost:6379"
echo "  MongoDB:   localhost:27017"
echo ""
echo "📝 默认账号信息："
echo "  MySQL:   用户名: qtrade, 密码: qtrade123"
echo "  MongoDB: 用户名: qtrade, 密码: qtrade123"
echo "======================================"