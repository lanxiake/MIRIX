#!/usr/bin/env python3
"""
测试前端上传功能
"""

import requests
import base64
import json

def test_frontend_upload():
    # 读取测试文件
    with open('simple_test.md', 'rb') as f:
        file_content = f.read()
    
    # Base64编码
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    
    # 准备请求数据（模拟前端请求）
    data = {
        "file_name": "simple_test.md",
        "file_type": "md",
        "content": encoded_content,
        "user_id": None,
        "description": "Frontend test upload"
    }
    
    # 使用前端配置的URL
    url = "http://10.157.152.40:47283/api/documents/upload"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ 前端文档上传成功!")
            return True
        else:
            print("❌ 前端文档上传失败")
            return False
            
    except Exception as e:
        print(f"请求失败: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend_upload()
    if success:
        print("\n🎉 文档上传功能修复成功！")
        print("前端现在可以正常上传文档到记忆系统了。")
    else:
        print("\n❌ 文档上传功能仍有问题。")
