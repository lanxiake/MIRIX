#!/usr/bin/env python3
"""
调试base64编码问题
"""

import base64

def debug_base64():
    # 读取测试文件
    with open('simple_test.md', 'rb') as f:
        file_content = f.read()
    
    print(f"原始文件内容: {file_content}")
    print(f"文件大小: {len(file_content)} bytes")
    
    # Base64编码
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    print(f"Base64编码: {encoded_content}")
    print(f"编码长度: {len(encoded_content)}")
    
    # 尝试解码
    try:
        decoded_content = base64.b64decode(encoded_content)
        print(f"解码成功: {decoded_content}")
        print(f"解码长度: {len(decoded_content)} bytes")
        
        # 检查是否一致
        if decoded_content == file_content:
            print("✅ 编码解码一致")
        else:
            print("❌ 编码解码不一致")
            
    except Exception as e:
        print(f"❌ 解码失败: {e}")

if __name__ == "__main__":
    debug_base64()
