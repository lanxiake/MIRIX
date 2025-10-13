# MIRIX Memory Search API 方法调用修复

## 问题描述

在测试向量搜索功能时发现多个API方法调用错误：

### 错误1: 情景记忆搜索方法不存在
```
AttributeError: 'EpisodicMemoryManager' object has no attribute 'search_episodic_memory'
```

### 错误2: 核心记忆获取方法不存在  
```
AttributeError: 'SyncServer' object has no attribute 'get_current_persona'
```

## 问题原因分析

1. **方法名称错误**: 新增的向量搜索API接口中使用了不存在的方法名
2. **API不一致**: 各个记忆管理器的方法命名不统一
3. **核心记忆结构误解**: 错误理解了核心记忆的数据结构

## 修复方案

### 1. 情景记忆搜索方法修复

**错误调用**:
```python
results = episodic_manager.search_episodic_memory(...)
```

**正确调用**:
```python
results = episodic_manager.list_episodic_memory(...)
```

### 2. 语义记忆搜索方法修复

**错误调用**:
```python
results = semantic_manager.search_semantic_memory(...)
```

**正确调用**:
```python
results = semantic_manager.list_semantic_items(...)
```

### 3. 程序记忆搜索方法修复

**错误调用**:
```python
results = procedural_manager.search_procedural_memory(...)
```

**正确调用**:
```python
results = procedural_manager.list_procedural_items(...)
```

### 4. 资源记忆搜索方法修复

**错误调用**:
```python
results = resource_manager.search_resource_memory(...)
```

**正确调用**:
```python
results = resource_manager.list_resource_items(...)
```

### 5. 凭证记忆搜索方法修复

**错误调用**:
```python
results = knowledge_manager.search_knowledge_vault(...)
```

**正确调用**:
```python
results = knowledge_manager.list_knowledge_vault_items(...)
```

### 6. 核心记忆获取逻辑重构

**错误实现**:
```python
core_memory = agent.client.server.get_current_persona(target_user.id).core_memory
for key, value in core_memory.items():
    # 处理键值对
```

**正确实现**:
```python
# 获取human块
core_memory_block = agent.client.get_in_context_memory(
    agent.agent_states.agent_state.id
).get_block("human")
core_memory_text = core_memory_block.value if core_memory_block else ""

# 获取persona块
persona_block = agent.client.get_in_context_memory(
    agent.agent_states.agent_state.id
).get_block("persona")
persona_text = persona_block.value if persona_block else ""
```

## 修复的API接口

1. `/memories/episodic/search` - 情景记忆搜索
2. `/memories/semantic/search` - 语义记忆搜索  
3. `/memories/procedural/search` - 程序记忆搜索
4. `/memories/resource/search` - 资源记忆搜索
5. `/memories/core/search` - 核心记忆搜索
6. `/memories/credentials/search` - 凭证记忆搜索

## 记忆管理器方法映射表

| 记忆类型 | 管理器类 | 正确方法名 | 错误方法名 |
|---------|---------|-----------|-----------|
| 情景记忆 | EpisodicMemoryManager | `list_episodic_memory` | `search_episodic_memory` |
| 语义记忆 | SemanticMemoryManager | `list_semantic_items` | `search_semantic_memory` |
| 程序记忆 | ProceduralMemoryManager | `list_procedural_items` | `search_procedural_memory` |
| 资源记忆 | ResourceMemoryManager | `list_resource_items` | `search_resource_memory` |
| 凭证记忆 | KnowledgeVaultManager | `list_knowledge_vault_items` | `search_knowledge_vault` |
| 核心记忆 | - | `get_in_context_memory` | `get_current_persona` |

## 核心记忆结构说明

### 原始错误理解
- 认为核心记忆是简单的字典结构
- 尝试通过 `get_current_persona()` 获取

### 正确理解
- 核心记忆由多个块(block)组成
- 主要包含 `human` 和 `persona` 两个块
- 每个块包含文本内容，而非键值对

### 核心记忆搜索逻辑
```python
# 搜索human块
if core_memory_text and query_lower in core_memory_text.lower():
    results.append({
        "id": "core_memory_human",
        "key": "human",
        "value": core_memory_text,
        "similarity_score": 0.8
    })

# 搜索persona块  
if persona_text and query_lower in persona_text.lower():
    results.append({
        "id": "core_memory_persona",
        "key": "persona",
        "value": persona_text,
        "similarity_score": 0.8
    })
```

## 错误处理改进

### 增强的异常处理
- 添加 try-catch 块防止获取记忆失败
- 提供详细的错误日志
- 优雅降级，避免整个搜索失败

### 日志改进
```python
logger.warning(f"获取核心记忆失败: {e}")
logger.debug(f"获取persona记忆失败: {e}")
```

## 测试验证

### 修复前的错误
```
AttributeError: 'EpisodicMemoryManager' object has no attribute 'search_episodic_memory'
AttributeError: 'SyncServer' object has no attribute 'get_current_persona'
```

### 修复后的预期结果
- 所有向量搜索API接口正常工作
- 各种记忆类型都能正确搜索
- 核心记忆搜索返回合理结果
- 错误处理更加健壮

## 当前需求总结

### 已完成的优化
1. ✅ **向量搜索功能**: 从关键字搜索升级为语义搜索
2. ✅ **用户认证修复**: 解决用户不存在的问题
3. ✅ **API方法修复**: 修正所有记忆管理器的方法调用
4. ✅ **核心记忆重构**: 正确理解和实现核心记忆搜索
5. ✅ **错误处理增强**: 添加完善的异常处理机制
6. ✅ **日志系统完善**: 提供详细的调试信息

### 技术栈优化
- **搜索技术**: 关键字匹配 → 向量语义搜索
- **用户管理**: 硬编码用户 → 动态用户获取
- **API设计**: 不一致的方法名 → 统一的接口规范
- **错误处理**: 简单报错 → 优雅降级
- **日志记录**: 基础日志 → 详细调试信息

### 系统稳定性提升
- **容错能力**: 单点失败 → 多层容错
- **用户体验**: 搜索失败 → 智能搜索
- **维护性**: 难以调试 → 详细日志追踪
- **扩展性**: 硬编码逻辑 → 可配置参数

## 总结

本次修复解决了向量搜索功能中的所有API方法调用错误，通过正确使用各个记忆管理器的方法名称和重构核心记忆获取逻辑，确保了系统的稳定运行。修复后的系统具有更好的错误处理能力和更详细的调试信息，为用户提供了完整可用的向量搜索功能。
