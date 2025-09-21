#!/bin/bash

# 快速Docker服务更新脚本
# 使用方法: ./update-service.sh <服务名> [--no-cache]

SERVICE_NAME=$1
NO_CACHE=$2

if [ -z "$SERVICE_NAME" ]; then
    echo "使用方法: $0 <服务名> [--no-cache]"
    echo "可用服务: mirix-backend mirix-frontend mirix-mcp-sse all"
    echo "示例: $0 mirix-backend"
    echo "示例: $0 mirix-frontend --no-cache"
    exit 1
fi

echo "🔄 开始更新服务: $SERVICE_NAME"

# 构建服务
echo "📦 构建服务..."
if [ "$NO_CACHE" = "--no-cache" ]; then
    docker-compose build --no-cache $SERVICE_NAME
else
    docker-compose build $SERVICE_NAME
fi

# 停止服务
echo "⏹️ 停止服务..."
if [ "$SERVICE_NAME" = "all" ]; then
    docker-compose down
else
    docker-compose stop $SERVICE_NAME
fi

# 启动服务
echo "🚀 启动服务..."
if [ "$SERVICE_NAME" = "all" ]; then
    docker-compose up -d
else
    docker-compose up -d $SERVICE_NAME
fi

echo "✅ 服务更新完成: $SERVICE_NAME"
echo "📊 当前状态:"
docker-compose ps $SERVICE_NAME