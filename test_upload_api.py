#!/usr/bin/env python3
"""
测试文档上传API
"""

import requests
import base64
import json

def test_upload_api():
    # 读取测试文件
    with open('simple_test.md', 'rb') as f:
        file_content = f.read()
    
    # Base64编码
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    
    # 准备请求数据
    data = {
        "file_name": "simple_test.md",
        "file_type": "md",
        "content": encoded_content,
        "user_id": None,
        "description": "Simple test upload"
    }
    
    # 发送请求
    url = "http://10.157.152.40:47284/api/documents/upload"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ 文档上传成功!")
        else:
            print("❌ 文档上传失败")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_upload_api()
