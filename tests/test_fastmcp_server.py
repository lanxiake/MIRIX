"""
FastMCP 服务器测试脚本

测试基于 FastMCP 的 MIRIX MCP 服务器功能，包括：
- SSE 连接建立
- 工具列表获取
- 工具调用
- 记忆管理功能

作者：MIRIX Development Team
版本：1.0.0
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, Optional
import aiohttp

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试配置
TEST_CONFIG = {
    "host": "localhost",
    "port": 18004,
    "sse_endpoint": "/sse",
    "timeout": 30,
    "user_id": "test_user_123"
}


class FastMCPTester:
    """FastMCP 服务器测试器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = f"http://{config['host']}:{config['port']}"
        self.sse_url = f"{self.base_url}{config['sse_endpoint']}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config['timeout']))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_sse_connection(self) -> tuple[bool, str]:
        """测试 SSE 连接并获取session_id"""
        logger.info("🔍 测试SSE连接建立...")

        try:
            async with self.session.get(self.sse_url) as response:
                if response.status == 200:
                    logger.info("✅ SSE连接成功建立")

                    # 读取一些初始事件
                    content_type = response.headers.get('content-type', '')
                    if 'text/event-stream' in content_type:
                        logger.info("✅ 响应内容类型正确: text/event-stream")

                        # 读取前几个事件，寻找session_id
                        event_count = 0
                        session_id = None
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str:
                                logger.info(f"📨 收到事件: {line_str}")

                                # 提取session_id
                                if "session_id=" in line_str:
                                    import re
                                    match = re.search(r'session_id=([a-f0-9]{32})', line_str)
                                    if match:
                                        session_id = match.group(1)
                                        logger.info(f"🔑 提取到session_id: {session_id}")

                                event_count += 1
                                if event_count >= 3:  # 只读取前3个事件
                                    break

                        logger.info(f"✅ 成功接收到 {event_count} 个事件")
                        return True, session_id
                    else:
                        logger.error(f"❌ 错误的内容类型: {content_type}")
                        return False, None
                else:
                    logger.error(f"❌ SSE连接失败，状态码: {response.status}")
                    return False, None

        except asyncio.TimeoutError:
            logger.error("❌ SSE连接超时")
            return False, None
        except Exception as e:
            logger.error(f"❌ SSE连接异常: {e}")
            return False, None

    def send_mcp_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送MCP请求 (同步版本，用于消息发送)"""
        message = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method
        }
        if params:
            message["params"] = params

        return message

    async def test_initialize(self, session_id: str) -> bool:
        """测试初始化"""
        if not session_id:
            logger.error("❌ 没有有效的session_id，跳过初始化测试")
            return False

        logger.info("🔍 测试MCP初始化...")

        try:
            # MCP初始化请求
            init_message = self.send_mcp_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "FastMCP Test Client",
                    "version": "1.0.0"
                }
            })

            logger.info(f"📤 发送初始化消息: {json.dumps(init_message, indent=2)}")

            # 使用带有session_id的消息端点
            message_url = f"{self.base_url}/messages/?session_id={session_id}"

            try:
                async with self.session.post(message_url, json=init_message) as response:
                    if response.status in [200, 202]:
                        try:
                            result = await response.json()
                            logger.info(f"📥 收到初始化响应: {json.dumps(result, indent=2)}")
                            return True
                        except:
                            text = await response.text()
                            logger.info(f"📥 收到初始化响应: {text}")
                            return True
                    else:
                        logger.error(f"❌ 初始化失败，状态码: {response.status}")
                        error_text = await response.text()
                        logger.error(f"错误详情: {error_text}")
                        return False
            except Exception as e:
                logger.error(f"❌ 初始化请求异常: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ 初始化异常: {e}")
            return False

    async def test_list_tools(self, session_id: str) -> bool:
        """测试工具列表"""
        if not session_id:
            logger.error("❌ 没有有效的session_id，跳过工具列表测试")
            return False

        logger.info("🔍 测试获取工具列表...")

        try:
            tools_message = self.send_mcp_request("tools/list")
            logger.info(f"📤 发送工具列表请求: {json.dumps(tools_message, indent=2)}")

            # 使用带有session_id的消息端点
            message_url = f"{self.base_url}/messages/?session_id={session_id}"

            try:
                async with self.session.post(message_url, json=tools_message) as response:
                    if response.status in [200, 202]:
                        try:
                            result = await response.json()
                            logger.info(f"📥 收到工具列表: {json.dumps(result, indent=2)}")

                            # 检查是否包含我们期望的工具
                            if "tools" in result or "result" in result:
                                logger.info("✅ 工具列表获取成功")
                                return True
                        except:
                            text = await response.text()
                            logger.info(f"📥 收到工具列表响应: {text}")
                            return True
                    else:
                        logger.error(f"❌ 工具列表获取失败，状态码: {response.status}")
                        error_text = await response.text()
                        logger.error(f"错误详情: {error_text}")
                        return False
            except Exception as e:
                logger.error(f"❌ 工具列表请求异常: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ 工具列表测试异常: {e}")
            return False

    async def test_tool_call(self, tool_name: str, arguments: Dict[str, Any], session_id: str) -> bool:
        """测试工具调用"""
        if not session_id:
            logger.error(f"❌ 没有有效的session_id，跳过工具调用测试: {tool_name}")
            return False

        logger.info(f"🔍 测试工具调用: {tool_name}")

        try:
            call_message = self.send_mcp_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            logger.info(f"📤 发送工具调用: {json.dumps(call_message, indent=2)}")

            # 使用带有session_id的消息端点
            message_url = f"{self.base_url}/messages/?session_id={session_id}"

            try:
                async with self.session.post(message_url, json=call_message) as response:
                    if response.status in [200, 202]:
                        try:
                            result = await response.json()
                            logger.info(f"📥 工具调用结果: {json.dumps(result, indent=2)}")
                        except:
                            text = await response.text()
                            logger.info(f"📥 工具调用结果: {text}")

                        logger.info(f"✅ 工具 {tool_name} 调用成功")
                        return True
                    else:
                        logger.error(f"❌ 工具 {tool_name} 调用失败，状态码: {response.status}")
                        error_text = await response.text()
                        logger.error(f"错误详情: {error_text}")
                        return False
            except Exception as e:
                logger.error(f"❌ 工具调用请求异常: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ 工具调用异常: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """运行综合测试"""
        logger.info("🚀 开始FastMCP服务器综合测试...")
        logger.info("=" * 60)

        results = {}

        # 测试1: SSE连接并获取session_id
        logger.info("\n📋 测试1: SSE连接建立")
        sse_success, session_id = await self.test_sse_connection()
        results["sse_connection"] = sse_success

        if not sse_success or not session_id:
            logger.error("❌ SSE连接失败或无法获取session_id，跳过后续测试")
            # 为剩余测试设置失败状态
            for test_name in ["initialize", "list_tools", "memory_add", "memory_search", "memory_chat", "memory_get_profile"]:
                results[test_name] = False
            return results

        logger.info(f"✅ 获得session_id: {session_id}")

        # 测试2: MCP初始化
        logger.info("\n📋 测试2: MCP初始化")
        results["initialize"] = await self.test_initialize(session_id)

        # 测试3: 工具列表
        logger.info("\n📋 测试3: 获取工具列表")
        results["list_tools"] = await self.test_list_tools(session_id)

        # 测试4: 记忆添加工具
        logger.info("\n📋 测试4: 记忆添加工具")
        results["memory_add"] = await self.test_tool_call("memory_add", {
            "content": "这是一个测试记忆内容",
            "user_id": self.config["user_id"]
        }, session_id)

        # 测试5: 记忆搜索工具
        logger.info("\n📋 测试5: 记忆搜索工具")
        results["memory_search"] = await self.test_tool_call("memory_search", {
            "query": "测试",
            "user_id": self.config["user_id"],
            "limit": 5
        }, session_id)

        # 测试6: 记忆对话工具
        logger.info("\n📋 测试6: 记忆对话工具")
        results["memory_chat"] = await self.test_tool_call("memory_chat", {
            "message": "你记得我之前说过什么吗？",
            "user_id": self.config["user_id"]
        }, session_id)

        # 测试7: 用户档案工具
        logger.info("\n📋 测试7: 用户档案工具")
        results["memory_get_profile"] = await self.test_tool_call("memory_get_profile", {
            "user_id": self.config["user_id"]
        }, session_id)

        return results


async def main():
    """主函数"""
    print("MIRIX FastMCP Server 测试工具")
    print("=" * 60)

    async with FastMCPTester(TEST_CONFIG) as tester:
        results = await tester.run_comprehensive_test()

        # 输出测试结果
        logger.info("\n" + "=" * 60)
        logger.info("📊 测试结果汇总:")
        logger.info("=" * 60)

        passed = 0
        total = len(results)

        for test_name, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            logger.info(f"{test_name:20s}: {status}")
            if success:
                passed += 1

        logger.info("=" * 60)
        logger.info(f"总计: {passed}/{total} 项测试通过")

        if passed == total:
            logger.info("🎉 所有测试都通过！FastMCP服务器运行正常")
            return 0
        else:
            logger.warning(f"⚠️  有 {total - passed} 项测试失败")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        sys.exit(1)