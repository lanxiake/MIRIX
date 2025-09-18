#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建 SQLite 数据库表结构
"""

import sys
import os
sys.path.append('.')

from mirix.orm.sqlalchemy_base import SqlalchemyBase
from sqlalchemy import create_engine
import sqlite3

def init_database():
    """初始化数据库表结构"""
    try:
        # 创建 SQLite 引擎
        print("正在创建 SQLite 引擎...")
        engine = create_engine('sqlite:///mirix.db', echo=True)
        
        # 创建所有表
        print('开始创建数据库表...')
        SqlalchemyBase.metadata.create_all(bind=engine)
        print('数据库表创建完成!')
        
        # 验证表是否创建成功
        print("验证表创建结果...")
        conn = sqlite3.connect('mirix.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f'创建的表: {table_names}')
        
        # 检查关键表是否存在
        required_tables = ['organizations', 'users', 'resource_memory']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"警告: 缺少关键表: {missing_tables}")
        else:
            print("所有关键表都已创建成功!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("数据库初始化成功!")
        sys.exit(0)
    else:
        print("数据库初始化失败!")
        sys.exit(1)