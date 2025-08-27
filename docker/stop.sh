#!/bin/bash

# qtrade项目Docker环境停止脚本

set -e

echo "=== qtrade项目Docker环境停止 ==="

# 进入docker目录
cd "$(dirname "$0")"

echo "当前目录: $(pwd)"

# 停止所有服务
echo "停止所有服务..."
docker compose down

# 显示停止后的状态
echo "检查容器状态..."
docker compose ps

echo ""
echo "=== 停止完成 ==="
echo "所有qtrade相关的Docker容器已停止"
echo ""
echo "如需完全清理（包括数据卷），请运行:"
echo "  docker compose down -v"
echo ""
echo "如需清理所有未使用的Docker资源，请运行:"
echo "  docker system prune -a"