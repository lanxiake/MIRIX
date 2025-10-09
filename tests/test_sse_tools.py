#!/usr/bin/env python3
"""
MCP SSE 工具测试脚本

该脚本提供全面的 MCP SSE 服务器工具功能测试，包括：
1. 连接测试 - 验证 SSE 连接和消息端点
2. 工具功能测试 - 测试所有可用的记忆工具
3. 错误处理测试 - 验证异常情况的处理
4. 性能测试 - 评估响应时间和并发能力
5. 集成测试 - 端到端功能验证

使用方法：
    python test_sse_tools.py [选项]

选项：
    --host HOST         服务器主机地址 (默认: localhost)
    --port PORT         服务器端口 (默认: 18002)
    --verbose          详细输出模式
    --quick            快速测试模式（跳过性能测试）
    --tool TOOL        测试特定工具（memory_add, memory_search, memory_chat, memory_get_profile）

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import asyncio
import json
import time
import argparse
import sys
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult(Enum):
    """测试结果枚举"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestCase:
    """测试用例数据结构"""
    name: str
    description: str
    test_func: callable
    expected_result: TestResult = TestResult.PASS
    timeout: int = 30
    prerequisites: List[str] = None


@dataclass
class TestReport:
    """测试报告数据结构"""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    start_time: datetime = None
    end_time: datetime = None
    details: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


class SSEToolTester:
    """SSE 工具测试器主类"""
    
    def __init__(self, host: str = "localhost", port: int = 18002, verbose: bool = False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.base_url = f"http://{host}:{port}"
        self.sse_url = f"{self.base_url}/sse"
        self.message_url = f"{self.base_url}/messages"
        self.session = None
        self.test_report = TestReport()
        
        # 测试用例注册
        self.test_cases = self._register_test_cases()
        
    def _register_test_cases(self) -> List[TestCase]:
        """注册所有测试用例"""
        return [
            # 连接测试
            TestCase(
                name="sse_connection_test",
                description="测试 SSE 连接端点",
                test_func=self._test_sse_connection
            ),
            TestCase(
                name="message_endpoint_test", 
                description="测试消息端点可达性",
                test_func=self._test_message_endpoint
            ),
            TestCase(
                name="initialize_protocol_test",
                description="测试 MCP 协议初始化",
                test_func=self._test_initialize_protocol
            ),
            
            # 工具功能测试
            TestCase(
                name="list_tools_test",
                description="测试工具列表获取",
                test_func=self._test_list_tools
            ),
            TestCase(
                name="memory_add_test",
                description="测试记忆添加功能",
                test_func=self._test_memory_add
            ),
            TestCase(
                name="memory_search_test",
                description="测试记忆搜索功能", 
                test_func=self._test_memory_search,
                prerequisites=["memory_add_test"]
            ),
            TestCase(
                name="memory_chat_test",
                description="测试记忆对话功能",
                test_func=self._test_memory_chat,
                prerequisites=["memory_add_test"]
            ),
            TestCase(
                name="memory_get_profile_test",
                description="测试获取用户配置功能",
                test_func=self._test_memory_get_profile
            ),
            
            # 错误处理测试
            TestCase(
                name="invalid_method_test",
                description="测试无效方法处理",
                test_func=self._test_invalid_method,
                expected_result=TestResult.PASS  # 期望正确处理错误
            ),
            TestCase(
                name="malformed_request_test",
                description="测试格式错误请求处理",
                test_func=self._test_malformed_request,
                expected_result=TestResult.PASS
            ),
            TestCase(
                name="missing_parameters_test",
                description="测试缺失参数处理",
                test_func=self._test_missing_parameters,
                expected_result=TestResult.PASS
            ),
            
            # 性能测试
            TestCase(
                name="response_time_test",
                description="测试响应时间性能",
                test_func=self._test_response_time
            ),
            TestCase(
                name="concurrent_requests_test",
                description="测试并发请求处理",
                test_func=self._test_concurrent_requests
            )
        ]
    
    async def run_all_tests(self, quick_mode: bool = False, specific_tool: str = None) -> TestReport:
        """运行所有测试用例"""
        self.test_report.start_time = datetime.now()
        
        print(f"\n🚀 开始 MCP SSE 工具测试")
        print(f"📍 服务器地址: {self.base_url}")
        print(f"⏰ 开始时间: {self.test_report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 创建 HTTP 会话
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # 过滤测试用例
            test_cases = self._filter_test_cases(quick_mode, specific_tool)
            self.test_report.total_tests = len(test_cases)
            
            # 执行测试用例
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n[{i}/{len(test_cases)}] 🧪 {test_case.name}")
                print(f"📝 {test_case.description}")
                
                # 检查前置条件
                if not self._check_prerequisites(test_case):
                    result = await self._skip_test(test_case, "前置条件未满足")
                else:
                    result = await self._run_single_test(test_case)
                
                self._update_report(result)
                self._print_test_result(result)
        
        self.test_report.end_time = datetime.now()
        self._print_final_report()
        return self.test_report
    
    def _filter_test_cases(self, quick_mode: bool, specific_tool: str) -> List[TestCase]:
        """过滤测试用例"""
        test_cases = self.test_cases.copy()
        
        if quick_mode:
            # 快速模式跳过性能测试
            test_cases = [tc for tc in test_cases if not tc.name.endswith('_performance_test')]
        
        if specific_tool:
            # 测试特定工具
            test_cases = [tc for tc in test_cases if specific_tool in tc.name]
        
        return test_cases
    
    def _check_prerequisites(self, test_case: TestCase) -> bool:
        """检查测试前置条件"""
        if not test_case.prerequisites:
            return True
        
        # 检查前置测试是否通过
        for prereq in test_case.prerequisites:
            prereq_passed = any(
                detail['name'] == prereq and detail['result'] == TestResult.PASS.value
                for detail in self.test_report.details
            )
            if not prereq_passed:
                return False
        
        return True
    
    async def _run_single_test(self, test_case: TestCase) -> Dict[str, Any]:
        """运行单个测试用例"""
        start_time = time.time()
        
        try:
            # 设置超时
            result = await asyncio.wait_for(
                test_case.test_func(),
                timeout=test_case.timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'name': test_case.name,
                'description': test_case.description,
                'result': TestResult.PASS.value if result else TestResult.FAIL.value,
                'duration': duration,
                'details': result if isinstance(result, dict) else {},
                'error': None
            }
            
        except asyncio.TimeoutError:
            return {
                'name': test_case.name,
                'description': test_case.description,
                'result': TestResult.ERROR.value,
                'duration': test_case.timeout,
                'details': {},
                'error': f"测试超时 ({test_case.timeout}s)"
            }
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'name': test_case.name,
                'description': test_case.description,
                'result': TestResult.ERROR.value,
                'duration': duration,
                'details': {},
                'error': str(e)
            }
    
    async def _skip_test(self, test_case: TestCase, reason: str) -> Dict[str, Any]:
        """跳过测试用例"""
        return {
            'name': test_case.name,
            'description': test_case.description,
            'result': TestResult.SKIP.value,
            'duration': 0,
            'details': {},
            'error': reason
        }
    
    def _update_report(self, result: Dict[str, Any]):
        """更新测试报告"""
        self.test_report.details.append(result)
        
        if result['result'] == TestResult.PASS.value:
            self.test_report.passed_tests += 1
        elif result['result'] == TestResult.FAIL.value:
            self.test_report.failed_tests += 1
        elif result['result'] == TestResult.SKIP.value:
            self.test_report.skipped_tests += 1
        elif result['result'] == TestResult.ERROR.value:
            self.test_report.error_tests += 1
    
    def _print_test_result(self, result: Dict[str, Any]):
        """打印测试结果"""
        status_icons = {
            TestResult.PASS.value: "✅",
            TestResult.FAIL.value: "❌", 
            TestResult.SKIP.value: "⏭️",
            TestResult.ERROR.value: "💥"
        }
        
        icon = status_icons.get(result['result'], "❓")
        duration = f"{result['duration']:.2f}s"
        
        print(f"   {icon} {result['result']} ({duration})")
        
        if result['error']:
            print(f"   🔍 错误: {result['error']}")
        
        if self.verbose and result['details']:
            print(f"   📊 详情: {json.dumps(result['details'], indent=2, ensure_ascii=False)}")
    
    def _print_final_report(self):
        """打印最终测试报告"""
        duration = (self.test_report.end_time - self.test_report.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("📊 测试报告摘要")
        print("=" * 60)
        print(f"⏱️  总耗时: {duration:.2f}s")
        print(f"🧪 总测试数: {self.test_report.total_tests}")
        print(f"✅ 通过: {self.test_report.passed_tests}")
        print(f"❌ 失败: {self.test_report.failed_tests}")
        print(f"⏭️  跳过: {self.test_report.skipped_tests}")
        print(f"💥 错误: {self.test_report.error_tests}")
        
        success_rate = (self.test_report.passed_tests / self.test_report.total_tests * 100) if self.test_report.total_tests > 0 else 0
        print(f"📈 成功率: {success_rate:.1f}%")
        
        if self.test_report.failed_tests > 0 or self.test_report.error_tests > 0:
            print("\n❗ 失败的测试:")
            for detail in self.test_report.details:
                if detail['result'] in [TestResult.FAIL.value, TestResult.ERROR.value]:
                    print(f"   - {detail['name']}: {detail['error'] or '测试失败'}")
    
    # ==================== 具体测试方法 ====================
    
    async def _test_sse_connection(self) -> bool:
        """测试 SSE 连接"""
        try:
            async with self.session.get(self.sse_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    return 'text/event-stream' in content_type
                return False
        except Exception as e:
            logger.error(f"SSE 连接测试失败: {e}")
            return False
    
    async def _test_message_endpoint(self) -> bool:
        """测试消息端点可达性"""
        try:
            # 发送一个简单的 ping 请求
            test_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "ping"
            }
            
            async with self.session.post(
                self.message_url,
                json=test_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                # 即使方法不存在，端点应该是可达的（不应该是 404）
                return response.status != 404
        except Exception as e:
            logger.error(f"消息端点测试失败: {e}")
            return False
    
    async def _test_initialize_protocol(self) -> bool:
        """测试 MCP 协议初始化"""
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=init_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return 'result' in data
                return response.status in [200, 202]  # 接受异步响应
        except Exception as e:
            logger.error(f"协议初始化测试失败: {e}")
            return False
    
    async def _test_list_tools(self) -> bool:
        """测试工具列表获取"""
        try:
            list_tools_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list"
            }
            
            async with self.session.post(
                self.message_url,
                json=list_tools_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 202]
        except Exception as e:
            logger.error(f"工具列表测试失败: {e}")
            return False
    
    async def _test_memory_add(self) -> bool:
        """测试记忆添加功能"""
        try:
            memory_add_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "memory_add",
                    "arguments": {
                        "content": "这是一个测试记忆内容",
                        "memory_type": "core",
                        "context": "SSE工具测试"
                    }
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=memory_add_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 202]
        except Exception as e:
            logger.error(f"记忆添加测试失败: {e}")
            return False
    
    async def _test_memory_search(self) -> bool:
        """测试记忆搜索功能"""
        try:
            memory_search_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "memory_search",
                    "arguments": {
                        "query": "测试记忆",
                        "limit": 5
                    }
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=memory_search_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 202]
        except Exception as e:
            logger.error(f"记忆搜索测试失败: {e}")
            return False
    
    async def _test_memory_chat(self) -> bool:
        """测试记忆对话功能"""
        try:
            memory_chat_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "memory_chat",
                    "arguments": {
                        "message": "你好，请基于我的记忆回答问题"
                    }
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=memory_chat_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 202]
        except Exception as e:
            logger.error(f"记忆对话测试失败: {e}")
            return False
    
    async def _test_memory_get_profile(self) -> bool:
        """测试获取用户配置功能"""
        try:
            get_profile_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "memory_get_profile",
                    "arguments": {}
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=get_profile_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 202]
        except Exception as e:
            logger.error(f"获取配置测试失败: {e}")
            return False
    
    async def _test_invalid_method(self) -> bool:
        """测试无效方法处理"""
        try:
            invalid_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "invalid_method_name"
            }
            
            async with self.session.post(
                self.message_url,
                json=invalid_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                # 应该返回错误响应，而不是崩溃
                return response.status in [400, 404, 405, 500]
        except Exception as e:
            logger.error(f"无效方法测试失败: {e}")
            return False
    
    async def _test_malformed_request(self) -> bool:
        """测试格式错误请求处理"""
        try:
            # 发送格式错误的 JSON
            async with self.session.post(
                self.message_url,
                data="这不是有效的JSON",
                headers={'Content-Type': 'application/json'}
            ) as response:
                # 应该返回错误响应
                return response.status in [400, 422, 500]
        except Exception as e:
            logger.error(f"格式错误请求测试失败: {e}")
            return False
    
    async def _test_missing_parameters(self) -> bool:
        """测试缺失参数处理"""
        try:
            incomplete_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "memory_add"
                    # 缺少 arguments
                }
            }
            
            async with self.session.post(
                self.message_url,
                json=incomplete_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                # 应该返回错误响应
                return response.status in [400, 422, 500]
        except Exception as e:
            logger.error(f"缺失参数测试失败: {e}")
            return False
    
    async def _test_response_time(self) -> bool:
        """测试响应时间性能"""
        try:
            start_time = time.time()
            
            simple_message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list"
            }
            
            async with self.session.post(
                self.message_url,
                json=simple_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                # 响应时间应该在合理范围内（< 5秒）
                return response_time < 5.0 and response.status in [200, 202]
        except Exception as e:
            logger.error(f"响应时间测试失败: {e}")
            return False
    
    async def _test_concurrent_requests(self) -> bool:
        """测试并发请求处理"""
        try:
            # 创建多个并发请求
            tasks = []
            for i in range(5):
                message = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "tools/list"
                }
                
                task = self.session.post(
                    self.message_url,
                    json=message,
                    headers={'Content-Type': 'application/json'}
                )
                tasks.append(task)
            
            # 等待所有请求完成
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查是否所有请求都成功处理
            success_count = 0
            for response in responses:
                if not isinstance(response, Exception):
                    if response.status in [200, 202]:
                        success_count += 1
                    response.close()
            
            # 至少80%的请求应该成功
            return success_count >= len(tasks) * 0.8
        except Exception as e:
            logger.error(f"并发请求测试失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP SSE 工具测试脚本")
    parser.add_argument("--host", default="localhost", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=18002, help="服务器端口")
    parser.add_argument("--verbose", action="store_true", help="详细输出模式")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")
    parser.add_argument("--tool", help="测试特定工具")
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = SSEToolTester(
        host=args.host,
        port=args.port,
        verbose=args.verbose
    )
    
    # 运行测试
    try:
        report = asyncio.run(tester.run_all_tests(
            quick_mode=args.quick,
            specific_tool=args.tool
        ))
        
        # 根据测试结果设置退出码
        if report.failed_tests > 0 or report.error_tests > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 测试执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()