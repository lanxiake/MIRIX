#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文档上传和MCP服务集成功能
支持多种文档格式的上传和记忆存储测试
"""

import asyncio
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import aiohttp
import aiofiles

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentUploadTester:
    """文档上传测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def create_test_files(self) -> Dict[str, str]:
        """创建测试文件"""
        test_files = {}
        test_dir = Path("test_documents")
        test_dir.mkdir(exist_ok=True)
        
        # 创建Markdown测试文件
        md_content = """# 测试文档标题

这是一个测试Markdown文档，用于验证MCP服务集成功能。

## 功能特性

- 支持多种文档格式
- 集成MCP服务处理
- 自动记忆存储
- 智能文本提取

## 技术架构

本系统采用以下技术栈：

1. **后端框架**: FastAPI
2. **MCP协议**: Model Context Protocol
3. **记忆系统**: 资源记忆管理器
4. **文档处理**: 多格式解析器

## 测试用例

这个文档将被用于测试：
- Base64编码/解码
- 文档格式识别
- MCP工具调用
- 记忆系统存储
- 响应数据验证

> 注意：这是一个测试文档，仅用于功能验证。
"""
        
        md_file = test_dir / "test_document.md"
        async with aiofiles.open(md_file, 'w', encoding='utf-8') as f:
            await f.write(md_content)
        test_files["markdown"] = str(md_file)
        
        # 创建文本测试文件
        txt_content = """文档上传测试文件

这是一个纯文本测试文件，用于验证系统对TXT格式的处理能力。

测试内容包括：
- 中文字符处理
- 英文字符处理
- 数字和符号处理
- 换行符处理

系统应该能够：
1. 正确解码Base64内容
2. 识别文件格式为TXT
3. 提取完整文本内容
4. 调用MCP服务处理
5. 存储到记忆系统

测试时间：2024年测试
测试目的：验证MCP服务集成功能
"""
        
        txt_file = test_dir / "test_document.txt"
        async with aiofiles.open(txt_file, 'w', encoding='utf-8') as f:
            await f.write(txt_content)
        test_files["text"] = str(txt_file)
        
        logger.info(f"创建测试文件完成: {list(test_files.keys())}")
        return test_files
    
    async def encode_file_to_base64(self, file_path: str) -> str:
        """将文件编码为Base64"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            encoded = base64.b64encode(content).decode('utf-8')
            logger.info(f"文件编码完成: {file_path}, 大小: {len(encoded)} 字符")
            return encoded
        except Exception as e:
            logger.error(f"文件编码失败: {file_path}, 错误: {e}")
            raise
    
    async def test_server_health(self) -> bool:
        """测试服务器健康状态"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"服务器健康检查通过: {data}")
                    return True
                else:
                    logger.error(f"服务器健康检查失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"服务器连接失败: {e}")
            return False
    
    async def test_mcp_status(self) -> Dict[str, Any]:
        """测试MCP服务状态"""
        try:
            async with self.session.get(f"{self.base_url}/mcp/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"MCP服务状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return data
                else:
                    logger.warning(f"MCP状态检查失败: {response.status}")
                    return {}
        except Exception as e:
            logger.warning(f"MCP状态检查异常: {e}")
            return {}
    
    async def upload_document(self, file_path: str, user_id: str = "test_user") -> Dict[str, Any]:
        """上传文档测试"""
        try:
            # 编码文件内容
            encoded_content = await self.encode_file_to_base64(file_path)
            file_name = Path(file_path).name
            
            # 确定文件类型
            file_extension = Path(file_path).suffix.lower()
            file_type_mapping = {
                '.md': 'markdown',
                '.txt': 'text',
                '.xlsx': 'excel',
                '.xls': 'excel',
                '.csv': 'csv'
            }
            file_type = file_type_mapping.get(file_extension, 'text')
            
            # 构建请求数据
            request_data = {
                "file_name": file_name,
                "file_type": file_type,
                "content": encoded_content,
                "user_id": "user-00000000-0000-4000-8000-000000000000"  # 使用默认用户ID
            }
            
            logger.info(f"开始上传文档: {file_name}")
            
            # 发送上传请求
            async with self.session.post(
                f"{self.base_url}/documents/upload",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_text = await response.text()
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应内容: {response_text}")
                
                if response.status == 200:
                    data = await response.json() if response_text else {}
                    logger.info(f"文档上传成功: {file_name}")
                    logger.info(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return data
                else:
                    logger.error(f"文档上传失败: {file_name}, 状态码: {response.status}")
                    logger.error(f"错误响应: {response_text}")
                    return {"error": f"HTTP {response.status}", "details": response_text}
                    
        except Exception as e:
            logger.error(f"文档上传异常: {file_path}, 错误: {e}")
            return {"error": str(e)}
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        logger.info("=" * 60)
        logger.info("开始文档上传和MCP服务集成测试")
        logger.info("=" * 60)
        
        # 1. 服务器健康检查
        logger.info("\n1. 服务器健康检查")
        if not await self.test_server_health():
            logger.error("服务器不可用，测试终止")
            return
        
        # 2. MCP服务状态检查
        logger.info("\n2. MCP服务状态检查")
        mcp_status = await self.test_mcp_status()
        
        # 3. 创建测试文件
        logger.info("\n3. 创建测试文件")
        test_files = await self.create_test_files()
        
        # 4. 测试文档上传
        logger.info("\n4. 测试文档上传")
        results = {}
        
        for file_type, file_path in test_files.items():
            logger.info(f"\n--- 测试 {file_type.upper()} 格式文档 ---")
            result = await self.upload_document(file_path)
            results[file_type] = result
            
            # 分析结果
            if "error" not in result:
                logger.info(f"✅ {file_type} 文档上传成功")
                if result.get("processed_content", {}).get("mcp_processed"):
                    logger.info("✅ MCP服务处理成功")
                else:
                    logger.warning("⚠️ MCP服务未处理或处理失败")
            else:
                logger.error(f"❌ {file_type} 文档上传失败: {result['error']}")
        
        # 5. 测试结果汇总
        logger.info("\n" + "=" * 60)
        logger.info("测试结果汇总")
        logger.info("=" * 60)
        
        success_count = sum(1 for r in results.values() if "error" not in r)
        mcp_success_count = sum(1 for r in results.values() 
                               if "error" not in r and r.get("processed_content", {}).get("mcp_processed"))
        
        logger.info(f"总测试文件数: {len(test_files)}")
        logger.info(f"上传成功数: {success_count}")
        logger.info(f"MCP处理成功数: {mcp_success_count}")
        logger.info(f"成功率: {success_count/len(test_files)*100:.1f}%")
        logger.info(f"MCP处理率: {mcp_success_count/len(test_files)*100:.1f}%")
        
        # 6. 详细结果输出
        logger.info("\n详细结果:")
        for file_type, result in results.items():
            if "error" not in result:
                processed_content = result.get("processed_content", {})
                logger.info(f"\n{file_type.upper()}:")
                logger.info(f"  - 文档ID: {result.get('document_id')}")
                logger.info(f"  - 文件类型: {processed_content.get('file_type')}")
                logger.info(f"  - 字数统计: {processed_content.get('word_count')}")
                logger.info(f"  - MCP处理: {'是' if processed_content.get('mcp_processed') else '否'}")
                logger.info(f"  - 处理时间: {processed_content.get('processed_at')}")
                if result.get('message'):
                    logger.info(f"  - 响应消息: {result['message']}")
            else:
                logger.error(f"\n{file_type.upper()}: 失败 - {result['error']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("测试完成")
        logger.info("=" * 60)

async def main():
    """主函数"""
    # 检查服务器地址参数
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logger.info(f"测试目标服务器: {server_url}")
    
    # 运行测试
    async with DocumentUploadTester(server_url) as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())