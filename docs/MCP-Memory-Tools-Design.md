# MIRIX MCP 记忆管理工具设计文档

## 概述

本文档描述了 MIRIX MCP (Model Context Protocol) 服务的简化工具设计方案。该方案专注于记忆管理的核心功能，为 AI Agent 提供简单、高效的记忆操作接口。

## 设计原则

1. **简单专注**: 只提供记忆相关的核心功能
2. **配置驱动**: 用户ID、模型等配置在工具初始化时设置
3. **场景明确**: 每个工具都有清晰的使用场景和执行顺序说明
4. **移除冗余**: 删除通用的 `list_mirix_tools` 和 `call_mirix_tool`

## 工具列表

### 1. memory_add - 添加记忆

**功能描述**: 向 MIRIX 记忆系统添加新信息。这是最基础的工具，用于将重要信息存储到用户的个人记忆库中。

**使用场景**:
- 当用户分享个人信息、偏好或重要事实时使用
- 学习新知识或技能时，将关键信息存储起来
- 记录重要的对话内容或决定
- 保存工作流程、步骤说明等程序性知识

**执行顺序**: 通常是对话中的第一步，在获取到有价值信息后立即使用

**预期效果**: 信息被永久存储，可通过 memory_search 检索，增强 AI 对用户的了解

**参数**:
```json
{
  "content": {
    "type": "string",
    "required": true,
    "description": "要存储的内容，应该是完整、有意义的信息片段"
  },
  "memory_type": {
    "type": "string",
    "required": true,
    "enum": ["core", "episodic", "semantic", "procedural", "resource", "knowledge_vault"],
    "description": "记忆类型：core(个人信息)、episodic(事件)、semantic(知识)、procedural(步骤)、resource(资源)、knowledge_vault(参考数据)"
  },
  "context": {
    "type": "string",
    "required": false,
    "description": "可选的上下文信息，帮助理解内容的背景"
  }
}
```

### 2. memory_search - 搜索记忆

**功能描述**: 在用户的记忆系统中搜索相关信息。这是获取历史信息的主要方式。

**使用场景**:
- 用户询问之前讨论过的话题时使用
- 需要回忆用户的偏好、习惯或个人信息时
- 查找相关的知识、经验或程序步骤
- 在回答问题前，先检索相关的背景信息

**执行顺序**: 通常在 memory_add 之前使用，避免重复存储；在回答用户问题前使用

**预期效果**: 获取相关的历史信息，提供更个性化、连贯的回应

**参数**:
```json
{
  "query": {
    "type": "string",
    "required": true,
    "description": "搜索查询，使用自然语言描述要查找的内容"
  },
  "memory_types": {
    "type": "array",
    "items": {"type": "string"},
    "required": false,
    "description": "要搜索的记忆类型列表，不指定则搜索所有类型"
  },
  "limit": {
    "type": "integer",
    "required": false,
    "default": 10,
    "description": "返回结果的最大数量"
  }
}
```

### 3. memory_chat - 记忆增强对话

**功能描述**: 发送消息给 MIRIX Agent 并自动管理记忆。这是一个智能对话工具，会自动决定是否存储对话内容。

**使用场景**:
- 进行需要记忆上下文的深度对话
- 讨论重要话题，希望 AI 记住关键信息
- 获取基于个人记忆的个性化回应
- 当需要 AI 学习和适应用户偏好时

**执行顺序**: 可以独立使用，或在 memory_search 后使用以提供更好的上下文

**预期效果**: 获得个性化回应，重要信息自动存储到记忆中

**参数**:
```json
{
  "message": {
    "type": "string",
    "required": true,
    "description": "要发送的消息内容"
  },
  "memorizing": {
    "type": "boolean",
    "required": false,
    "default": true,
    "description": "是否将对话内容存储到记忆中"
  },
  "image_uris": {
    "type": "array",
    "items": {"type": "string"},
    "required": false,
    "description": "可选的图片URI列表，用于多模态对话"
  }
}
```

### 4. memory_get_profile - 获取用户档案

**功能描述**: 获取用户的完整记忆档案概览。用于了解用户的基本信息、偏好和历史。

**使用场景**:
- 初次与用户交互时，了解用户背景
- 需要全面了解用户偏好和特点时
- 为用户提供个性化建议前的信息收集
- 定期回顾和更新对用户的了解

**执行顺序**: 通常在对话开始时使用，为后续交互提供基础

**预期效果**: 获得用户的全面画像，包括个人信息、偏好、历史记录等

**参数**:
```json
{
  "memory_types": {
    "type": "array",
    "items": {"type": "string"},
    "required": false,
    "description": "要获取的记忆类型，不指定则获取所有类型的概览"
  }
}
```

## 典型使用流程

### 场景 1: 新用户初次对话
```
1. memory_get_profile() → 了解用户背景
2. memory_chat(message="...", memorizing=true) → 进行对话并学习
3. memory_add() → 补充重要信息（如果需要）
```

### 场景 2: 回答用户问题
```
1. memory_search(query="相关话题") → 检索相关信息
2. memory_chat(message="基于记忆的回答") → 提供个性化回应
```

### 场景 3: 学习新信息
```
1. memory_search() → 检查是否已有相关信息
2. memory_add() → 存储新信息
3. memory_chat() → 确认理解并讨论
```

## 配置项设计

在 MCP 服务初始化时配置以下参数：

```json
{
  "default_user_id": "用户ID，所有操作的默认用户",
  "ai_model": "使用的AI模型名称",
  "memory_settings": {
    "auto_categorize": true,
    "default_memory_type": "semantic",
    "search_limit": 10
  },
  "mirix_backend_url": "MIRIX后端服务地址"
}
```

## 记忆类型说明

- **core**: 核心记忆 - 用户个人资料和交互偏好
- **episodic**: 情景记忆 - 时间相关的事件和活动
- **semantic**: 语义记忆 - 通用知识和概念
- **procedural**: 程序记忆 - 步骤说明和工作流程
- **resource**: 资源记忆 - 文件、文档和参考资料
- **knowledge_vault**: 知识库记忆 - 静态参考数据（联系信息、密码等）

## 实现注意事项

1. **错误处理**: 所有工具都应提供统一的错误响应格式
2. **日志记录**: 记录所有操作的详细日志，便于调试和监控
3. **性能优化**: 对频繁的搜索操作进行缓存优化
4. **安全性**: 确保用户数据的隔离和安全访问
5. **扩展性**: 保持接口的向前兼容性，便于未来功能扩展

## 版本信息

- **文档版本**: 1.0
- **创建日期**: 2024-01-20
- **最后更新**: 2024-01-20
- **作者**: MIRIX Team