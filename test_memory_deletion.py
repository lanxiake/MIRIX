#!/usr/bin/env python3
"""
测试记忆删除功能的脚本

这个脚本会:
1. 列出所有类型的记忆
2. 创建一个测试记忆
3. 删除该记忆
4. 验证记忆已被删除
"""

import requests
import json
import sys
from datetime import datetime

SERVER_URL = "http://10.157.152.40:47283"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_episodic_memory_deletion():
    """测试情景记忆删除"""
    print_section("测试情景记忆删除")

    # 1. 获取现有的情景记忆
    print("1. 获取现有的情景记忆...")
    response = requests.get(f"{SERVER_URL}/memory/episodic")
    if response.status_code == 200:
        memories = response.json()
        print(f"   找到 {len(memories)} 条情景记忆")
        if memories:
            print(f"   第一条记忆: {memories[0].get('summary', 'N/A')[:50]}...")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False

    # 2. 如果有记忆,选择第一条进行删除测试
    if memories:
        test_memory_id = memories[0].get('id')
        test_memory_summary = memories[0].get('summary', 'N/A')

        print(f"\n2. 准备删除测试记忆...")
        print(f"   ID: {test_memory_id}")
        print(f"   摘要: {test_memory_summary[:50]}...")

        # 3. 删除记忆
        print(f"\n3. 删除记忆 (ID: {test_memory_id})...")
        delete_response = requests.delete(f"{SERVER_URL}/memory/episodic/{test_memory_id}")

        if delete_response.status_code == 200:
            result = delete_response.json()
            print(f"   ✅ 删除请求成功: {result.get('message', 'N/A')}")
            print(f"   删除数量: {result.get('deleted_count', 0)}")
        else:
            print(f"   ❌ 删除失败: {delete_response.status_code}")
            print(f"   错误信息: {delete_response.text}")
            return False

        # 4. 验证删除
        print(f"\n4. 验证记忆已被删除...")
        verify_response = requests.get(f"{SERVER_URL}/memory/episodic")
        if verify_response.status_code == 200:
            updated_memories = verify_response.json()
            deleted = not any(m.get('id') == test_memory_id for m in updated_memories)

            if deleted:
                print(f"   ✅ 验证成功: 记忆已从数据库中删除")
                print(f"   当前记忆数量: {len(updated_memories)} (原来: {len(memories)})")
            else:
                print(f"   ❌ 验证失败: 记忆仍然存在于数据库中!")
                return False
        else:
            print(f"   ❌ 验证失败: 无法获取记忆列表")
            return False
    else:
        print("   ⚠️  没有找到可供测试的记忆")

    return True

def test_semantic_memory_deletion():
    """测试语义记忆删除"""
    print_section("测试语义记忆删除")

    # 1. 获取现有的语义记忆
    print("1. 获取现有的语义记忆...")
    response = requests.get(f"{SERVER_URL}/memory/semantic")
    if response.status_code == 200:
        memories = response.json()
        print(f"   找到 {len(memories)} 条语义记忆")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False

    # 2. 如果有记忆,选择第一条进行删除测试
    if memories:
        test_memory_id = memories[0].get('id')
        test_memory_name = memories[0].get('name') or memories[0].get('title', 'N/A')

        print(f"\n2. 准备删除测试记忆...")
        print(f"   ID: {test_memory_id}")
        print(f"   名称: {test_memory_name[:50]}...")

        # 3. 删除记忆
        print(f"\n3. 删除记忆 (ID: {test_memory_id})...")
        delete_response = requests.delete(f"{SERVER_URL}/memory/semantic/{test_memory_id}")

        if delete_response.status_code == 200:
            result = delete_response.json()
            print(f"   ✅ 删除请求成功: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ 删除失败: {delete_response.status_code}")
            return False

        # 4. 验证删除
        print(f"\n4. 验证记忆已被删除...")
        verify_response = requests.get(f"{SERVER_URL}/memory/semantic")
        if verify_response.status_code == 200:
            updated_memories = verify_response.json()
            deleted = not any(m.get('id') == test_memory_id for m in updated_memories)

            if deleted:
                print(f"   ✅ 验证成功: 记忆已从数据库中删除")
            else:
                print(f"   ❌ 验证失败: 记忆仍然存在于数据库中!")
                return False
        else:
            print(f"   ❌ 验证失败: 无法获取记忆列表")
            return False
    else:
        print("   ⚠️  没有找到可供测试的记忆")

    return True

def check_core_memory():
    """检查核心记忆"""
    print_section("检查核心记忆")

    print("获取核心记忆...")
    response = requests.get(f"{SERVER_URL}/memory/core")
    if response.status_code == 200:
        memories = response.json()
        print(f"   找到 {len(memories)} 个核心记忆块")
        for mem in memories:
            aspect = mem.get('aspect') or mem.get('category', 'N/A')
            content = mem.get('understanding') or mem.get('content', '')
            print(f"\n   块: {aspect}")
            print(f"   内容: {content[:100]}...")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")

def main():
    print_section("MIRIX 记忆删除功能测试")
    print(f"服务器地址: {SERVER_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试情景记忆删除
        episodic_result = test_episodic_memory_deletion()

        # 测试语义记忆删除
        semantic_result = test_semantic_memory_deletion()

        # 检查核心记忆
        check_core_memory()

        # 总结
        print_section("测试总结")
        print(f"情景记忆删除: {'✅ 通过' if episodic_result else '❌ 失败'}")
        print(f"语义记忆删除: {'✅ 通过' if semantic_result else '❌ 失败'}")

        if episodic_result and semantic_result:
            print("\n🎉 所有测试通过! 删除功能正常工作。")
            print("\n💡 如果 agent 对话时仍能查询到已删除的信息,请检查:")
            print("   1. 核心记忆 (Core Memory) 中是否有该信息的副本")
            print("   2. 对话历史中是否提到过该信息")
            print("   3. 其他类型记忆 (如 semantic/procedural) 中是否也存储了该信息")
            return 0
        else:
            print("\n❌ 部分测试失败,请查看上面的详细信息。")
            return 1

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
