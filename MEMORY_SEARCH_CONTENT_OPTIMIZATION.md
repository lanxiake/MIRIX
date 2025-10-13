# MIRIX Memory Search 内容返回优化与错误修复

## 问题描述

### 问题1: 向量搜索返回内容不完整
- 搜索结果只返回摘要，而不是完整的文档内容
- 资源记忆搜索应该返回完整文档内容以便用户查看

### 问题2: 记忆管理器方法名错误
```
AttributeError: 'ProceduralMemoryManager' object has no attribute 'list_procedural_items'
AttributeError: 'ResourceMemoryManager' object has no attribute 'list_resource_items'  
AttributeError: 'KnowledgeVaultManager' object has no attribute 'list_knowledge_vault_items'
```

### 问题3: SSL连接错误
```
httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
```

## 修复方案

### 1. 向量搜索内容返回优化

#### 1.1 修改默认搜索字段
**文件**: `/opt/MIRIX/mcp_server/mirix_adapter.py`

**修改前**:
```python
"resource": "summary",      # 资源记忆搜索摘要字段
```

**修改后**:
```python
"resource": "content",      # 资源记忆搜索内容字段（完整文档内容）
```

#### 1.2 API接口返回完整内容
**文件**: `/opt/MIRIX/mirix/server/fastapi_server.py`

**修改前**:
```python
"content": getattr(item, "content", "")[:200] + "...",  # 截取内容预览
```

**修改后**:
```python
"content": getattr(item, "content", ""),  # 返回完整内容
```

#### 1.3 MCP服务器结果格式化优化
**文件**: `/opt/MIRIX/mcp_server/server.py`

**新增逻辑**:
```python
if memory_type == "resource":
    # 资源记忆优先返回完整内容
    content = (
        memory.get("content") or 
        memory.get("summary") or 
        memory.get("title") or
        memory.get("filename", "")
    )
    # 资源记忆返回更多内容（前1000字符）
    content_preview = content[:1000] + ("..." if len(content) > 1000 else "")
else:
    # 其他记忆类型保持200字符限制
    content_preview = content[:200] + ("..." if len(content) > 200 else "")
```

### 2. 记忆管理器方法名修复

#### 2.1 程序记忆管理器
**错误方法**: `list_procedural_items`
**正确方法**: `list_procedures`

#### 2.2 资源记忆管理器  
**错误方法**: `list_resource_items`
**正确方法**: `list_resources`

#### 2.3 知识库管理器
**错误方法**: `list_knowledge_vault_items`
**正确方法**: `list_knowledge`

### 3. SSL连接错误处理

**文件**: `/opt/MIRIX/mirix/server/fastapi_server.py`

**新增重试机制**:
```python
# 执行搜索，添加SSL错误重试
max_retries = 3
for attempt in range(max_retries):
    try:
        results = semantic_manager.list_semantic_items(...)
        break  # 成功则跳出重试循环
    except Exception as e:
        if "SSL" in str(e) and attempt < max_retries - 1:
            logger.warning(f"SSL错误，重试 {attempt + 1}/{max_retries}: {e}")
            import time
            time.sleep(1)  # 等待1秒后重试
            continue
        else:
            raise  # 非SSL错误或已达到最大重试次数，抛出异常
```

## 修复的API接口

1. `/memories/procedural/search` - 程序记忆搜索
2. `/memories/resource/search` - 资源记忆搜索  
3. `/memories/credentials/search` - 凭证记忆搜索
4. `/memories/semantic/search` - 语义记忆搜索（SSL重试）

## 记忆管理器方法映射表（更新版）

| 记忆类型 | 管理器类 | 正确方法名 | 错误方法名 |
|---------|---------|-----------|-----------|
| 情景记忆 | EpisodicMemoryManager | `list_episodic_memory` | `search_episodic_memory` |
| 语义记忆 | SemanticMemoryManager | `list_semantic_items` | `search_semantic_memory` |
| 程序记忆 | ProceduralMemoryManager | `list_procedures` | `list_procedural_items` |
| 资源记忆 | ResourceMemoryManager | `list_resources` | `list_resource_items` |
| 凭证记忆 | KnowledgeVaultManager | `list_knowledge` | `list_knowledge_vault_items` |
| 核心记忆 | - | `get_in_context_memory` | `get_current_persona` |

## 搜索字段优化

### 资源记忆搜索字段变更
- **修改前**: 搜索 `summary` 字段（摘要）
- **修改后**: 搜索 `content` 字段（完整文档内容）

### 搜索效果提升
1. **语义理解更准确**: 直接搜索文档内容而非摘要
2. **搜索结果更全面**: 能找到文档中的具体细节
3. **内容返回更完整**: 用户可以看到完整的文档内容

## 内容返回策略

### 资源记忆（文档）
- **搜索字段**: `content`（完整文档内容）
- **返回内容**: 完整文档内容
- **显示长度**: 前1000字符（MCP接口）/ 完整内容（API接口）

### 其他记忆类型
- **搜索字段**: `details` 或 `summary`
- **返回内容**: 摘要或详情
- **显示长度**: 前200字符

## 错误处理改进

### SSL连接错误
- **重试机制**: 最多重试3次
- **重试间隔**: 1秒
- **错误识别**: 检测SSL相关错误
- **日志记录**: 详细记录重试过程

### 方法调用错误
- **预防措施**: 使用正确的方法名
- **错误恢复**: 完善的异常处理
- **日志追踪**: 详细的错误信息

## 测试验证

### 修复前的问题
1. 搜索结果只显示摘要，无法看到完整文档
2. 多个API接口因方法名错误而失败
3. SSL连接错误导致搜索失败

### 修复后的效果
1. ✅ 资源记忆搜索返回完整文档内容
2. ✅ 所有记忆管理器方法调用正确
3. ✅ SSL错误自动重试，提高成功率
4. ✅ 搜索直接基于文档内容，更准确

## 用户体验提升

### 搜索准确性
- **内容搜索**: 直接搜索文档内容而非摘要
- **语义理解**: 基于完整内容的向量搜索
- **结果相关性**: 更准确的语义匹配

### 内容可用性
- **完整内容**: 返回完整的文档内容
- **即时可用**: 无需额外请求获取完整内容
- **内容丰富**: 1000字符的预览（vs 200字符）

### 系统稳定性
- **自动重试**: SSL错误自动重试
- **错误恢复**: 完善的异常处理
- **日志追踪**: 详细的调试信息

## 总结

本次优化和修复解决了向量搜索功能中的内容返回和方法调用问题：

1. **内容优化**: 资源记忆现在返回完整文档内容，并直接搜索文档内容而非摘要
2. **方法修复**: 修正了所有记忆管理器的方法调用错误
3. **错误处理**: 添加了SSL连接错误的重试机制
4. **用户体验**: 显著提升了搜索准确性和内容可用性

修复后的系统能够提供更准确的语义搜索结果和更完整的文档内容，为用户提供了更好的搜索体验。
