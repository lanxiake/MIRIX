#!/usr/bin/env python3
"""
调试用户和组织ID的脚本
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from mirix.services.user_manager import UserManager
from mirix.services.organization_manager import OrganizationManager

def debug_user_organization():
    """调试用户和组织ID"""
    print("开始调试用户和组织ID...")

    try:
        # 初始化管理器
        user_manager = UserManager()
        org_manager = OrganizationManager()
        
        print("OK 管理器初始化成功")

        # 获取默认用户
        default_user = user_manager.get_default_user()
        print(f"默认用户ID: {default_user.id}")
        print(f"默认用户名称: {default_user.name}")
        print(f"默认用户组织ID: {default_user.organization_id}")
        print(f"默认用户状态: {default_user.status}")
        
        # 获取默认组织
        try:
            default_org = org_manager.get_default_organization()
            print(f"默认组织ID: {default_org.id}")
            print(f"默认组织名称: {default_org.name}")
        except Exception as e:
            print(f"ERROR 获取默认组织失败: {e}")
            
        # 检查用户的组织ID是否存在
        if default_user.organization_id:
            try:
                user_org = org_manager.get_organization_by_id(default_user.organization_id)
                print(f"用户所属组织: {user_org.name} (ID: {user_org.id})")
            except Exception as e:
                print(f"ERROR 用户的组织ID无效: {e}")
        else:
            print("ERROR 用户没有组织ID")

        return True

    except Exception as e:
        print(f"ERROR 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_user_organization()
    sys.exit(0 if success else 1)