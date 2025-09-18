#!/usr/bin/env python3
"""
简单测试MARKDOWN文档处理器
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from mirix.services.document_processor import DocumentProcessor
from pathlib import Path
import traceback

def test_markdown_processor():
    """测试MARKDOWN文档处理器"""
    
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
    
    print("开始测试MARKDOWN文档处理器...")
    print(f"文档内容长度: {len(markdown_content)} 字符")
    
    try:
        # 创建文档处理器
        processor = DocumentProcessor()
        print("文档处理器创建成功")
        
        # 处理MARKDOWN内容
        content_bytes = markdown_content.encode('utf-8')
        file_path = Path("test.md")
        
        print("开始处理MARKDOWN文档...")
        result = processor._process_markdown(file_path, content_bytes)
        
        print("MARKDOWN文档处理成功!")
        print(f"文件名: {result['file_name']}")
        print(f"文件类型: {result['file_type']}")
        print(f"字符数: {result['char_count']}")
        print(f"单词数: {result['word_count']}")
        print(f"标题数: {len(result['headers'])}")
        print(f"摘要: {result['summary'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"MARKDOWN文档处理失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_markdown_processor()
    
    if success:
        print("\n✅ MARKDOWN文档处理器测试成功")
        sys.exit(0)
    else:
        print("\n❌ MARKDOWN文档处理器测试失败")
        sys.exit(1)