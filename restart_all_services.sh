#!/bin/bash
"""
完整重启MIRIX服务的脚本

这个脚本会完全重启所有Docker服务，确保所有组件都使用最新代码
"""

echo "🔄 完整重启MIRIX服务"
echo "================================="

# 停止所有服务
echo "1. 停止所有Docker服务..."
sudo docker-compose down

# 等待完全停止
sleep 5

# 重新启动所有服务
echo "2. 启动所有Docker服务..."
sudo docker-compose up -d

# 等待服务启动
echo "3. 等待服务初始化..."
sleep 30

# 检查服务状态
echo "4. 检查服务状态..."
echo ""
echo "=== MIRIX 后端服务状态 ==="
sudo docker-compose logs mirix-backend --tail 10

echo ""
echo "=== MCP 服务状态 ==="  
sudo docker-compose logs mirix-mcp --tail 10

echo ""
echo "=== 服务健康检查 ==="
echo "MIRIX Backend:"
curl -s http://localhost:47283/health | head -1

echo "MCP Server:"
curl -s http://localhost:18002/sse -I | head -1

echo ""
echo "================================="
echo "✅ 服务重启完成"
echo ""
echo "现在可以重新测试MCP功能："
echo "1. memory_add - 添加记忆"
echo "2. memory_search - 搜索记忆"  
echo "3. memory_get_profile - 获取档案"
echo "4. memory_chat - 对话功能（如果仍超时，属于已知问题）"
