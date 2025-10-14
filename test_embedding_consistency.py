#!/usr/bin/env python3
"""
Embedding配置一致性测试脚本

此脚本用于验证MIRIX系统中所有memory agent的embedding配置是否一致。
"""

import sys
sys.path.insert(0, '/opt/MIRIX')

from mirix.agent.agent_wrapper import AgentWrapper


def test_embedding_consistency():
    """测试所有memory agent的embedding配置一致性"""

    print("=" * 60)
    print("MIRIX Embedding配置一致性测试")
    print("=" * 60)

    try:
        # 初始化agent
        print("\n正在初始化AgentWrapper...")
        agent = AgentWrapper('mirix/configs/mirix_monitor.yaml')
        print("✅ AgentWrapper初始化成功")

        # 获取所有memory agent的embedding配置
        agent_states = agent.agent_states

        configs = []
        agent_names = [
            'episodic_memory_agent_state',
            'semantic_memory_agent_state',
            'procedural_memory_agent_state',
            'resource_memory_agent_state',
            'knowledge_vault_agent_state'
        ]

        print("\n检查各个memory agent的embedding配置:")
        print("-" * 60)

        for attr_name in agent_names:
            agent_state = getattr(agent_states, attr_name, None)
            if agent_state:
                config = agent_state.embedding_config
                config_info = {
                    'agent': attr_name,
                    'model': config.embedding_model,
                    'dimension': config.embedding_dim,
                    'endpoint_type': config.embedding_endpoint_type,
                    'endpoint': config.embedding_endpoint,
                    'chunk_size': config.embedding_chunk_size
                }
                configs.append(config_info)

                print(f"\n📊 {attr_name}:")
                print(f"   模型: {config.embedding_model}")
                print(f"   维度: {config.embedding_dim}")
                print(f"   端点类型: {config.embedding_endpoint_type}")
                print(f"   端点: {config.embedding_endpoint}")
                print(f"   分块大小: {config.embedding_chunk_size}")
            else:
                print(f"\n⚠️  {attr_name}: 未找到agent state")

        # 检查一致性
        print("\n" + "=" * 60)
        print("一致性检查结果:")
        print("=" * 60)

        if not configs:
            print("❌ 错误: 未找到任何memory agent配置")
            return False

        # 检查维度一致性
        first_dim = configs[0]['dimension']
        first_model = configs[0]['model']
        first_endpoint_type = configs[0]['endpoint_type']

        dimension_mismatch = []
        model_mismatch = []
        endpoint_type_mismatch = []

        for c in configs:
            if c['dimension'] != first_dim:
                dimension_mismatch.append(c)
            if c['model'] != first_model:
                model_mismatch.append(c)
            if c['endpoint_type'] != first_endpoint_type:
                endpoint_type_mismatch.append(c)

        # 报告结果
        all_consistent = (
            not dimension_mismatch and
            not model_mismatch and
            not endpoint_type_mismatch
        )

        if all_consistent:
            print(f"\n✅ 所有agents使用一致的embedding配置:")
            print(f"   - 模型: {first_model}")
            print(f"   - 维度: {first_dim}")
            print(f"   - 端点类型: {first_endpoint_type}")
            print(f"   - 总共检查了 {len(configs)} 个memory agents")
        else:
            print(f"\n❌ 发现配置不一致!")

            if dimension_mismatch:
                print(f"\n维度不一致:")
                print(f"  基准: {first_dim}维 (来自 {configs[0]['agent']})")
                for c in dimension_mismatch:
                    print(f"  ⚠️  {c['agent']}: {c['dimension']}维")

            if model_mismatch:
                print(f"\n模型不一致:")
                print(f"  基准: {first_model} (来自 {configs[0]['agent']})")
                for c in model_mismatch:
                    print(f"  ⚠️  {c['agent']}: {c['model']}")

            if endpoint_type_mismatch:
                print(f"\n端点类型不一致:")
                print(f"  基准: {first_endpoint_type} (来自 {configs[0]['agent']})")
                for c in endpoint_type_mismatch:
                    print(f"  ⚠️  {c['agent']}: {c['endpoint_type']}")

        # 给出建议
        print("\n" + "=" * 60)
        print("建议:")
        print("=" * 60)

        if all_consistent:
            print("\n✅ 系统配置正常,所有memory agents使用一致的embedding配置。")
            print("   如果遇到embedding相关错误,可能是数据库中存在旧的embeddings。")
            print("   请运行以下命令检查数据库中的embedding维度:")
            print("\n   docker-compose exec mirix-backend python check_database_embeddings.py")
        else:
            print("\n⚠️  发现配置不一致,这可能导致embedding维度不匹配错误。")
            print("   建议采取以下行动:")
            print("\n   1. 检查 mirix/agent/agent_wrapper.py 中的默认embedding配置")
            print("   2. 确保所有agents在创建时使用相同的embedding配置")
            print("   3. 如果需要更改配置,请重新生成数据库中的所有embeddings")
            print("\n   详细解决方案请参考: EMBEDDING_DIMENSION_SOLUTION.md")

        print("\n" + "=" * 60)

        return all_consistent

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_embedding_consistency()
    sys.exit(0 if success else 1)
