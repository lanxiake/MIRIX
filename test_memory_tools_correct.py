#!/usr/bin/env python3
"""
测试 MIRIX 记忆管理工具的正确调用

使用正确的参数格式测试各个记忆管理工具。
"""

import asyncio
import json
from mcp.client.sse import sse_client
import mcp

async def test_memory_tools():
    """测试 MIRIX 记忆管理工具"""
    server_url = "http://localhost:8080"
    sse_endpoint = f"{server_url}/sse/sse"
    
    print(f"🔗 连接到 MIRIX MCP SSE 服务: {server_url}")
    
    try:
        async with sse_client(sse_endpoint, timeout=30.0) as streams:
            async with mcp.ClientSession(*streams) as session:
                print("✅ MCP 会话建立成功")
                
                # 初始化会话
                await session.initialize()
                print("🚀 会话初始化完成")
                
                # 测试 1: 添加记忆
                print("\n📝 测试 1: 添加记忆")
                try:
                    result = await session.call_tool("memory_add", {
                        "content": "用户正在测试 MIRIX MCP 记忆管理功能",
                        "memory_type": "episodic",  # 使用正确的记忆类型
                        "context": "MCP 工具测试"
                    })
                    print(f"✅ 添加记忆成功: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ 添加记忆失败: {e}")
                
                # 测试 2: 搜索记忆
                print("\n🔍 测试 2: 搜索记忆")
                try:
                    result = await session.call_tool("memory_search", {
                        "query": "MCP 测试",
                        "limit": 5
                    })
                    print(f"✅ 搜索记忆成功: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ 搜索记忆失败: {e}")
                
                # 测试 3: 获取用户档案
                print("\n👤 测试 3: 获取用户档案")
                try:
                    result = await session.call_tool("memory_get_profile", {})
                    print(f"✅ 获取用户档案成功: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ 获取用户档案失败: {e}")
                
                # 测试 4: 记忆对话
                print("\n💬 测试 4: 记忆对话")
                try:
                    result = await session.call_tool("memory_chat", {
                        "message": "你好，我正在测试 MIRIX 的 MCP 接口功能",
                        "memorizing": True
                    })
                    print(f"✅ 记忆对话成功: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ 记忆对话失败: {e}")
                
                # 测试 5: 添加不同类型的记忆
                print("\n📚 测试 5: 添加不同类型的记忆")
                memory_types = ["core", "semantic", "procedural", "resource", "knowledge_vault"]
                
                for memory_type in memory_types:
                    try:
                        result = await session.call_tool("memory_add", {
                            "content": f"这是一个 {memory_type} 类型的测试记忆",
                            "memory_type": memory_type,
                            "context": f"{memory_type} 记忆测试"
                        })
                        print(f"✅ 添加 {memory_type} 记忆成功")
                    except Exception as e:
                        print(f"❌ 添加 {memory_type} 记忆失败: {e}")
                
                # 测试 6: 按类型搜索记忆
                print("\n🎯 测试 6: 按类型搜索记忆")
                try:
                    result = await session.call_tool("memory_search", {
                        "query": "测试",
                        "memory_types": ["episodic", "semantic"],
                        "limit": 10
                    })
                    print(f"✅ 按类型搜索记忆成功: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ 按类型搜索记忆失败: {e}")
                
                print("\n🎉 所有记忆工具测试完成！")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_memory_tools())