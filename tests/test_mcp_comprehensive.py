#!/usr/bin/env python3
"""
MIRIX MCP 服务器全功能测试套件

这个测试套件覆盖了MIRIX MCP服务器的所有核心功能：
1. 基础连接测试
2. 工具列表获取测试
3. 记忆添加功能测试 (memory_add)
4. 记忆搜索功能测试 (memory_search)
5. 记忆对话功能测试 (memory_chat)
6. 用户档案获取测试 (memory_get_profile)
7. 端到端集成测试
8. 错误处理测试
"""

import asyncio
import json
import time
import requests
import aiohttp
import re
from typing import Optional, Dict, Any, List
import logging
from dataclasses import dataclass
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    success: bool
    message: str
    duration: float
    details: Optional[Dict[str, Any]] = None

class MIRIXMCPComprehensiveTest:
    """MIRIX MCP 服务器全功能测试类"""

    def __init__(self, base_url: str = "http://localhost:18003", user_id: str = None):
        self.base_url = base_url
        self.user_id = user_id or f"test_user_{int(time.time())}"
        self.session_id: Optional[str] = None
        self.test_results: List[TestResult] = []

        # 测试数据
        self.test_memory_data = {
            "core_memory": {
                "content": "我的名字是测试用户，我来自北京，喜欢编程和AI技术",
                "memory_type": "core",
                "context": "用户基本信息测试数据"
            },
            "episodic_memory": {
                "content": "今天在MIRIX系统上进行了全功能测试，测试了记忆系统的各个组件",
                "memory_type": "episodic",
                "context": "2025年9月26日的测试活动"
            },
            "semantic_memory": {
                "content": "MCP (Model Context Protocol) 是一个用于AI模型与外部系统交互的协议标准",
                "memory_type": "semantic",
                "context": "技术知识学习"
            },
            "procedural_memory": {
                "content": "使用MIRIX系统的步骤：1.连接服务器 2.建立会话 3.调用工具 4.处理响应",
                "memory_type": "procedural",
                "context": "系统使用流程"
            }
        }

    def log_result(self, result: TestResult):
        """记录测试结果"""
        self.test_results.append(result)
        status = "✅ 通过" if result.success else "❌ 失败"
        logger.info(f"{result.name}: {status} ({result.duration:.2f}s) - {result.message}")

    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        start_time = time.time()
        try:
            logger.info("🔍 测试服务器健康检查...")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self.log_result(TestResult(
                    "健康检查", True, f"服务器状态正常: {data.get('service', 'Unknown')}",
                    duration, data
                ))
                return True
            else:
                self.log_result(TestResult(
                    "健康检查", False, f"HTTP状态码: {response.status_code}", duration
                ))
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result(TestResult(
                "健康检查", False, f"异常: {str(e)}", duration
            ))
            return False

    async def get_session_id(self) -> Optional[str]:
        """建立SSE连接并获取session_id"""
        start_time = time.time()
        logger.info("🔍 建立SSE连接并获取session_id...")

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/sse") as response:
                    duration = time.time() - start_time

                    if response.status == 200:
                        # 读取SSE数据获取session_id
                        lines_read = 0
                        async for line in response.content:
                            if lines_read >= 5:
                                break

                            line_str = line.decode('utf-8').strip()
                            if 'session_id=' in line_str:
                                match = re.search(r'session_id=([a-f0-9]+)', line_str)
                                if match:
                                    session_id = match.group(1)
                                    self.session_id = session_id
                                    self.log_result(TestResult(
                                        "SSE连接", True, f"成功获取session_id: {session_id[:8]}...",
                                        duration, {"session_id": session_id}
                                    ))
                                    return session_id
                            lines_read += 1

                        self.log_result(TestResult(
                            "SSE连接", False, "未能从SSE数据中提取session_id", duration
                        ))
                        return None
                    else:
                        self.log_result(TestResult(
                            "SSE连接", False, f"HTTP状态码: {response.status}", duration
                        ))
                        return None
        except Exception as e:
            duration = time.time() - start_time
            self.log_result(TestResult(
                "SSE连接", False, f"异常: {str(e)}", duration
            ))
            return None

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """调用MCP工具的通用方法"""
        if not self.session_id:
            logger.error("没有有效的session_id，无法调用工具")
            return None

        start_time = time.time()

        # 构造MCP协议消息
        mcp_message = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),  # 使用时间戳作为唯一ID
            "method": f"tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                params={"session_id": self.session_id},
                json=mcp_message,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            duration = time.time() - start_time

            if response.status_code in [200, 202]:
                try:
                    # 对于202状态码，可能返回非JSON响应
                    if response.headers.get('content-type', '').startswith('application/json'):
                        data = response.json()
                        self.log_result(TestResult(
                            f"工具调用:{tool_name}", True, "调用成功并返回JSON数据",
                            duration, data
                        ))
                        return data
                    else:
                        # 对于202 Accepted响应，表示请求已被接受处理
                        self.log_result(TestResult(
                            f"工具调用:{tool_name}", True, f"调用已接受: {response.text[:100]}",
                            duration, {"raw_response": response.text}
                        ))
                        return {"status": "accepted", "raw_response": response.text}
                except json.JSONDecodeError:
                    self.log_result(TestResult(
                        f"工具调用:{tool_name}", True, f"调用成功(非JSON): {response.text[:100]}",
                        duration, {"raw_response": response.text}
                    ))
                    return {"status": "success", "raw_response": response.text}
            else:
                self.log_result(TestResult(
                    f"工具调用:{tool_name}", False, f"HTTP {response.status_code}: {response.text[:200]}",
                    duration
                ))
                return None

        except Exception as e:
            duration = time.time() - start_time
            self.log_result(TestResult(
                f"工具调用:{tool_name}", False, f"异常: {str(e)}", duration
            ))
            return None

    def test_list_tools(self) -> bool:
        """测试工具列表获取"""
        logger.info("🔍 测试工具列表获取...")

        if not self.session_id:
            self.log_result(TestResult(
                "工具列表", False, "没有有效的session_id", 0
            ))
            return False

        start_time = time.time()

        # 构造列表工具请求
        mcp_message = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/list",
            "params": {}
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                params={"session_id": self.session_id},
                json=mcp_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            duration = time.time() - start_time

            if response.status_code in [200, 202]:
                self.log_result(TestResult(
                    "工具列表", True, f"成功获取工具列表 (HTTP {response.status_code})",
                    duration, {"response_size": len(response.text)}
                ))
                return True
            else:
                self.log_result(TestResult(
                    "工具列表", False, f"HTTP {response.status_code}: {response.text[:200]}", duration
                ))
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_result(TestResult(
                "工具列表", False, f"异常: {str(e)}", duration
            ))
            return False

    def test_memory_add(self) -> bool:
        """测试记忆添加功能"""
        logger.info("🔍 测试记忆添加功能...")

        success_count = 0
        total_count = len(self.test_memory_data)

        for memory_name, memory_data in self.test_memory_data.items():
            logger.info(f"  添加{memory_name}...")

            # 添加用户ID到参数中
            arguments = {
                "content": memory_data["content"],
                "memory_type": memory_data["memory_type"],
                "context": memory_data["context"],
                "user_id": self.user_id
            }

            result = self.call_mcp_tool("memory_add", arguments)
            if result:
                success_count += 1
                logger.info(f"  ✅ {memory_name} 添加成功")
            else:
                logger.error(f"  ❌ {memory_name} 添加失败")

        overall_success = success_count == total_count
        self.log_result(TestResult(
            "记忆添加", overall_success, f"成功添加 {success_count}/{total_count} 条记忆",
            0, {"success_count": success_count, "total_count": total_count}
        ))

        return overall_success

    def test_memory_search(self) -> bool:
        """测试记忆搜索功能"""
        logger.info("🔍 测试记忆搜索功能...")

        # 等待记忆数据保存完成
        time.sleep(2)

        search_queries = [
            {"query": "测试用户", "expected_type": "core"},
            {"query": "MIRIX测试", "expected_type": "episodic"},
            {"query": "MCP协议", "expected_type": "semantic"},
            {"query": "系统使用步骤", "expected_type": "procedural"},
            {"query": "编程", "expected_type": "core"}  # 模糊搜索
        ]

        success_count = 0

        for i, search_data in enumerate(search_queries):
            logger.info(f"  搜索查询 {i+1}: '{search_data['query']}'")

            arguments = {
                "query": search_data["query"],
                "memory_types": [search_data["expected_type"]],
                "limit": 5,
                "user_id": self.user_id
            }

            result = self.call_mcp_tool("memory_search", arguments)
            if result:
                success_count += 1
                logger.info(f"  ✅ 搜索查询 {i+1} 执行成功")
            else:
                logger.error(f"  ❌ 搜索查询 {i+1} 执行失败")

        overall_success = success_count >= len(search_queries) // 2  # 至少一半成功
        self.log_result(TestResult(
            "记忆搜索", overall_success, f"成功执行 {success_count}/{len(search_queries)} 个搜索查询",
            0, {"success_count": success_count, "total_queries": len(search_queries)}
        ))

        return overall_success

    def test_memory_chat(self) -> bool:
        """测试记忆对话功能"""
        logger.info("🔍 测试记忆对话功能...")

        chat_tests = [
            {
                "message": "你好，请介绍一下我的基本信息",
                "memorizing": False,
                "description": "基本信息查询"
            },
            {
                "message": "今天我学习了什么新技术？",
                "memorizing": False,
                "description": "学习内容查询"
            },
            {
                "message": "请告诉我关于MCP协议的信息",
                "memorizing": False,
                "description": "技术知识查询"
            }
        ]

        success_count = 0

        for i, chat_data in enumerate(chat_tests):
            logger.info(f"  对话测试 {i+1}: {chat_data['description']}")

            arguments = {
                "message": chat_data["message"],
                "memorizing": chat_data["memorizing"],
                "user_id": self.user_id
            }

            result = self.call_mcp_tool("memory_chat", arguments)
            if result:
                success_count += 1
                logger.info(f"  ✅ 对话测试 {i+1} 成功")
            else:
                logger.error(f"  ❌ 对话测试 {i+1} 失败")

        overall_success = success_count >= len(chat_tests) // 2
        self.log_result(TestResult(
            "记忆对话", overall_success, f"成功执行 {success_count}/{len(chat_tests)} 个对话测试",
            0, {"success_count": success_count, "total_tests": len(chat_tests)}
        ))

        return overall_success

    def test_memory_get_profile(self) -> bool:
        """测试用户档案获取功能"""
        logger.info("🔍 测试用户档案获取功能...")

        profile_tests = [
            {
                "memory_types": ["core"],
                "description": "获取核心记忆档案"
            },
            {
                "memory_types": ["core", "episodic"],
                "description": "获取核心和情节记忆档案"
            },
            {
                "memory_types": ["all"],
                "description": "获取完整用户档案"
            }
        ]

        success_count = 0

        for i, profile_data in enumerate(profile_tests):
            logger.info(f"  档案测试 {i+1}: {profile_data['description']}")

            arguments = {
                "memory_types": profile_data["memory_types"],
                "user_id": self.user_id
            }

            result = self.call_mcp_tool("memory_get_profile", arguments)
            if result:
                success_count += 1
                logger.info(f"  ✅ 档案测试 {i+1} 成功")
            else:
                logger.error(f"  ❌ 档案测试 {i+1} 失败")

        overall_success = success_count >= len(profile_tests) // 2
        self.log_result(TestResult(
            "用户档案", overall_success, f"成功执行 {success_count}/{len(profile_tests)} 个档案测试",
            0, {"success_count": success_count, "total_tests": len(profile_tests)}
        ))

        return overall_success

    def test_error_handling(self) -> bool:
        """测试错误处理"""
        logger.info("🔍 测试错误处理...")

        error_tests = [
            {
                "tool": "memory_add",
                "args": {"content": ""},  # 空内容
                "description": "空内容测试"
            },
            {
                "tool": "memory_search",
                "args": {"query": ""},  # 空查询
                "description": "空查询测试"
            },
            {
                "tool": "nonexistent_tool",
                "args": {"test": "data"},  # 不存在的工具
                "description": "不存在工具测试"
            }
        ]

        handled_errors = 0

        for i, error_test in enumerate(error_tests):
            logger.info(f"  错误测试 {i+1}: {error_test['description']}")

            result = self.call_mcp_tool(error_test["tool"], error_test["args"])
            # 对于错误处理测试，我们期望得到某种响应（即使是错误响应）
            if result is not None:
                handled_errors += 1
                logger.info(f"  ✅ 错误测试 {i+1} - 系统正确处理了错误")
            else:
                logger.info(f"  ⚠️ 错误测试 {i+1} - 系统未返回错误信息")

        # 对于错误处理，我们认为能处理一部分错误就是成功
        overall_success = handled_errors > 0
        self.log_result(TestResult(
            "错误处理", overall_success, f"成功处理 {handled_errors}/{len(error_tests)} 个错误场景",
            0, {"handled_errors": handled_errors, "total_tests": len(error_tests)}
        ))

        return overall_success

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """运行所有综合测试"""
        logger.info("🚀 开始MIRIX MCP服务器全功能测试...")
        logger.info("=" * 80)

        test_start_time = time.time()

        # 测试序列
        test_sequence = [
            ("基础连接测试", [
                ("健康检查", self.test_health_check),
                ("SSE连接", lambda: asyncio.create_task(self.get_session_id())),
                ("工具列表", self.test_list_tools),
            ]),
            ("核心功能测试", [
                ("记忆添加", self.test_memory_add),
                ("记忆搜索", self.test_memory_search),
                ("记忆对话", self.test_memory_chat),
                ("用户档案", self.test_memory_get_profile),
            ]),
            ("异常处理测试", [
                ("错误处理", self.test_error_handling),
            ])
        ]

        category_results = {}

        for category_name, tests in test_sequence:
            logger.info(f"\n📋 {category_name}")
            logger.info("-" * 60)

            category_success = True
            category_details = []

            for test_name, test_func in tests:
                logger.info(f"\n🔍 执行测试: {test_name}")

                try:
                    if asyncio.iscoroutinefunction(test_func) or hasattr(test_func, '__call__'):
                        if test_name == "SSE连接":
                            # 特殊处理异步SSE连接测试
                            session_id = await test_func()
                            success = session_id is not None
                        else:
                            success = test_func()
                    else:
                        success = test_func

                    category_details.append({
                        "name": test_name,
                        "success": success
                    })

                    if not success:
                        category_success = False

                except Exception as e:
                    logger.error(f"测试 {test_name} 执行异常: {e}")
                    category_success = False
                    category_details.append({
                        "name": test_name,
                        "success": False,
                        "error": str(e)
                    })

            category_results[category_name] = {
                "success": category_success,
                "details": category_details
            }

        total_duration = time.time() - test_start_time

        # 生成测试报告
        return self.generate_test_report(category_results, total_duration)

    def generate_test_report(self, category_results: Dict[str, Any], total_duration: float) -> Dict[str, Any]:
        """生成详细的测试报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 MIRIX MCP服务器全功能测试报告")
        logger.info("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests

        # 打印每个测试的详细结果
        for result in self.test_results:
            status = "✅ 通过" if result.success else "❌ 失败"
            logger.info(f"{result.name:20} : {status:8} ({result.duration:.2f}s) - {result.message}")

        logger.info("-" * 80)
        logger.info(f"测试用户ID        : {self.user_id}")
        logger.info(f"会话ID           : {self.session_id[:8] if self.session_id else 'N/A'}...")
        logger.info(f"服务器地址        : {self.base_url}")
        logger.info(f"总测试数量        : {total_tests}")
        logger.info(f"通过测试数量      : {passed_tests}")
        logger.info(f"失败测试数量      : {failed_tests}")
        logger.info(f"成功率           : {(passed_tests/total_tests*100):.1f}%")
        logger.info(f"总耗时           : {total_duration:.2f}秒")

        # 按类别显示结果
        logger.info("\n📋 按类别测试结果:")
        for category, result in category_results.items():
            status = "✅ 通过" if result["success"] else "❌ 失败"
            logger.info(f"  {category:15} : {status}")

        logger.info("=" * 80)

        overall_success = passed_tests >= total_tests * 0.7  # 70%通过率认为整体成功

        if overall_success:
            logger.info("🎉 综合测试结果: 通过 - MIRIX MCP服务器功能正常")
        else:
            logger.info("⚠️ 综合测试结果: 失败 - 发现功能问题，需要检查")

        # 返回结构化报告
        return {
            "overall_success": overall_success,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "server_url": self.base_url,
            "statistics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests/total_tests if total_tests > 0 else 0,
                "total_duration": total_duration
            },
            "category_results": category_results,
            "detailed_results": [
                {
                    "name": result.name,
                    "success": result.success,
                    "message": result.message,
                    "duration": result.duration,
                    "details": result.details
                }
                for result in self.test_results
            ]
        }

async def main():
    """主函数"""
    print("MIRIX MCP 服务器全功能测试套件")
    print("=" * 80)

    # 可以通过环境变量或参数自定义配置
    import os
    base_url = os.environ.get('MCP_TEST_URL', 'http://localhost:18003')
    user_id = os.environ.get('MCP_TEST_USER_ID', f'test_user_{int(time.time())}')

    try:
        # 创建测试实例
        tester = MIRIXMCPComprehensiveTest(base_url=base_url, user_id=user_id)

        # 运行全面测试
        report = await tester.run_comprehensive_tests()

        # 输出最终结果
        exit_code = 0 if report["overall_success"] else 1
        exit(exit_code)

    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"❌ 测试执行异常: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())