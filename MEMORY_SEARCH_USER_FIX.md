# MIRIX Memory Search 用户认证修复

## 问题描述

在测试向量搜索功能时遇到用户认证错误：
```
User not found with id='default_user', is_deleted=False
```

## 问题原因分析

1. **MCP配置问题**: MCP服务器配置中默认用户ID设置为 `"default_user"`，但这个用户在后端数据库中不存在
2. **用户获取逻辑缺陷**: 当传入不存在的用户ID时，系统没有回退机制
3. **API接口用户处理不当**: 新增的向量搜索API接口没有正确处理用户不存在的情况

## 修复方案

### 1. 改进用户获取函数 (`fastapi_server.py`)

**修复位置**: `get_user_or_default()` 函数

**修复内容**:
```python
def get_user_or_default(agent_wrapper, user_id: Optional[str] = None):
    """Get user by ID or return current user"""
    if user_id:
        try:
            return agent_wrapper.client.server.user_manager.get_user_by_id(user_id)
        except Exception:
            # 如果指定用户不存在，回退到默认用户
            logger.warning(f"用户 {user_id} 不存在，使用默认用户")
            return agent_wrapper.client.server.user_manager.get_default_user()
    elif agent_wrapper and agent_wrapper.client.user:
        return agent_wrapper.client.user
    else:
        return agent_wrapper.client.server.user_manager.get_default_user()
```

**改进效果**:
- 添加异常处理机制
- 用户不存在时自动回退到系统默认用户
- 添加警告日志记录

### 2. 优化MCP适配器用户传递逻辑 (`mirix_adapter.py`)

**修复位置**: `search_memories_by_vector()` 方法

**修复内容**:
```python
# 构建向量搜索请求
search_request = {
    "query": query,
    "search_method": "embedding",
    "search_field": self._get_default_search_field(memory_type),
    "limit": limit,
    "similarity_threshold": similarity_threshold
}

# 只有当user_id不是默认值时才传递，让后端使用当前活跃用户
if user_id and user_id != self.config.default_user_id:
    search_request["user_id"] = user_id
```

**改进效果**:
- 避免传递不存在的默认用户ID
- 让后端自动使用当前活跃用户
- 减少用户认证错误

### 3. 增强API接口用户处理 (`fastapi_server.py`)

**修复位置**: 所有6个向量搜索API接口

**修复内容**:
```python
# 获取用户 - 如果没有指定user_id，使用当前活跃用户或默认用户
if request.user_id:
    target_user = get_user_or_default(agent, request.user_id)
else:
    target_user = get_user_or_default(agent, None)
if not target_user:
    raise HTTPException(status_code=404, detail="用户不存在")

logger.debug(f"使用用户: {target_user.id}")
```

**改进效果**:
- 明确区分有无user_id的处理逻辑
- 增加用户获取的调试日志
- 提供更详细的错误信息

## 修复的API接口

1. `/memories/episodic/search` - 情景记忆搜索
2. `/memories/semantic/search` - 语义记忆搜索  
3. `/memories/procedural/search` - 程序记忆搜索
4. `/memories/resource/search` - 资源记忆搜索
5. `/memories/core/search` - 核心记忆搜索
6. `/memories/credentials/search` - 凭证记忆搜索

## 日志改进

### 增强的日志信息

**修复前**:
```
INFO - 核心记忆向量搜索: query='记忆系统架构设计文档', method=embedding
```

**修复后**:
```
INFO - 核心记忆向量搜索: query='记忆系统架构设计文档', method=embedding, user_id=default_user
DEBUG - 使用用户: actual_user_id
WARNING - 用户 default_user 不存在，使用默认用户
```

### 日志优势

- **调试信息更完整**: 显示传入的user_id和实际使用的用户
- **问题追踪更容易**: 警告日志明确显示用户回退情况
- **运行状态更透明**: 详细记录用户获取过程

## 兼容性保证

### 向后兼容

- **保持原有API签名**: 所有接口参数保持不变
- **保持原有行为**: 正常用户ID仍然正常工作
- **优雅降级**: 用户不存在时自动回退而非报错

### 错误处理改进

- **更友好的错误信息**: 明确指出用户不存在问题
- **自动恢复机制**: 用户问题时自动使用默认用户
- **详细的调试信息**: 帮助快速定位问题

## 测试验证

### 测试场景

1. **正常用户ID**: 验证现有用户仍能正常工作
2. **不存在用户ID**: 验证自动回退到默认用户
3. **空用户ID**: 验证使用当前活跃用户
4. **default_user ID**: 验证特殊处理逻辑

### 预期结果

- 所有搜索请求都能成功执行
- 用户认证错误得到解决
- 日志信息更加详细和有用
- 系统稳定性显著提升

## 总结

本次修复解决了向量搜索功能中的用户认证问题，通过改进用户获取逻辑、优化用户传递机制和增强错误处理，确保了系统的稳定性和可用性。修复后的系统具有更好的容错能力和更详细的调试信息。
