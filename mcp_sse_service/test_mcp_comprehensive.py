#!/usr/bin/env python3
"""
MIRIX MCP 服务器测试脚本

完整测试 MCP SSE 服务的各项功能。
"""

import asyncio
import json
import sys
import time
import httpx
import argparse


class MCPTestClient:
    """MCP 测试客户端"""

    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self.client.aclose()

    async def test_basic_connection(self):
        """测试基本连接"""
        print("🔗 测试基本连接...")
        try:
            response = await self.client.get(f"{self.base_url}/")
            data = response.json()
            print(f"✅ 服务器信息: {data['name']} v{data['version']}")
            print(f"   后端URL: {data['backend_url']}")
            print(f"   用户ID: {data['default_user_id']}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def test_health_check(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            data = response.json()
            print(f"✅ 健康状态: {data['status']}")
            return True
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False

    async def test_mcp_initialize(self):
        """测试 MCP 初始化"""
        print("\n🚀 测试 MCP 初始化...")
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                }
            }
            response = await self.client.post(
                f"{self.base_url}/mcp/request",
                json=request_data
            )
            data = response.json()
            if data.get("result"):
                print(f"✅ MCP 初始化成功")
                print(f"   协议版本: {data['result']['protocolVersion']}")
                print(f"   服务器名称: {data['result']['serverInfo']['name']}")
                return True
            else:
                print(f"❌ MCP 初始化失败: {data}")
                return False
        except Exception as e:
            print(f"❌ MCP 初始化异常: {e}")
            return False

    async def test_tools_list(self):
        """测试工具列表"""
        print("\n🛠️ 测试工具列表...")
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            response = await self.client.post(
                f"{self.base_url}/mcp/request",
                json=request_data
            )
            data = response.json()
            if data.get("result") and data["result"].get("tools"):
                tools = data["result"]["tools"]
                print(f"✅ 可用工具 ({len(tools)} 个):")
                for tool in tools:
                    print(f"   - {tool['name']}: {tool['description']}")
                return tools
            else:
                print(f"❌ 获取工具列表失败: {data}")
                return []
        except Exception as e:
            print(f"❌ 获取工具列表异常: {e}")
            return []

    async def test_memory_add(self):
        """测试记忆添加"""
        print("\n💾 测试记忆添加...")
        try:
            # 测试直接 HTTP API
            response = await self.client.post(
                f"{self.base_url}/tools/memory_add",
                json={
                    "content": "我是一个AI测试工程师，专注于MCP协议开发",
                    "memory_type": "core",
                    "context": "职业信息"
                }
            )
            data = response.json()
            if data.get("success"):
                print(f"✅ HTTP API 记忆添加成功: {data['memory_id']}")
            else:
                print(f"❌ HTTP API 记忆添加失败: {data}")

            # 测试 MCP 协议
            request_data = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "memory_add",
                    "arguments": {
                        "content": "我喜欢使用Python进行自动化测试",
                        "memory_type": "semantic",
                        "context": "技能偏好"
                    }
                }
            }
            response = await self.client.post(
                f"{self.base_url}/mcp/request",
                json=request_data
            )
            data = response.json()
            if not data.get("result", {}).get("isError", True):
                content = json.loads(data["result"]["content"][0]["text"])
                if content.get("success"):
                    print(f"✅ MCP 协议记忆添加成功: {content['memory_id']}")
                    return True
                else:
                    print(f"❌ MCP 协议记忆添加失败: {content}")
            else:
                print(f"❌ MCP 协议记忆添加失败: {data}")
            return False
        except Exception as e:
            print(f"❌ 记忆添加异常: {e}")
            return False

    async def test_memory_search(self):
        """测试记忆搜索"""
        print("\n🔍 测试记忆搜索...")
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/memory_search",
                json={
                    "query": "测试",
                    "limit": 5
                }
            )
            data = response.json()
            if data.get("success"):
                print(f"✅ 记忆搜索成功，找到 {data['total_count']} 条记录")
                for memory in data.get("memories", []):
                    print(f"   - {memory.get('type', 'unknown')}: {memory.get('content', '')[:50]}...")
                return True
            else:
                print(f"❌ 记忆搜索失败: {data}")
                return False
        except Exception as e:
            print(f"❌ 记忆搜索异常: {e}")
            return False

    async def test_memory_chat(self):
        """测试记忆聊天"""
        print("\n💬 测试记忆聊天...")
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/memory_chat",
                json={
                    "message": "请介绍一下我的技能和兴趣爱好",
                    "memorizing": True
                }
            )
            data = response.json()
            if data.get("success"):
                print(f"✅ 记忆聊天成功")
                if data.get("response"):
                    print(f"   响应: {data['response'][:100]}...")
                print(f"   已记忆: {data.get('memorized', False)}")
                return True
            else:
                print(f"❌ 记忆聊天失败: {data}")
                return False
        except Exception as e:
            print(f"❌ 记忆聊天异常: {e}")
            return False

    async def test_memory_profile(self):
        """测试用户档案"""
        print("\n👤 测试用户档案...")
        try:
            response = await self.client.get(f"{self.base_url}/tools/memory_get_profile")
            data = response.json()
            if data.get("success"):
                print(f"✅ 用户档案获取成功")
                print(f"   用户ID: {data['user_id']}")
                print(f"   总记忆数: {data['total_memories']}")
                memory_summary = data.get("memory_summary", {})
                for mem_type, count in memory_summary.items():
                    print(f"   {mem_type}: {count} 条")
                return True
            else:
                print(f"❌ 用户档案获取失败: {data}")
                return False
        except Exception as e:
            print(f"❌ 用户档案获取异常: {e}")
            return False

    async def test_resources(self):
        """测试资源"""
        print("\n📄 测试资源...")
        try:
            # 测试状态资源
            response = await self.client.get(f"{self.base_url}/resources/status")
            data = response.json()
            print(f"✅ 状态资源: {data.get('status', 'unknown')}")

            # 测试记忆统计资源
            response = await self.client.get(f"{self.base_url}/resources/memory_stats")
            data = response.json()
            print(f"✅ 记忆统计: {data.get('total_count', 0)} 条记录")
            return True
        except Exception as e:
            print(f"❌ 资源测试异常: {e}")
            return False

    async def test_sse_connection(self):
        """测试 SSE 连接"""
        print("\n📡 测试 SSE 连接...")
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", f"{self.base_url}/mcp/sse") as response:
                    if response.status_code == 200:
                        print("✅ SSE 连接建立成功")
                        # 读取前几个事件
                        count = 0
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = json.loads(line[6:])  # 去掉 "data: " 前缀
                                print(f"   收到事件: {data.get('type', 'unknown')}")
                                count += 1
                                if count >= 2:  # 只读取前两个事件
                                    break
                        return True
                    else:
                        print(f"❌ SSE 连接失败: {response.status_code}")
                        return False
        except Exception as e:
            print(f"❌ SSE 连接异常: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始 MIRIX MCP SSE 服务器完整测试")
        print("=" * 50)

        tests = [
            self.test_basic_connection,
            self.test_health_check,
            self.test_mcp_initialize,
            self.test_tools_list,
            self.test_memory_add,
            self.test_memory_search,
            self.test_memory_chat,
            self.test_memory_profile,
            self.test_resources,
            self.test_sse_connection,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                time.sleep(0.5)  # 短暂延迟
            except Exception as e:
                print(f"❌ 测试异常: {e}")

        print("\n" + "=" * 50)
        print(f"🏁 测试完成: {passed}/{total} 通过")
        if passed == total:
            print("🎉 所有测试通过！MCP SSE 服务器运行正常。")
        else:
            print("⚠️ 部分测试失败，请检查服务器配置。")

        return passed == total


async def main():
    parser = argparse.ArgumentParser(description="MIRIX MCP 服务器测试")
    parser.add_argument("--url", default="http://localhost:8081", help="MCP 服务器 URL")
    args = parser.parse_args()

    client = MCPTestClient(args.url)
    try:
        success = await client.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())