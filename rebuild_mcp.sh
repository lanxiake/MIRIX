#!/bin/bash
"""
MCP服务重建脚本

这个脚本用于重新构建和重启MCP Docker容器以应用代码修复
需要sudo权限执行Docker命令
"""

echo "=== MCP服务重建脚本 ==="
echo "正在重新构建MCP服务容器..."

# 停止现有容器
echo "1. 停止现有MCP容器..."
sudo docker-compose down mirix-mcp

# 重新构建容器
echo "2. 重新构建MCP容器..."
sudo docker-compose build mirix-mcp

# 启动容器
echo "3. 启动MCP容器..."
sudo docker-compose up -d mirix-mcp

# 等待服务启动
echo "4. 等待服务启动..."
sleep 5

# 检查服务状态
echo "5. 检查服务状态..."
sudo docker-compose logs mirix-mcp --tail 20

echo "=== MCP服务重建完成 ==="
echo "可以使用以下命令查看日志："
echo "sudo docker-compose logs -f mirix-mcp"
