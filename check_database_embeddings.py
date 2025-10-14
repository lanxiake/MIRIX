#!/usr/bin/env python3
"""
数据库Embedding维度检查脚本

此脚本用于检查PostgreSQL数据库中实际存储的embedding向量维度。
可以帮助诊断embedding维度不匹配问题。
"""

import sys
import os

# 添加MIRIX路径
sys.path.insert(0, '/opt/MIRIX')


def check_database_embeddings():
    """检查数据库中各个表的embedding维度"""

    print("=" * 70)
    print("MIRIX 数据库Embedding维度检查")
    print("=" * 70)

    try:
        # 导入必要的模块
        import psycopg2
        import numpy as np

        # 从环境变量获取数据库连接信息,或使用默认值
        db_host = os.getenv('DATABASE_HOST', 'localhost')
        db_port = os.getenv('DATABASE_PORT', '5432')
        db_name = os.getenv('DATABASE_NAME', 'mirix')
        db_user = os.getenv('DATABASE_USER', 'mirix')
        db_password = os.getenv('DATABASE_PASSWORD', 'mirix123')

        print(f"\n连接到数据库: {db_host}:{db_port}/{db_name}")

        # 连接到数据库
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()

        print("✅ 数据库连接成功")

        # 要检查的表和embedding字段
        tables_to_check = [
            {
                'table': 'episodic_memory',
                'embedding_fields': ['details_embedding', 'summary_embedding']
            },
            {
                'table': 'semantic_memory',
                'embedding_fields': ['details_embedding', 'summary_embedding']
            },
            {
                'table': 'procedural_memory',
                'embedding_fields': ['summary_embedding', 'steps_embedding']
            },
            {
                'table': 'resource_memory',
                'embedding_fields': ['summary_embedding', 'content_embedding']
            }
        ]

        print("\n" + "=" * 70)
        print("检查各个表的embedding维度:")
        print("=" * 70)

        all_dimensions = {}
        has_issues = False

        for table_info in tables_to_check:
            table_name = table_info['table']
            embedding_fields = table_info['embedding_fields']

            print(f"\n📊 表: {table_name}")
            print("-" * 70)

            for field in embedding_fields:
                try:
                    # 检查字段是否存在
                    cur.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        AND column_name = '{field}'
                    """)

                    if not cur.fetchone():
                        print(f"   {field}: ⚠️  字段不存在")
                        continue

                    # 获取该字段的记录数
                    cur.execute(f"""
                        SELECT COUNT(*)
                        FROM {table_name}
                        WHERE {field} IS NOT NULL
                    """)
                    record_count = cur.fetchone()[0]

                    if record_count == 0:
                        print(f"   {field}: 📭 无数据")
                        continue

                    print(f"   {field}: 找到 {record_count} 条记录")

                    # 获取前5条记录检查维度
                    cur.execute(f"""
                        SELECT id, {field}
                        FROM {table_name}
                        WHERE {field} IS NOT NULL
                        LIMIT 5
                    """)

                    rows = cur.fetchall()
                    dimensions_found = {}

                    for row_id, embedding_data in rows:
                        if embedding_data:
                            embedding = np.array(embedding_data)
                            total_dims = len(embedding)
                            non_zero_dims = np.count_nonzero(embedding)

                            # 统计维度分布
                            dim_key = f"总维度={total_dims}, 非零维度={non_zero_dims}"
                            if dim_key not in dimensions_found:
                                dimensions_found[dim_key] = []
                            dimensions_found[dim_key].append(row_id)

                            # 记录到全局统计
                            key = f"{table_name}.{field}"
                            if key not in all_dimensions:
                                all_dimensions[key] = set()
                            all_dimensions[key].add(non_zero_dims)

                    # 显示维度统计
                    for dim_key, ids in dimensions_found.items():
                        print(f"      {dim_key}: {len(ids)} 条记录")
                        if len(ids) <= 3:
                            print(f"        IDs: {ids}")

                    # 检查是否有维度不一致
                    unique_non_zero_dims = len(set(
                        int(d.split("非零维度=")[1]) for d in dimensions_found.keys()
                    ))
                    if unique_non_zero_dims > 1:
                        print(f"      ⚠️  警告: 发现不同的非零维度!")
                        has_issues = True

                except Exception as e:
                    print(f"   {field}: ❌ 检查失败 - {e}")

        # 汇总报告
        print("\n" + "=" * 70)
        print("维度汇总报告:")
        print("=" * 70)

        if not all_dimensions:
            print("\n⚠️  数据库中没有找到任何embedding数据")
        else:
            # 按非零维度分组
            dimension_groups = {}
            for field, dims in all_dimensions.items():
                for dim in dims:
                    if dim not in dimension_groups:
                        dimension_groups[dim] = []
                    dimension_groups[dim].append(field)

            print(f"\n发现 {len(dimension_groups)} 种不同的embedding维度:")

            for dim in sorted(dimension_groups.keys()):
                fields = dimension_groups[dim]
                print(f"\n  📏 {dim}维 (非零维度):")
                for field in fields:
                    print(f"     - {field}")

            # 判断是否有问题
            if len(dimension_groups) > 1:
                print("\n❌ 警告: 发现多种不同的embedding维度!")
                print("   这可能导致向量搜索失败。")
                has_issues = True
            else:
                print(f"\n✅ 所有embeddings使用相同的维度: {list(dimension_groups.keys())[0]}维")

        # 给出建议
        print("\n" + "=" * 70)
        print("分析和建议:")
        print("=" * 70)

        if not all_dimensions:
            print("\n📭 数据库中没有embedding数据,这可能是因为:")
            print("   1. 系统刚初始化,还没有创建任何记忆")
            print("   2. Embeddings尚未生成")
            print("\n建议:")
            print("   - 正常使用系统,添加一些记忆后再次运行此检查")

        elif has_issues:
            print("\n⚠️  发现embedding维度不一致!")
            print("\n可能的原因:")
            print("   1. 系统曾使用不同的embedding模型")
            print("   2. 部分数据是从其他系统迁移过来的")
            print("   3. 配置文件在历史上发生过变更")

            print("\n解决方案:")
            print("   选项1: 重新生成所有embeddings(推荐)")
            print("   选项2: 删除旧的embeddings,只保留一致的数据")
            print("   选项3: 分别处理不同维度的数据")

            print("\n详细解决步骤请参考: EMBEDDING_DIMENSION_SOLUTION.md")

        else:
            dim = list(dimension_groups.keys())[0]
            print(f"\n✅ 数据库embedding维度一致: {dim}维")

            # 检查是否与当前配置匹配
            print("\n下一步: 验证数据库维度与系统配置是否匹配")
            print("运行以下命令:")
            print("   python test_embedding_consistency.py")

            # 推断可能使用的模型
            model_mapping = {
                768: "Google AI text-embedding-004",
                1536: "OpenAI text-embedding-3-small",
                3072: "OpenAI text-embedding-3-large",
                1024: "BAAI/bge-large-en-v1.5"
            }

            if dim in model_mapping:
                print(f"\n根据维度 {dim}, 数据可能是使用以下模型创建的:")
                print(f"   {model_mapping[dim]}")

        print("\n" + "=" * 70)

        cur.close()
        conn.close()

        return not has_issues

    except ImportError as e:
        print(f"\n❌ 缺少必要的Python包: {e}")
        print("请安装: pip install psycopg2-binary numpy")
        return False

    except psycopg2.OperationalError as e:
        print(f"\n❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("   1. PostgreSQL服务是否运行")
        print("   2. 数据库连接参数是否正确")
        print("   3. 是否有访问权限")

        print("\n如果使用Docker,请运行:")
        print("   docker-compose ps")
        print("   docker-compose logs postgres")

        return False

    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_database_embeddings()
    sys.exit(0 if success else 1)
