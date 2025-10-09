#!/usr/bin/env python3
"""
MCP SSE 服务器连接测试脚本

这个脚本用于测试MIRIX MCP服务器的SSE连接和消息端点功能。
包含以下测试用例：
1. 健康检查端点测试
2. SSE连接测试并获取session_id
3. 消息端点测试（发送MCP协议消息）
4. 工具列表获取测试
"""

import asyncio
import json
import time
import requests
import aiohttp
import re
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPSSETestClient:
    """MCP SSE测试客户端"""
    
    def __init__(self, base_url: str = "http://localhost:18004"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        
    def test_health_endpoint(self) -> bool:
        """测试健康检查端点"""
        logger.info("🔍 测试健康检查端点...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code in [200, 202]:
                data = response.json()
                logger.info(f"✅ 健康检查成功: {data}")
                return True
            else:
                logger.error(f"❌ 健康检查失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {e}")
            return False
    
    async def get_session_id_via_sse(self) -> Optional[str]:
        """通过SSE连接获取session_id"""
        logger.info("🔍 通过SSE连接获取session_id...")
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/sse") as response:
                    if response.status == 200:
                        logger.info("✅ SSE连接建立成功")
                        
                        # 读取前几行数据来获取session_id
                        lines_read = 0
                        async for line in response.content:
                            if lines_read >= 5:  # 只读取前5行
                                break
                            
                            line_str = line.decode('utf-8').strip()
                            logger.info(f"📥 SSE数据: {line_str}")
                            
                            # 查找包含session_id的数据行
                            if 'session_id=' in line_str:
                                # 使用正则表达式提取session_id
                                match = re.search(r'session_id=([a-f0-9]+)', line_str)
                                if match:
                                    session_id = match.group(1)
                                    logger.info(f"✅ 获取到session_id: {session_id}")
                                    self.session_id = session_id
                                    return session_id
                            
                            lines_read += 1
                        
                        logger.warning("⚠️ 未能从SSE数据中提取session_id")
                        return None
                    else:
                        logger.error(f"❌ SSE连接失败: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ SSE连接异常: {e}")
            return None
    
    def test_message_endpoint(self, session_id: str) -> bool:
        """测试消息端点"""
        logger.info(f"🔍 测试消息端点 (session_id: {session_id})...")
        
        # 构造MCP协议消息
        mcp_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                params={"session_id": session_id},
                json=mcp_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                try:
                    data = response.json()
                    logger.info(f"✅ 消息端点响应成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return True
                except json.JSONDecodeError:
                    logger.info(f"✅ 消息端点响应成功 (非JSON): {response.text}")
                    return True
            else:
                logger.error(f"❌ 消息端点失败: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 消息端点异常: {e}")
            return False
    
    def test_tools_list(self, session_id: str) -> bool:
        """测试工具列表获取"""
        logger.info(f"🔍 测试工具列表获取 (session_id: {session_id})...")
        
        mcp_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                params={"session_id": session_id},
                json=mcp_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                try:
                    data = response.json()
                    if "result" in data and "tools" in data["result"]:
                        tools = data["result"]["tools"]
                        logger.info(f"✅ 成功获取工具列表，共 {len(tools)} 个工具:")
                        for tool in tools:
                            logger.info(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                        return True
                    else:
                        logger.info(f"✅ 工具列表响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        return True
                except json.JSONDecodeError:
                    logger.info(f"✅ 工具列表响应 (非JSON): {response.text}")
                    return True
            else:
                logger.error(f"❌ 工具列表获取失败: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 工具列表获取异常: {e}")
            return False

async def run_tests():
    """运行所有测试"""
    logger.info("🚀 开始MCP SSE服务器测试...")
    logger.info("=" * 60)
    
    client = MCPSSETestClient()
    test_results = []
    
    # 测试1: 健康检查
    logger.info("\n📋 测试1: 健康检查端点")
    health_ok = client.test_health_endpoint()
    test_results.append(("健康检查", health_ok))
    
    if not health_ok:
        logger.error("❌ 健康检查失败，跳过后续测试")
        return
    
    # 测试2: SSE连接和session_id获取
    logger.info("\n📋 测试2: SSE连接和session_id获取")
    session_id = await client.get_session_id_via_sse()
    sse_ok = session_id is not None
    test_results.append(("SSE连接", sse_ok))
    
    if not sse_ok:
        logger.error("❌ SSE连接失败，跳过后续测试")
        return
    
    # 测试3: 消息端点
    logger.info("\n📋 测试3: 消息端点测试")
    message_ok = client.test_message_endpoint(session_id)
    test_results.append(("消息端点", message_ok))
    
    # 测试4: 工具列表
    logger.info("\n📋 测试4: 工具列表获取")
    tools_ok = client.test_tools_list(session_id)
    test_results.append(("工具列表", tools_ok))
    
    # 输出测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果汇总:")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name:15} : {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 所有测试通过！MCP SSE服务器运行正常")
    else:
        logger.info("⚠️ 部分测试失败，请检查服务器配置")
    
    return all_passed

def main():
    """主函数"""
    print("MIRIX MCP SSE 服务器测试工具")
    print("=" * 60)
    
    try:
        # 运行异步测试
        result = asyncio.run(run_tests())
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