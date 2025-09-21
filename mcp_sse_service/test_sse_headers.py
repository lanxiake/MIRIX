#!/usr/bin/env python3
"""
测试 SSE Content-Type 的脚本
"""

import httpx
import asyncio


async def test_sse_headers():
    """测试 SSE 端点的响应头"""
    print("🧪 测试 SSE Content-Type...")

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", "http://localhost:8082/mcp/sse") as response:
                print(f"状态码: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
                print(f"Cache-Control: {response.headers.get('cache-control', 'N/A')}")
                print(f"Connection: {response.headers.get('connection', 'N/A')}")

                if response.headers.get('content-type') == 'text/event-stream; charset=utf-8':
                    print("✅ SSE Content-Type 正确")
                else:
                    print("❌ SSE Content-Type 不正确")

                # 读取第一个事件
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        print(f"收到事件: {line}")
                        break

    except Exception as e:
        print(f"❌ 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_sse_headers())