#!/usr/bin/env python3
"""
MIRIX 数据库初始化脚本

此脚本用于初始化 MIRIX 数据库，创建所有必要的表结构和初始数据。

使用方法:
    python database/init_db.py

环境变量:
    MIRIX_PG_URI: PostgreSQL 连接字符串
    或
    DATABASE_URL: PostgreSQL 连接字符串（兼容）
"""

import os
import sys
from pathlib import Path
import asyncio
import asyncpg
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DatabaseInitializer:
    """数据库初始化器"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None

    async def connect(self):
        """连接到数据库"""
        try:
            self.conn = await asyncpg.connect(self.database_url)
            print("✓ 成功连接到数据库")
        except Exception as e:
            print(f"✗ 连接数据库失败: {e}")
            raise

    async def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            await self.conn.close()
            print("✓ 数据库连接已关闭")

    async def execute_sql_file(self, file_path: Path):
        """执行 SQL 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # 移除不支持的 \restrict 命令
            sql = '\n'.join([line for line in sql.split('\n')
                           if not line.strip().startswith('\\restrict')])

            await self.conn.execute(sql)
            print(f"✓ 成功执行 SQL 文件: {file_path.name}")
            return True
        except Exception as e:
            print(f"✗ 执行 SQL 文件失败 ({file_path.name}): {e}")
            return False

    async def check_extensions(self):
        """检查必需的扩展"""
        print("\n检查数据库扩展...")

        extensions = await self.conn.fetch("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname IN ('uuid-ossp', 'vector')
        """)

        ext_dict = {ext['extname']: ext['extversion'] for ext in extensions}

        if 'uuid-ossp' in ext_dict:
            print(f"  ✓ uuid-ossp: {ext_dict['uuid-ossp']}")
        else:
            print("  ✗ uuid-ossp 扩展未安装")

        if 'vector' in ext_dict:
            print(f"  ✓ vector (pgvector): {ext_dict['vector']}")
        else:
            print("  ✗ vector 扩展未安装")

        return len(ext_dict) == 2

    async def check_tables(self):
        """检查数据库表"""
        print("\n检查数据库表...")

        tables = await self.conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        table_names = [t['tablename'] for t in tables]

        expected_tables = [
            'users', 'organizations', 'user_settings',
            'agents', 'agents_tags', 'agent_environment_variables',
            'messages', 'steps',
            'episodic_memory', 'semantic_memory', 'procedural_memory',
            'resource_memory', 'knowledge_vault',
            'files', 'cloud_file_mapping',
            'tools', 'tools_agents', 'providers',
            'sandbox_configs', 'sandbox_environment_variables',
            'block', 'blocks_agents'
        ]

        print(f"  找到 {len(table_names)} 个表")

        for table in expected_tables:
            if table in table_names:
                print(f"    ✓ {table}")
            else:
                print(f"    ✗ {table} (缺失)")

        return len(table_names) >= len(expected_tables) * 0.9  # 允许 10% 的差异

    async def get_table_count(self, table_name: str) -> int:
        """获取表中的记录数"""
        try:
            count = await self.conn.fetchval(
                f"SELECT COUNT(*) FROM {table_name} WHERE NOT is_deleted"
            )
            return count
        except:
            return 0

    async def show_statistics(self):
        """显示数据库统计信息"""
        print("\n数据库统计:")

        stats = {
            '用户': await self.get_table_count('users'),
            '组织': await self.get_table_count('organizations'),
            'Agents': await self.get_table_count('agents'),
            '消息': await self.get_table_count('messages'),
            '情景记忆': await self.get_table_count('episodic_memory'),
            '语义记忆': await self.get_table_count('semantic_memory'),
            '程序记忆': await self.get_table_count('procedural_memory'),
            '资源记忆': await self.get_table_count('resource_memory'),
            '知识库': await self.get_table_count('knowledge_vault'),
            '文件': await self.get_table_count('files'),
            '工具': await self.get_table_count('tools'),
        }

        for name, count in stats.items():
            print(f"  {name}: {count} 条记录")

    async def initialize(self, force: bool = False):
        """初始化数据库"""
        print("="*60)
        print("MIRIX 数据库初始化")
        print("="*60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据库: {self.database_url.split('@')[-1]}")
        print("="*60)

        await self.connect()

        # 检查是否已初始化
        try:
            user_count = await self.get_table_count('users')
            if user_count > 0 and not force:
                print("\n⚠️  数据库似乎已经初始化")
                print(f"   找到 {user_count} 个用户")
                response = input("\n是否继续？这将重新创建所有表 (yes/no): ")
                if response.lower() != 'yes':
                    print("已取消初始化")
                    await self.disconnect()
                    return False
        except:
            pass  # 表不存在，继续初始化

        # 执行初始化 SQL
        print("\n执行数据库初始化脚本...")
        sql_file = project_root / 'database' / 'init_complete.sql'

        if not sql_file.exists():
            print(f"✗ SQL 文件不存在: {sql_file}")
            await self.disconnect()
            return False

        success = await self.execute_sql_file(sql_file)

        if not success:
            print("\n✗ 数据库初始化失败")
            await self.disconnect()
            return False

        # 验证初始化结果
        print("\n验证初始化结果...")

        extensions_ok = await self.check_extensions()
        tables_ok = await self.check_tables()

        if extensions_ok and tables_ok:
            print("\n" + "="*60)
            print("✓ 数据库初始化成功！")
            print("="*60)

            await self.show_statistics()

            print("\n默认账户:")
            print("  用户 ID: user-00000000-0000-4000-8000-000000000000")
            print("  组织 ID: org-00000000-0000-4000-8000-000000000000")

            await self.disconnect()
            return True
        else:
            print("\n✗ 数据库初始化验证失败")
            await self.disconnect()
            return False


async def main():
    """主函数"""
    # 获取数据库连接字符串
    database_url = os.getenv('MIRIX_PG_URI') or os.getenv('DATABASE_URL')

    if not database_url:
        print("错误: 未设置数据库连接字符串")
        print("请设置环境变量: MIRIX_PG_URI 或 DATABASE_URL")
        print("\n示例:")
        print("  export MIRIX_PG_URI='postgresql://mirix:password@localhost:5432/mirix'")
        sys.exit(1)

    # 检查命令行参数
    force = '--force' in sys.argv or '-f' in sys.argv

    # 初始化数据库
    initializer = DatabaseInitializer(database_url)

    try:
        success = await initializer.initialize(force=force)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消初始化")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 初始化过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
