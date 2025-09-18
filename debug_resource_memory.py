#!/usr/bin/env python3
"""
调试资源内存存储功能的脚本
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from mirix.services.resource_memory_manager import ResourceMemoryManager
from mirix.services.user_manager import UserManager
from mirix.schemas.resource_memory import ResourceMemoryItem as PydanticResourceMemoryItem

def debug_resource_memory():
    """调试资源内存存储功能"""
    print("开始调试资源内存存储功能...")

    try:
        # 初始化管理器
        resource_manager = ResourceMemoryManager()
        user_manager = UserManager()
        
        print("OK 管理器初始化成功")

        # 获取默认用户
        default_user = user_manager.get_default_user()
        print(f"使用用户: {default_user.name} (ID: {default_user.id})")
        print(f"用户组织ID: {default_user.organization_id}")

        # 创建测试资源数据
        test_item = PydanticResourceMemoryItem(
            title="测试MARKDOWN文档",
            summary="这是一个测试MARKDOWN文档的摘要",
            content="# 测试标题\n\n这是测试内容。\n\n## 子标题\n\n更多内容...",
            resource_type="markdown",
            tree_path=["test", "documents"],
            metadata_={"source": "debug_test", "type": "markdown"},
            user_id=default_user.id,
            organization_id=default_user.organization_id
        )
        print("OK 测试资源数据创建成功")

        # 尝试创建资源
        print("尝试调用create_item方法...")
        created_resource = resource_manager.create_item(test_item, default_user)
        print(f"OK 资源创建成功!")
        print(f"创建的资源ID: {created_resource.id}")
        print(f"创建的资源标题: {created_resource.title}")
        print(f"创建的资源类型: {created_resource.resource_type}")
        print(f"创建的资源用户ID: {created_resource.user_id}")
        print(f"创建的资源组织ID: {created_resource.organization_id}")

        return True

    except Exception as e:
        print(f"ERROR 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_resource_memory()
    sys.exit(0 if success else 1)