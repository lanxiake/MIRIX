# MIRIX MCP 服务 API 参考文档

## 概述

MIRIX MCP 服务提供了四个核心工具，用于记忆管理和个性化对话。所有工具都遵循 MCP (Model Context Protocol) 标准，支持异步调用和结构化数据交换。

## 通用响应格式

所有 API 调用都返回统一的响应格式：

```json
{
  "success": true,
  "data": {
    // 具体的返回数据
  },
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time": 0.123
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 工具列表

| 工具名称 | 描述 | 主要用途 |
|---------|------|---------|
| `memory_add` | 添加记忆 | 存储用户信息、对话内容、知识点等 |
| `memory_search` | 搜索记忆 | 检索相关记忆内容 |
| `memory_chat` | 记忆对话 | 基于记忆进行个性化对话 |
| `memory_get_profile` | 获取记忆配置文件 | 查看用户记忆统计和配置 |

---

## 1. memory_add - 添加记忆

### 描述
向 MIRIX 记忆系统添加新的记忆内容。支持多种记忆类型，用于构建用户的个性化知识库。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 | 默认值 |
|--------|------|------|------|--------|
| `content` | string | ✅ | 记忆内容，长度 1-10000 字符 | - |
| `memory_type` | string | ✅ | 记忆类型，见下表 | - |
| `context` | string | ❌ | 记忆的上下文信息 | null |

### 记忆类型说明

| 类型 | 英文名 | 描述 | 使用场景 |
|------|--------|------|---------|
| 核心记忆 | `core` | 用户的基本信息和重要特征 | 姓名、职业、兴趣爱好、价值观 |
| 情节记忆 | `episodic` | 具体的事件和经历 | 对话历史、重要事件、经历 |
| 语义记忆 | `semantic` | 概念性知识和事实 | 学习内容、知识点、概念定义 |
| 程序记忆 | `procedural` | 技能和操作步骤 | 工作流程、操作指南、技能 |
| 资源记忆 | `resource` | 外部资源和引用 | 文档链接、工具推荐、资源 |
| 知识库 | `knowledge_vault` | 结构化知识存储 | 专业知识、学习笔记、研究资料 |

### 返回数据

```json
{
  "success": true,
  "data": {
    "memory_id": "mem_1234567890",
    "content": "添加的记忆内容",
    "memory_type": "core",
    "context": "上下文信息",
    "created_at": "2024-01-01T12:00:00Z",
    "user_id": "default_user"
  },
  "message": "记忆添加成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time": 0.156
}
```

### 使用示例

#### 基础用法
```python
# 添加核心记忆
result = await execute_tool('memory_add', {
    'content': '我是一名软件工程师，专注于 AI 和机器学习领域',
    'memory_type': 'core'
})
```

#### 带上下文的记忆
```python
# 添加情节记忆
result = await execute_tool('memory_add', {
    'content': '今天学习了 Transformer 架构的工作原理',
    'memory_type': 'episodic',
    'context': '深度学习课程第5章'
})
```

#### 知识库记忆
```python
# 添加知识库记忆
result = await execute_tool('memory_add', {
    'content': 'Python 装饰器是一种设计模式，用于在不修改函数定义的情况下增加函数功能',
    'memory_type': 'knowledge_vault',
    'context': 'Python 高级编程概念'
})
```

### 错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|---------|
| `INVALID_CONTENT` | 内容为空或超出长度限制 | 检查内容长度（1-10000字符） |
| `INVALID_MEMORY_TYPE` | 无效的记忆类型 | 使用有效的记忆类型 |
| `BACKEND_ERROR` | 后端服务错误 | 检查 MIRIX 后端服务状态 |

---

## 2. memory_search - 搜索记忆

### 描述
在 MIRIX 记忆系统中搜索相关的记忆内容。支持语义搜索和类型过滤。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 | 默认值 |
|--------|------|------|------|--------|
| `query` | string | ✅ | 搜索查询，长度 1-1000 字符 | - |
| `memory_types` | array | ❌ | 要搜索的记忆类型列表 | 所有类型 |
| `limit` | integer | ❌ | 返回结果数量限制 | 10 |

### 返回数据

```json
{
  "success": true,
  "data": {
    "query": "搜索查询",
    "results": [
      {
        "memory_id": "mem_1234567890",
        "content": "匹配的记忆内容",
        "memory_type": "core",
        "context": "上下文信息",
        "relevance_score": 0.95,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total_results": 5,
    "search_time": 0.089
  },
  "message": "搜索完成",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time": 0.123
}
```

### 使用示例

#### 基础搜索
```python
# 搜索所有相关记忆
result = await execute_tool('memory_search', {
    'query': 'Python 编程'
})
```

#### 类型过滤搜索
```python
# 只搜索核心记忆和知识库
result = await execute_tool('memory_search', {
    'query': '机器学习',
    'memory_types': ['core', 'knowledge_vault']
})
```

#### 限制结果数量
```python
# 只返回前3个最相关的结果
result = await execute_tool('memory_search', {
    'query': '工作经验',
    'limit': 3
})
```

### 搜索技巧

1. **使用关键词**: 使用具体的关键词获得更精确的结果
2. **组合搜索**: 使用多个相关词语提高搜索准确性
3. **类型过滤**: 根据需要限制搜索的记忆类型
4. **相关性评分**: 结果按相关性评分排序，评分越高越相关

### 错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|---------|
| `INVALID_QUERY` | 查询为空或超出长度限制 | 检查查询长度（1-1000字符） |
| `INVALID_MEMORY_TYPES` | 无效的记忆类型 | 使用有效的记忆类型 |
| `INVALID_LIMIT` | 无效的限制数量 | 使用 1-100 之间的数字 |

---

## 3. memory_chat - 记忆对话

### 描述
基于用户记忆进行个性化对话。AI 会根据用户的记忆内容提供更加个性化和相关的回复。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 | 默认值 |
|--------|------|------|------|--------|
| `message` | string | ✅ | 用户消息，长度 1-5000 字符 | - |
| `memorizing` | boolean | ❌ | 是否将对话存储为记忆 | true |
| `image_uris` | array | ❌ | 图片 URI 列表（多模态对话） | [] |

### 返回数据

```json
{
  "success": true,
  "data": {
    "response": "AI 的个性化回复",
    "conversation_id": "conv_1234567890",
    "message_id": "msg_1234567890",
    "used_memories": [
      {
        "memory_id": "mem_1234567890",
        "content": "相关记忆内容",
        "relevance_score": 0.89
      }
    ],
    "memorized": true,
    "response_time": 1.234
  },
  "message": "对话完成",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time": 1.456
}
```

### 使用示例

#### 基础对话
```python
# 基础个性化对话
result = await execute_tool('memory_chat', {
    'message': '我想学习一些新的编程技术，有什么建议吗？'
})
```

#### 非记忆对话
```python
# 不存储对话记忆的临时对话
result = await execute_tool('memory_chat', {
    'message': '今天天气怎么样？',
    'memorizing': false
})
```

#### 多模态对话
```python
# 包含图片的对话
result = await execute_tool('memory_chat', {
    'message': '这张图片展示了什么内容？',
    'image_uris': ['data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...']
})
```

### 对话特性

1. **个性化回复**: 基于用户记忆提供定制化回复
2. **上下文感知**: 理解对话上下文和历史
3. **记忆整合**: 自动关联相关记忆内容
4. **多模态支持**: 支持文本和图片输入
5. **对话记录**: 可选择是否存储对话为记忆

### 错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|---------|
| `INVALID_MESSAGE` | 消息为空或超出长度限制 | 检查消息长度（1-5000字符） |
| `INVALID_IMAGE_URI` | 无效的图片 URI | 检查图片格式和编码 |
| `CHAT_SERVICE_ERROR` | 对话服务错误 | 检查 AI 服务状态 |

---

## 4. memory_get_profile - 获取记忆配置文件

### 描述
获取用户的记忆统计信息和配置文件，包括各类型记忆的数量、最近活动等。

### 输入参数

| 参数名 | 类型 | 必需 | 描述 | 默认值 |
|--------|------|------|------|--------|
| `memory_types` | array | ❌ | 要查询的记忆类型列表 | 所有类型 |

### 返回数据

```json
{
  "success": true,
  "data": {
    "user_id": "default_user",
    "profile": {
      "total_memories": 156,
      "memory_types": {
        "core": {
          "count": 12,
          "last_updated": "2024-01-01T10:30:00Z"
        },
        "episodic": {
          "count": 45,
          "last_updated": "2024-01-01T11:45:00Z"
        },
        "semantic": {
          "count": 38,
          "last_updated": "2024-01-01T09:15:00Z"
        },
        "procedural": {
          "count": 23,
          "last_updated": "2024-01-01T08:20:00Z"
        },
        "resource": {
          "count": 19,
          "last_updated": "2024-01-01T12:00:00Z"
        },
        "knowledge_vault": {
          "count": 19,
          "last_updated": "2024-01-01T11:30:00Z"
        }
      },
      "recent_activity": [
        {
          "action": "add",
          "memory_type": "core",
          "timestamp": "2024-01-01T12:00:00Z"
        }
      ],
      "created_at": "2023-12-01T00:00:00Z",
      "last_activity": "2024-01-01T12:00:00Z"
    }
  },
  "message": "配置文件获取成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time": 0.089
}
```

### 使用示例

#### 获取完整配置文件
```python
# 获取所有记忆类型的统计信息
result = await execute_tool('memory_get_profile', {})
```

#### 获取特定类型统计
```python
# 只获取核心记忆和知识库的统计
result = await execute_tool('memory_get_profile', {
    'memory_types': ['core', 'knowledge_vault']
})
```

### 配置文件信息说明

1. **总体统计**: 记忆总数、用户创建时间、最后活动时间
2. **类型统计**: 每种记忆类型的数量和最后更新时间
3. **活动历史**: 最近的记忆操作记录
4. **使用模式**: 用户的记忆使用习惯分析

### 错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|---------|
| `INVALID_MEMORY_TYPES` | 无效的记忆类型 | 使用有效的记忆类型 |
| `PROFILE_NOT_FOUND` | 用户配置文件不存在 | 检查用户ID或创建新配置文件 |

---

## 高级用法

### 1. 批量操作

#### 批量添加记忆
```python
memories = [
    {'content': '记忆1', 'memory_type': 'core'},
    {'content': '记忆2', 'memory_type': 'episodic'},
    {'content': '记忆3', 'memory_type': 'semantic'}
]

for memory in memories:
    result = await execute_tool('memory_add', memory)
    print(f"添加记忆: {result['success']}")
```

### 2. 记忆管理工作流

#### 智能记忆分类
```python
async def smart_memory_add(content, context=None):
    """智能记忆添加，自动判断记忆类型"""
    
    # 基于内容特征判断记忆类型
    if any(keyword in content.lower() for keyword in ['我是', '我的', '我叫']):
        memory_type = 'core'
    elif any(keyword in content.lower() for keyword in ['今天', '昨天', '刚才']):
        memory_type = 'episodic'
    elif any(keyword in content.lower() for keyword in ['定义', '概念', '原理']):
        memory_type = 'semantic'
    elif any(keyword in content.lower() for keyword in ['步骤', '方法', '如何']):
        memory_type = 'procedural'
    elif any(keyword in content.lower() for keyword in ['链接', '文档', '资源']):
        memory_type = 'resource'
    else:
        memory_type = 'knowledge_vault'
    
    return await execute_tool('memory_add', {
        'content': content,
        'memory_type': memory_type,
        'context': context
    })
```

#### 记忆搜索和对话结合
```python
async def enhanced_chat(message):
    """增强对话：先搜索相关记忆，再进行对话"""
    
    # 搜索相关记忆
    search_result = await execute_tool('memory_search', {
        'query': message,
        'limit': 5
    })
    
    # 基于搜索结果进行对话
    chat_result = await execute_tool('memory_chat', {
        'message': message
    })
    
    return {
        'related_memories': search_result['data']['results'],
        'chat_response': chat_result['data']['response']
    }
```

### 3. 错误处理和重试

```python
import asyncio
from typing import Dict, Any

async def robust_tool_call(tool_name: str, params: Dict[str, Any], max_retries: int = 3):
    """带重试机制的工具调用"""
    
    for attempt in range(max_retries):
        try:
            result = await execute_tool(tool_name, params)
            if result['success']:
                return result
            else:
                print(f"工具调用失败 (尝试 {attempt + 1}): {result.get('error', {}).get('message')}")
        except Exception as e:
            print(f"工具调用异常 (尝试 {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # 指数退避
    
    raise Exception(f"工具 {tool_name} 调用失败，已重试 {max_retries} 次")
```

### 4. 性能优化

#### 并发调用
```python
import asyncio

async def concurrent_memory_operations():
    """并发执行多个记忆操作"""
    
    tasks = [
        execute_tool('memory_add', {'content': '记忆1', 'memory_type': 'core'}),
        execute_tool('memory_add', {'content': '记忆2', 'memory_type': 'episodic'}),
        execute_tool('memory_search', {'query': '搜索查询'})
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"任务 {i} 失败: {result}")
        else:
            print(f"任务 {i} 成功: {result['success']}")
```

## 最佳实践

### 1. 记忆内容设计
- **核心记忆**: 存储用户的基本信息，保持简洁和准确
- **情节记忆**: 记录具体事件，包含时间和上下文
- **语义记忆**: 存储概念和知识，使用清晰的定义
- **程序记忆**: 记录操作步骤，保持逻辑清晰
- **资源记忆**: 包含完整的链接和描述信息
- **知识库**: 结构化存储，便于检索和引用

### 2. 搜索优化
- 使用具体的关键词而非泛泛的描述
- 结合记忆类型过滤提高搜索精度
- 适当调整搜索结果数量限制
- 利用相关性评分选择最佳结果

### 3. 对话策略
- 开启记忆存储以建立连续的对话体验
- 对于敏感或临时信息，关闭记忆存储
- 利用多模态功能处理图片和文本结合的场景
- 定期检查和清理不必要的对话记忆

### 4. 监控和维护
- 定期获取记忆配置文件，了解使用情况
- 监控各类记忆的增长趋势
- 及时处理错误和异常情况
- 保持记忆内容的质量和相关性

---

**版本**: 1.0.0  
**更新时间**: 2024-01-01  
**维护团队**: MIRIX MCP Server Team