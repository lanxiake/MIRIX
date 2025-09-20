#!/usr/bin/env python3
"""
简单验证修复是否有效
"""

import asyncio
import json
import httpx
from typing import Dict, Any

async def verify_fix():
    """验证工具列表响应格式修复"""

    async with httpx.AsyncClient() as client:
        # 模拟MCP客户端的listTools请求
        print("Testing MCP tools list...")

        # 1. 连接到MCP服务器
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-mcp-client",
                    "version": "0.1.0"
                }
            }
        }

        response = await client.post("http://localhost:8080/mcp/connect", json=init_request)
        if response.status_code != 200:
            print(f"Connection failed: {response.text}")
            return False

        conn_result = response.json()
        session_id = conn_result["result"]["session_id"]
        print(f"Connected with session: {session_id}")

        # 2. 发送tools/list请求
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        tools_response = await client.post(
            f"http://localhost:8080/mcp/message/{session_id}",
            json=tools_request
        )

        print(f"Tools request status: {tools_response.status_code}")

        if tools_response.status_code == 200:
            result = tools_response.json()
            print(f"Tools request accepted: {result}")

            # 3. 直接测试tools端点（用于验证响应格式）
            tools_endpoint_response = await client.get("http://localhost:8080/mcp/tools")
            print(f"Direct tools endpoint status: {tools_endpoint_response.status_code}")

            if tools_endpoint_response.status_code == 200:
                tools_data = tools_endpoint_response.json()
                print(f"Tools endpoint response: {json.dumps(tools_data, indent=2)}")

                # 验证是否包含tools字段
                if "tools" in tools_data:
                    print("SUCCESS: 'tools' field is present in response")
                    print(f"Tools count: {len(tools_data['tools'])}")

                    # 这应该解决原始错误：
                    # "code": "invalid_type", "expected": "array", "received": "undefined", "path": ["tools"]
                    return True
                else:
                    print("ERROR: 'tools' field is missing from response")
                    return False
            else:
                print(f"ERROR: Tools endpoint failed with status {tools_endpoint_response.status_code}")
                return False
        else:
            print(f"ERROR: Tools request failed with status {tools_response.status_code}")
            return False

if __name__ == "__main__":
    result = asyncio.run(verify_fix())
    if result:
        print("\n=== VERIFICATION SUCCESS ===")
        print("The MCP tools response now includes the required 'tools' field")
        print("This should resolve the client error: 'tools' field 'undefined'")
    else:
        print("\n=== VERIFICATION FAILED ===")
        print("The fix did not work as expected")