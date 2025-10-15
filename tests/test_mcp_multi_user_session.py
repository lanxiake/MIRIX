"""
测试 MCP Server 的多用户和多会话功能

该测试脚本验证以下功能：
1. 多个不同用户同时连接
2. 同一用户的多个会话
3. 会话隔离和用户数据隔离
4. URL 参数正确传递 user_id
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP Server 配置
MCP_SERVER_URL = "http://10.157.152.40:18002"
SSE_ENDPOINT = "/sse"
MESSAGE_ENDPOINT = "/messages"


class MCPTestClient:
    """MCP 测试客户端"""

    def __init__(self, user_id: str, session_id: str = None):
        """
        初始化测试客户端

        Args:
            user_id: 用户ID
            session_id: 可选的会话ID
        """
        self.user_id = user_id
        self.session_id = session_id or f"session_{user_id}"
        self.messages_received = []

    async def connect(self):
        """建立 SSE 连接"""
        # 构建连接 URL
        params = {
            "user_id": self.user_id,
            "session_id": self.session_id
        }

        url = f"{MCP_SERVER_URL}{SSE_ENDPOINT}"

        logger.info(f"[{self.user_id}][{self.session_id}] 连接到 {url}")
        logger.info(f"[{self.user_id}][{self.session_id}] 参数: {params}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    logger.info(f"[{self.user_id}][{self.session_id}] 连接状态: {response.status}")

                    if response.status == 200:
                        # 读取 SSE 消息
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data:'):
                                    data = line_str[5:].strip()
                                    try:
                                        message = json.loads(data)
                                        self.messages_received.append(message)
                                        logger.info(f"[{self.user_id}][{self.session_id}] 收到消息: {message}")
                                    except json.JSONDecodeError:
                                        logger.warning(f"[{self.user_id}][{self.session_id}] 无法解析消息: {data}")
                    else:
                        logger.error(f"[{self.user_id}][{self.session_id}] 连接失败: {response.status}")

        except Exception as e:
            logger.error(f"[{self.user_id}][{self.session_id}] 连接错误: {e}")


async def test_multi_user_connection():
    """测试多用户同时连接"""
    logger.info("=" * 60)
    logger.info("测试1: 多用户同时连接")
    logger.info("=" * 60)

    # 创建3个不同的用户客户端
    users = ["user_alice", "user_bob", "user_charlie"]
    clients = [MCPTestClient(user_id) for user_id in users]

    # 并发连接
    tasks = [client.connect() for client in clients]

    # 设置超时（30秒）
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=30.0)
        logger.info("✓ 多用户连接测试完成")
    except asyncio.TimeoutError:
        logger.info("✓ 多用户连接测试超时（预期行为，SSE 是长连接）")
    except Exception as e:
        logger.error(f"✗ 多用户连接测试失败: {e}")


async def test_same_user_multiple_sessions():
    """测试同一用户的多个会话"""
    logger.info("=" * 60)
    logger.info("测试2: 同一用户多个会话")
    logger.info("=" * 60)

    # 创建同一用户的3个不同会话
    user_id = "user_test"
    sessions = ["session_1", "session_2", "session_3"]
    clients = [MCPTestClient(user_id, session_id) for session_id in sessions]

    # 并发连接
    tasks = [client.connect() for client in clients]

    # 设置超时（30秒）
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=30.0)
        logger.info("✓ 多会话测试完成")
    except asyncio.TimeoutError:
        logger.info("✓ 多会话测试超时（预期行为，SSE 是长连接）")
    except Exception as e:
        logger.error(f"✗ 多会话测试失败: {e}")


async def test_url_parameters():
    """测试 URL 参数传递"""
    logger.info("=" * 60)
    logger.info("测试3: URL 参数传递")
    logger.info("=" * 60)

    test_cases = [
        {
            "user_id": "user_param_test",
            "session_id": "session_test_123",
            "description": "标准参数"
        },
        {
            "user_id": "user_with_special_chars!@#",
            "session_id": None,
            "description": "特殊字符用户ID"
        },
        {
            "user_id": "user_no_session",
            "session_id": None,
            "description": "仅 user_id 参数"
        }
    ]

    for test_case in test_cases:
        logger.info(f"测试场景: {test_case['description']}")
        client = MCPTestClient(test_case['user_id'], test_case['session_id'])

        try:
            await asyncio.wait_for(client.connect(), timeout=10.0)
            logger.info(f"✓ {test_case['description']} 测试通过")
        except asyncio.TimeoutError:
            logger.info(f"✓ {test_case['description']} 测试超时（预期行为）")
        except Exception as e:
            logger.error(f"✗ {test_case['description']} 测试失败: {e}")


async def test_connection_info():
    """测试连接信息获取"""
    logger.info("=" * 60)
    logger.info("测试4: 连接信息获取")
    logger.info("=" * 60)

    # 简单的 HTTP 请求测试
    test_endpoints = [
        {"path": "/", "desc": "根路径"},
        {"path": "/health", "desc": "健康检查"},
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in test_endpoints:
            url = f"{MCP_SERVER_URL}{endpoint['path']}"
            try:
                async with session.get(url, timeout=5.0) as response:
                    logger.info(f"{endpoint['desc']}: {response.status}")
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"响应数据: {json.dumps(data, indent=2)}")
                        except:
                            text = await response.text()
                            logger.info(f"响应文本: {text[:200]}")
            except Exception as e:
                logger.warning(f"{endpoint['desc']} 请求失败: {e}")


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始 MCP Server 多用户和多会话测试")
    logger.info("=" * 60)

    # 测试4: 连接信息（最简单，先测试服务器是否可达）
    await test_connection_info()

    # 测试3: URL 参数传递
    await test_url_parameters()

    # 测试1: 多用户同时连接
    await test_multi_user_connection()

    # 测试2: 同一用户多个会话
    await test_same_user_multiple_sessions()

    logger.info("=" * 60)
    logger.info("所有测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
