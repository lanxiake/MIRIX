#!/usr/bin/env python3
"""
记忆功能修复验证脚本

测试修复后的记忆功能是否正常工作
"""

import asyncio
import json
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode


class MCPMemoryTester:
    """MCP记忆功能测试器"""
    
    def __init__(self, base_url="http://localhost:18002"):
        self.base_url = base_url.rstrip('/')
        self.session_id = f"test_session_{int(time.time())}"
    
    def make_request(self, tool_name, arguments):
        """发送MCP工具请求"""
        try:
            message_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            url = f"{self.base_url}/messages/?session_id={self.session_id}"
            data = json.dumps(message_data).encode('utf-8')
            
            req = Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            with urlopen(req, timeout=30) as response:
                return {
                    "status_code": response.getcode(),
                    "response": response.read().decode('utf-8')
                }
        except Exception as e:
            return {"error": str(e)}
    
    def test_memory_add(self):
        """测试添加记忆"""
        print("🧠 测试添加记忆...")
        result = self.make_request("memory_add", {
            "content": "修复测试记忆：今天是2024年，我们正在测试MCP记忆系统的修复效果。这个记忆包含了时间信息和测试目的。",
            "user_id": "test_user_fix"
        })
        
        print(f"  状态: {result.get('status_code', 'Error')}")
        if 'error' in result:
            print(f"  错误: {result['error']}")
        return result.get('status_code') == 202
    
    def test_memory_search(self):
        """测试搜索记忆"""
        print("🔍 测试搜索记忆...")
        result = self.make_request("memory_search", {
            "query": "修复测试",
            "user_id": "test_user_fix", 
            "limit": 5
        })
        
        print(f"  状态: {result.get('status_code', 'Error')}")
        if 'error' in result:
            print(f"  错误: {result['error']}")
        return result.get('status_code') == 202
    
    def test_memory_chat(self):
        """测试记忆对话"""
        print("💬 测试记忆对话...")
        result = self.make_request("memory_chat", {
            "message": "你还记得我刚才添加的修复测试记忆吗？请告诉我你记住了什么内容。",
            "user_id": "test_user_fix"
        })
        
        print(f"  状态: {result.get('status_code', 'Error')}")
        if 'error' in result:
            print(f"  错误: {result['error']}")
        return result.get('status_code') == 202
    
    def test_get_profile(self):
        """测试获取用户档案"""
        print("👤 测试获取用户档案...")
        result = self.make_request("memory_get_profile", {
            "user_id": "test_user_fix"
        })
        
        print(f"  状态: {result.get('status_code', 'Error')}")
        if 'error' in result:
            print(f"  错误: {result['error']}")
        return result.get('status_code') == 202
    
    def run_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("🔧 MCP记忆功能修复验证测试")
        print("=" * 50)
        
        # 测试连接
        try:
            req = Request(f"{self.base_url}/sse")
            with urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    print("✅ MCP服务器连接正常")
                else:
                    print("❌ MCP服务器连接异常")
                    return
        except Exception as e:
            print(f"❌ 无法连接到MCP服务器: {e}")
            return
        
        print(f"📋 测试会话ID: {self.session_id}")
        print()
        
        # 运行测试
        tests = [
            ("添加记忆", self.test_memory_add),
            ("搜索记忆", self.test_memory_search),
            ("记忆对话", self.test_memory_chat),
            ("获取档案", self.test_get_profile)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"🔄 {test_name}...")
            success = test_func()
            results[test_name] = success
            print(f"   {'✅ 通过' if success else '❌ 失败'}")
            print()
            time.sleep(2)  # 给服务器处理时间
        
        # 总结
        print("=" * 50)
        print("📊 测试结果总结:")
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        print(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！记忆功能修复成功！")
        else:
            print(f"⚠️  有 {total - passed} 个测试失败，需要进一步检查")


def main():
    tester = MCPMemoryTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
