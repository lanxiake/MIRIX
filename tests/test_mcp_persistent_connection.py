#!/usr/bin/env python3
"""
MCP SSE 持久连接测试脚本

这个脚本创建一个持久的SSE连接来正确测试MCP协议，
确保SSE连接在整个会话期间保持开放，以便接收工具执行结果。
"""

import asyncio
import json
import time
import aiohttp
import re
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPPersistentTestClient:
    """MCP 持久连接测试客户端"""

    def __init__(self, base_url: str = "http://localhost:18005"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.sse_task: Optional[asyncio.Task] = None
        self.message_queue = asyncio.Queue()
        self.connected = False

    async def start_persistent_sse_connection(self) -> Optional[str]:
        """建立持久的SSE连接"""
        logger.info("🔍 建立持久SSE连接...")

        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)  # 5分钟超时
            )

            # 创建SSE连接
            response = await self.session.get(f"{self.base_url}/sse")

            if response.status == 200:
                logger.info("✅ SSE连接建立成功")

                # 启动后台任务处理SSE数据
                self.sse_task = asyncio.create_task(self._handle_sse_stream(response))

                # 等待获取session_id
                for _ in range(10):  # 等待最多10秒
                    if self.session_id:
                        break
                    await asyncio.sleep(1)

                if self.session_id:
                    self.connected = True
                    logger.info(f"✅ 获取session_id成功: {self.session_id}")
                    return self.session_id
                else:
                    logger.error("❌ 未能获取session_id")
                    return None
            else:
                logger.error(f"❌ SSE连接失败: HTTP {response.status}")
                return None

        except Exception as e:
            logger.error(f"❌ SSE连接异常: {e}")
            return None

    async def _handle_sse_stream(self, response):
        """处理SSE数据流"""
        try:
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str:
                    logger.debug(f"📥 SSE: {line_str}")

                    # 解析session_id
                    if 'session_id=' in line_str and not self.session_id:
                        match = re.search(r'session_id=([a-f0-9]+)', line_str)
                        if match:
                            self.session_id = match.group(1)

                    # 解析MCP消息
                    if line_str.startswith('data: {'):
                        try:
                            json_data = line_str[6:]  # 移除 'data: ' 前缀
                            message = json.loads(json_data)
                            await self.message_queue.put(message)
                            logger.info(f"📨 收到MCP响应: {message.get('id', 'N/A')}")
                        except json.JSONDecodeError:
                            pass

        except Exception as e:
            logger.error(f"❌ SSE流处理异常: {e}")
            self.connected = False

    async def send_mcp_message(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送MCP消息并等待响应"""
        if not self.connected or not self.session_id:
            logger.error("❌ 连接未建立或无效")
            return None

        # 构造MCP消息
        message_id = int(time.time() * 1000)
        mcp_message = {
            "jsonrpc": "2.0",
            "id": message_id,
            "method": method,
            "params": params
        }

        logger.info(f"📤 发送MCP消息: {method} (ID: {message_id})")

        try:
            # 使用独立的session发送POST请求
            async with aiohttp.ClientSession() as post_session:
                async with post_session.post(
                    f"{self.base_url}/messages",
                    params={"session_id": self.session_id},
                    json=mcp_message,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status in [200, 202]:
                        logger.info(f"✅ 消息发送成功: HTTP {response.status}")

                        # 等待响应
                        try:
                            response_message = await asyncio.wait_for(
                                self.message_queue.get(),
                                timeout=10.0
                            )

                            if response_message.get('id') == message_id:
                                logger.info(f"✅ 收到匹配响应: {message_id}")
                                return response_message
                            else:
                                # 消息ID不匹配，放回队列
                                await self.message_queue.put(response_message)
                                logger.warning(f"⚠️ 响应ID不匹配: 期望{message_id}, 收到{response_message.get('id')}")
                                return None

                        except asyncio.TimeoutError:
                            logger.warning(f"⚠️ 等待响应超时: {message_id}")
                            return {"timeout": True}
                    else:
                        logger.error(f"❌ 消息发送失败: HTTP {response.status}")
                        return None

        except Exception as e:
            logger.error(f"❌ 发送消息异常: {e}")
            return None

    async def test_memory_add(self, content: str, memory_type: str, context: str, user_id: str) -> bool:
        """测试记忆添加功能"""
        params = {
            "content": content,
            "memory_type": memory_type,
            "context": context,
            "user_id": user_id
        }

        response = await self.send_mcp_message("tools/call", {
            "name": "memory_add",
            "arguments": params
        })

        if response and "result" in response:
            logger.info(f"✅ 记忆添加成功: {memory_type}")
            return True
        else:
            if response:
                logger.error(f"❌ 记忆添加失败: {memory_type}, 响应: {response}")
            else:
                logger.error(f"❌ 记忆添加失败: {memory_type}, 无响应")
            return False

    async def test_memory_search(self, query: str, memory_types: list, user_id: str) -> bool:
        """测试记忆搜索功能"""
        params = {
            "query": query,
            "memory_types": memory_types,
            "limit": 5,
            "user_id": user_id
        }

        response = await self.send_mcp_message("tools/call", {
            "name": "memory_search",
            "arguments": params
        })

        if response and "result" in response:
            logger.info(f"✅ 记忆搜索成功: {query}")
            return True
        else:
            if response:
                logger.error(f"❌ 记忆搜索失败: {query}, 响应: {response}")
            else:
                logger.error(f"❌ 记忆搜索失败: {query}, 无响应")
            return False

    async def close(self):
        """关闭连接"""
        self.connected = False

        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info("🔌 连接已关闭")

async def run_persistent_test():
    """运行持久连接测试"""
    logger.info("🚀 开始MCP持久连接测试...")
    logger.info("=" * 60)

    client = MCPPersistentTestClient()

    try:
        # 建立持久连接
        session_id = await client.start_persistent_sse_connection()
        if not session_id:
            logger.error("❌ 无法建立SSE连接，测试终止")
            return False

        # 等待连接稳定
        await asyncio.sleep(2)

        # 测试工具列表
        logger.info("\n📋 测试工具列表...")
        response = await client.send_mcp_message("tools/list", {})
        if response:
            tools = response.get("result", {}).get("tools", [])
            logger.info(f"✅ 获取到 {len(tools)} 个工具")
            for tool in tools:
                logger.info(f"  - {tool.get('name')}: {tool.get('description')}")

        # 测试记忆添加
        logger.info("\n📋 测试记忆添加...")
        test_user = f"persistent_test_user_{int(time.time())}"

        success_count = 0
        test_memories = [
            ("我是持久连接测试用户，正在测试MCP协议", "core", "用户身份信息"),
            ("今天进行了持久连接的MCP测试", "episodic", "测试活动记录"),
            ("MCP协议需要保持持久的SSE连接才能正常工作", "semantic", "技术知识"),
        ]

        for content, mem_type, context in test_memories:
            if await client.test_memory_add(content, mem_type, context, test_user):
                success_count += 1

        logger.info(f"📊 记忆添加结果: {success_count}/{len(test_memories)} 成功")

        # 等待数据处理
        await asyncio.sleep(3)

        # 测试记忆搜索
        logger.info("\n📋 测试记忆搜索...")
        search_queries = [
            ("持久连接", ["core", "episodic"]),
            ("MCP协议", ["semantic"]),
            ("测试用户", ["core"])
        ]

        search_success = 0
        for query, mem_types in search_queries:
            if await client.test_memory_search(query, mem_types, test_user):
                search_success += 1

        logger.info(f"📊 记忆搜索结果: {search_success}/{len(search_queries)} 成功")

        # 总结结果
        overall_success = (success_count >= 2 and search_success >= 1)

        logger.info("\n" + "=" * 60)
        if overall_success:
            logger.info("🎉 持久连接测试通过！MCP协议工作正常")
        else:
            logger.info("⚠️ 持久连接测试部分失败，需要进一步调试")

        return overall_success

    except Exception as e:
        logger.error(f"❌ 测试执行异常: {e}")
        return False
    finally:
        await client.close()

def main():
    """主函数"""
    print("MIRIX MCP 持久连接测试工具")
    print("=" * 60)

    try:
        result = asyncio.run(run_persistent_test())
        exit_code = 0 if result else 1
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"❌ 测试执行异常: {e}")
        exit(1)

if __name__ == "__main__":
    main()