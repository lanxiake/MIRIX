# MCP工具使用指南

本文档为AI助手提供详细的工具选择和使用指导，基于[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)最佳实践编写。

## 工具概览

MIRIX MCP服务器提供四个核心工具，每个工具都有特定的使用场景和目的：

| 工具名称 | 主要用途 | 使用时机 | 复杂度 |
|---------|---------|----------|--------|
| `memory_add` | 保存重要信息 | 发现需要记住的信息时 | 简单 |
| `memory_search` | 快速信息检索 | 查找具体事实或数据时 | 简单 |
| `memory_chat` | 智能分析对话 | 需要推理和分析时 | 复杂 |
| `resource_upload` | 文档知识库管理 | 处理文件和文档时 | 中等 |

## 决策流程图

```
用户提出问题/请求
       ↓
是否需要保存信息？
   ↓(是)        ↓(否)
memory_add    是否涉及文档？
                ↓(是)      ↓(否)
           resource_upload  问题是否复杂？
                           ↓(是)      ↓(否)
                       memory_chat  memory_search
```

## 详细使用指南

### 1. memory_add - 信息保存工具

**何时使用**：
- ✅ 用户明确说"请记住..."、"帮我保存..."
- ✅ 发现重要的用户偏好（编程语言、工具选择等）
- ✅ 用户做出重要决定或设定目标
- ✅ 需要记录重要的对话结论

**何时不使用**：
- ❌ 临时信息或一次性查询结果
- ❌ 通用知识（如"Python是编程语言"）
- ❌ 用户只是随意提到的信息

**最佳实践**：
```python
# 好的例子
await memory_add("用户偏好使用VSCode编辑器，特别喜欢Python扩展和主题Dark+")

# 不好的例子  
await memory_add("今天是星期一")  # 临时信息
```

### 2. memory_search vs memory_chat - 关键区别

这是最重要的选择决策，直接影响用户体验质量。

#### memory_search - 快速检索工具

**使用场景**：
- 查找具体事实："用户的生日是什么时候？"
- 检索特定偏好："用户喜欢什么编程语言？"
- 寻找历史记录："用户之前提到的项目有哪些？"
- 简单信息查询："关于Python的记忆有哪些？"

**特点**：
- 返回原始记忆片段
- 快速直接
- 适合事实查询
- 不需要AI推理

#### memory_chat - 智能分析工具

**使用场景**：
- 复杂问题分析："基于我的经历，如何规划职业发展？"
- 个性化建议："根据我的偏好，推荐技术栈"
- 趋势分析："我最近的兴趣有什么变化？"
- 决策支持："考虑我的经验，这个项目要注意什么？"

**特点**：
- AI生成智能回复
- 基于记忆进行推理
- 提供个性化建议
- 适合复杂分析

#### 判断标准

**使用memory_search的信号**：
- 问题包含"什么时候"、"哪些"、"是否"
- 需要具体的事实或数据
- 可以用简单搜索回答

**使用memory_chat的信号**：
- 问题包含"如何"、"为什么"、"建议"
- 需要分析和推理
- 需要综合多个信息
- 寻求个性化意见

### 3. memory_types参数使用指南

在使用`memory_search`时，合理选择记忆类型可以提高检索精度：

```python
# 查找用户基本偏好
await memory_search("编程语言", memory_types=["core"], limit=5)

# 查找具体事件
await memory_search("项目会议", memory_types=["episodic"])

# 查找学习内容
await memory_search("Python教程", memory_types=["semantic", "resource"])

# 查找操作步骤
await memory_search("部署流程", memory_types=["procedural"])
```

### 4. resource_upload - 文档管理工具

**使用场景**：
- 用户上传文档文件
- 需要建立知识库
- 批量保存文本内容
- 集成外部资源

**最佳实践**：
```python
# 提供详细描述
await resource_upload(
    "API文档.pdf", 
    pdf_content, 
    "application/pdf",
    "项目核心API接口文档，包含认证和数据格式说明"
)
```

## 实际使用示例

### 场景1：用户咨询问题

**用户**："我之前学过什么编程语言？"

**分析**：简单事实查询
**选择**：memory_search
```python
await memory_search("编程语言", memory_types=["core", "semantic"])
```

### 场景2：用户寻求建议

**用户**："基于我的学习背景，我应该学什么技术栈？"

**分析**：需要分析和个性化建议
**选择**：memory_chat
```python
await memory_chat("基于我的学习背景，我应该学什么技术栈？")
```

### 场景3：用户表达偏好

**用户**："我觉得React比Vue更适合我"

**分析**：重要偏好信息需要保存
**选择**：memory_add
```python
await memory_add("用户偏好React框架而不是Vue，认为React更适合自己的开发风格")
```

### 场景4：用户上传文档

**用户**："帮我保存这个项目文档"

**分析**：文档处理需求
**选择**：resource_upload
```python
await resource_upload(
    file_name="项目文档.md",
    file_content=document_content,
    file_type="text/markdown",
    description="项目核心设计文档"
)
```

## 错误处理和优化

### 常见错误

1. **混淆search和chat**：
   - 错误：用memory_chat查询简单事实
   - 正确：简单查询用search，复杂分析用chat

2. **过度使用memory_add**：
   - 错误：保存所有提到的信息
   - 正确：只保存重要和有价值的信息

3. **忽略memory_types**：
   - 错误：总是搜索所有类型
   - 正确：根据查询内容选择合适类型

### 性能优化

1. **合理设置limit参数**：
   - 精确查询：limit=3-5
   - 广泛搜索：limit=10-15
   - 探索性查询：limit=20+

2. **优化搜索关键词**：
   - 使用具体、相关的关键词
   - 避免过于宽泛的搜索词
   - 考虑同义词和相关词汇

## 总结

选择合适的工具是提供优质用户体验的关键。记住：

- **memory_add**：保存重要信息
- **memory_search**：快速查找事实
- **memory_chat**：智能分析推理  
- **resource_upload**：文档知识管理

通过正确使用这些工具，AI可以提供更加个性化、准确和有价值的服务。
