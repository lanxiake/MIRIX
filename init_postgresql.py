#!/usr/bin/env python3
"""
PostgreSQL 数据库初始化脚本
使用 SQLAlchemy ORM 模型自动创建数据库表结构
"""

import sys
import os
sys.path.append('.')

from mirix.orm.sqlalchemy_base import SqlalchemyBase
from sqlalchemy import create_engine, text
from mirix.settings import settings
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_postgresql():
    """初始化 PostgreSQL 数据库表结构"""
    try:
        # 使用配置中的数据库 URI
        db_url = settings.mirix_pg_uri or "postgresql://mirix:mirix123@localhost:5432/mirix"
        logger.info(f"正在连接 PostgreSQL 数据库: {db_url}")

        # 创建 PostgreSQL 引擎
        engine = create_engine(db_url, echo=True)

        # 测试连接
        with engine.connect() as conn:
            logger.info("数据库连接成功")

            # 创建必要的扩展
            logger.info("创建必要的 PostgreSQL 扩展...")
            try:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                conn.commit()
                logger.info("uuid-ossp 扩展创建成功")
            except Exception as e:
                logger.warning(f"创建 uuid-ossp 扩展失败 (可能已存在): {e}")

            try:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
                conn.commit()
                logger.info("vector 扩展创建成功")
            except Exception as e:
                logger.warning(f"创建 vector 扩展失败 (可能已存在): {e}")

        # 导入所有 ORM 模型以确保它们被注册
        logger.info("导入所有 ORM 模型...")
        from mirix.orm import (
            organization, user, agent, message, step,
            episodic_memory, semantic_memory, procedural_memory,
            resource_memory, knowledge_vault, file, cloud_file_mapping,
            tool, provider, sandbox_config, block
        )

        # 创建所有表
        logger.info('开始创建数据库表...')
        SqlalchemyBase.metadata.create_all(bind=engine)
        logger.info('数据库表创建完成!')

        # 验证表是否创建成功
        logger.info("验证表创建结果...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            logger.info(f'创建的表: {tables}')

            # 检查关键表是否存在
            required_tables = ['organizations', 'users', 'agents', 'messages', 'episodic_memory', 'semantic_memory']
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                logger.warning(f"缺少关键表: {missing_tables}")
                return False
            else:
                logger.info("所有关键表都已创建成功!")

                # 插入默认数据
                logger.info("插入默认数据...")
                try:
                    # 插入默认组织
                    conn.execute(text("""
                        INSERT INTO organizations (id, name, created_at, updated_at, is_deleted)
                        VALUES ('org-00000000-0000-4000-8000-000000000000', 'Default Organization', now(), now(), false)
                        ON CONFLICT (id) DO NOTHING
                    """))

                    # 插入默认用户
                    conn.execute(text("""
                        INSERT INTO users (id, name, status, timezone, organization_id, created_at, updated_at, is_deleted)
                        VALUES ('user-00000000-0000-4000-8000-000000000000', 'Default User', 'active', 'UTC',
                                'org-00000000-0000-4000-8000-000000000000', now(), now(), false)
                        ON CONFLICT (id) DO NOTHING
                    """))

                    conn.commit()
                    logger.info("默认数据插入成功!")
                except Exception as e:
                    logger.error(f"插入默认数据失败: {e}")
                    conn.rollback()

        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_postgresql()
    if success:
        logger.info("PostgreSQL 数据库初始化成功!")
        sys.exit(0)
    else:
        logger.error("PostgreSQL 数据库初始化失败!")
        sys.exit(1)