#!/usr/bin/env python3
"""
诊断脚本，检查运行中的服务器状态
"""

import requests
import json


def diagnose_server():
    """诊断服务器状态"""
    print("开始诊断服务器状态...")

    try:
        # 首先检查服务器健康状态
        health_url = "http://10.157.152.40:47283/health"
        response = requests.get(health_url, timeout=10)
        print(f"健康检查状态: {response.status_code}")
        if response.status_code == 200:
            print("服务器运行正常")
        else:
            print("服务器可能有问题")
            return

        # 直接调用一个简单的API来查看是否有具体错误信息
        # 先尝试获取用户信息
        users_url = "http://10.157.152.40:47283/users"
        try:
            response = requests.get(users_url, timeout=10)
            print(f"用户API状态: {response.status_code}")
            if response.status_code == 200:
                users_data = response.json()
                print(f"用户数量: {len(users_data.get('users', []))}")
            else:
                print(f"用户API错误: {response.text}")
        except Exception as e:
            print(f"用户API异常: {e}")

        # 尝试一个更简单的文档上传来获取详细错误
        print("\n尝试简化的文档上传...")

        import base64
        simple_content = "# 测试\n这是一个简单的测试文档。"
        encoded_content = base64.b64encode(simple_content.encode('utf-8')).decode('utf-8')

        upload_data = {
            "file_name": "test.md",
            "file_type": "md",
            "content": encoded_content,
            "user_id": None
        }

        upload_url = "http://10.157.152.40:47283/documents/upload"
        response = requests.post(upload_url, json=upload_data, timeout=30)

        print(f"上传状态: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        try:
            response_data = response.json()
            print(f"响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            if not response_data.get("success"):
                error_msg = response_data.get('message', '未知错误')
                print(f"\n详细错误: {error_msg}")

                # 如果是create_resource错误，说明问题确实存在
                if 'create_resource' in error_msg:
                    print("确认：create_resource方法缺失错误")
                    print("这表明运行时的ResourceMemoryManager实例有问题")

        except json.JSONDecodeError:
            print(f"无法解析JSON响应: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except Exception as e:
        print(f"诊断异常: {e}")


if __name__ == "__main__":
    diagnose_server()