#!/bin/bash
"""
强制重建MCP服务脚本

这个脚本将彻底重建MCP Docker容器以确保使用最新的代码修复
"""

echo "=== 强制重建MCP服务 ==="
echo "注意：这将彻底重建容器，确保使用最新代码"

# 完全停止并移除容器
echo "1. 停止并移除MCP容器..."
sudo docker-compose stop mirix-mcp
sudo docker-compose rm -f mirix-mcp

# 移除镜像（可选，确保完全重建）
echo "2. 移除旧镜像..."
sudo docker rmi mirix-mirix-mcp 2>/dev/null || echo "镜像不存在或已移除"

# 重新构建容器
echo "3. 重新构建MCP容器..."
sudo docker-compose build --no-cache mirix-mcp

# 启动容器
echo "4. 启动MCP容器..."
sudo docker-compose up -d mirix-mcp

# 等待服务启动
echo "5. 等待服务启动..."
sleep 10

# 检查服务状态
echo "6. 检查服务状态..."
sudo docker-compose logs mirix-mcp --tail 10

echo ""
echo "=== 重建完成 ==="
echo "请等待几秒钟让服务完全启动，然后可以测试修复效果"
echo ""
echo "测试命令："
echo "python3 tests/test_mcp_client.py"
