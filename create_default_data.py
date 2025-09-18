#!/usr/bin/env python3
"""
创建默认数据脚本
用于插入默认的组织和用户数据
"""

import sys
import os
sys.path.append('.')

from mirix.orm.organization import Organization
from mirix.orm.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mirix.utils import generate_unique_short_id
import uuid

def create_default_data():
    """创建默认的组织和用户数据"""
    try:
        # 创建 SQLite 引擎和会话
        engine = create_engine('sqlite:///mirix.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # 检查是否已存在默认组织
            existing_org = session.query(Organization).filter_by(name="Default Organization").first()
            if not existing_org:
                # 创建默认组织
                default_org = Organization(
                    id=str(uuid.uuid4()),
                    name="Default Organization"
                )
                session.add(default_org)
                session.flush()  # 获取 ID
                print(f"创建默认组织: {default_org.name} (ID: {default_org.id})")
            else:
                default_org = existing_org
                print(f"使用现有默认组织: {default_org.name} (ID: {default_org.id})")
            
            # 使用应用程序期望的默认用户ID
            expected_user_id = "user-00000000-0000-4000-8000-000000000000"
            
            # 检查是否已存在具有期望ID的用户
            existing_user = session.query(User).filter_by(id=expected_user_id).first()
            if not existing_user:
                # 删除任何现有的default_user（如果存在）
                old_user = session.query(User).filter_by(name="default_user").first()
                if old_user:
                    print(f"删除旧的默认用户: {old_user.name} (ID: {old_user.id})")
                    session.delete(old_user)
                
                # 创建具有正确ID的默认用户
                default_user = User(
                    id=expected_user_id,
                    name="default_user",
                    status="active",
                    timezone="UTC",
                    organization_id=default_org.id
                )
                session.add(default_user)
                session.flush()  # 获取 ID
                print(f"创建默认用户: {default_user.name} (ID: {default_user.id})")
            else:
                default_user = existing_user
                print(f"使用现有默认用户: {default_user.name} (ID: {default_user.id})")
            
            # 提交事务
            session.commit()
            
            # 验证数据
            org_count = session.query(Organization).count()
            user_count = session.query(User).count()
            
            print(f"数据库中组织数量: {org_count}")
            print(f"数据库中用户数量: {user_count}")
            
            return True
            
    except Exception as e:
        print(f"创建默认数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_default_data()
    if success:
        print("默认数据创建成功!")
        sys.exit(0)
    else:
        print("默认数据创建失败!")
        sys.exit(1)