#!/usr/bin/env python3
"""
详细调试MARKDOWN文档上传失败的问题
"""
import requests
import base64
import json
import sys
import traceback

def test_markdown_upload_debug(base_url):
    """详细测试MARKDOWN文档上传并捕获错误信息"""
    
    # 创建测试MARKDOWN内容
    markdown_content = """# 测试文档

这是一个测试MARKDOWN文档。

## 功能特性

- 支持标题
- 支持列表
- 支持**粗体**和*斜体*

## 代码示例

```python
def hello_world():
    print("Hello, World!")
```

## 总结

这是一个简单的测试文档。
"""
    
    print(f"开始测试MARKDOWN文档上传到: {base_url}")
    print(f"文档内容长度: {len(markdown_content)} 字符")
    
    try:
        # Base64编码内容
        import base64
        encoded_content = base64.b64encode(markdown_content.encode('utf-8')).decode('utf-8')
        
        # 准备JSON请求数据
        request_data = {
            "file_name": "test_markdown.md",
            "file_type": "markdown",
            "content": encoded_content,
            "user_id": None
        }
        
        # 发送上传请求
        print("发送上传请求...")
        print(f"请求数据: file_name={request_data['file_name']}, file_type={request_data['file_type']}")
        
        response = requests.post(
            f"{base_url}/documents/upload",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("上传成功!")
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"上传失败! 状态码: {response.status_code}")
            print(f"错误响应: {response.text}")
            
            # 尝试解析JSON错误信息
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print("无法解析错误响应为JSON")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        print(f"异常类型: {type(e).__name__}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"其他异常: {e}")
        print(f"异常类型: {type(e).__name__}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python test_markdown_debug.py <base_url>")
        print("示例: python test_markdown_debug.py http://localhost:47283")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    success = test_markdown_upload_debug(base_url)
    
    if success:
        print("\n✅ MARKDOWN文档上传测试成功")
        sys.exit(0)
    else:
        print("\n❌ MARKDOWN文档上传测试失败")
        sys.exit(1)