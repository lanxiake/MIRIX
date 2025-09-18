#!/usr/bin/env python3
"""
测试MARKDOWN文档上传功能
"""
import requests
import base64
import json

# 测试MARKDOWN内容
markdown_content = """# 测试文档

这是一个测试MARKDOWN文档。

## 功能特性

- 支持标题
- 支持列表
- 支持代码块

```python
def hello_world():
    print("Hello, World!")
```

## 总结

这是一个完整的MARKDOWN文档测试。
"""

def test_markdown_upload():
    """测试MARKDOWN文档上传"""
    print("开始测试MARKDOWN文档上传...")
    
    # 编码文档内容
    encoded_content = base64.b64encode(markdown_content.encode('utf-8')).decode('utf-8')
    
    # 构建请求数据
    request_data = {
        "file_name": "test_document.md",
        "file_type": "md",
        "content": encoded_content,
        "user_id": None
    }
    
    # 发送请求
    try:
        response = requests.post(
            "http://localhost:47283/documents/upload",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            print("上传成功!")
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("上传失败!")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_markdown_upload()