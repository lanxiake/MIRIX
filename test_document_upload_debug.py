#!/usr/bin/env python3
"""
测试文档上传功能，用于调试 create_resource 错误
"""

import requests
import base64
import json


def test_document_upload():
    """测试文档上传"""

    # 测试文档内容
    test_content = """# CSRF防护与MaxKey SSO兼容方案

## 概述
本文档描述了CSRF防护机制与MaxKey SSO系统的兼容性方案。

## 主要内容
1. CSRF攻击原理
2. 防护措施
3. 与SSO系统的集成方案
4. 最佳实践建议

## 详细说明
CSRF（Cross-Site Request Forgery）是一种常见的Web安全威胁...
"""

    # Base64编码内容
    encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')

    # 构建请求数据
    request_data = {
        "file_name": "CSRF防护与MaxKey_SSO兼容方案.md",
        "file_type": "md",
        "content": encoded_content,
        "user_id": None
    }

    print("开始测试文档上传...")
    print(f"文档名称: {request_data['file_name']}")
    print(f"文档类型: {request_data['file_type']}")
    print(f"内容长度: {len(test_content)} 字符")

    try:
        # 发送请求
        url = "http://localhost:47283/documents/upload"
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url,
                               json=request_data,
                               headers=headers,
                               timeout=30)

        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        try:
            response_data = response.json()
            print(f"响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            if response_data.get("success"):
                print("\n文档上传成功!")
                print(f"文档ID: {response_data.get('document_id')}")
            else:
                print("\n文档上传失败!")
                print(f"错误信息: {response_data.get('message')}")

        except json.JSONDecodeError:
            print(f"响应文本: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except Exception as e:
        print(f"未知错误: {e}")


if __name__ == "__main__":
    test_document_upload()