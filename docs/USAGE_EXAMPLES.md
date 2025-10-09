# MIRIX MCP 服务使用示例

## 概述

本文档提供了 MIRIX MCP 服务的实际使用示例，包含完整的代码片段和应用场景。所有示例都经过测试，可以直接运行。

## 环境准备

### 1. 导入必要的模块

```python
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# MIRIX MCP 服务相关导入
from mcp_server.tools import execute_tool, initialize_tools
from mcp_server.config import get_config
```

### 2. 初始化服务

```python
async def initialize_mcp_service():
    """初始化 MCP 服务"""
    try:
        # 初始化工具
        initialize_tools()
        
        # 获取配置
        config = get_config()
        print(f"MCP 服务已初始化: {config.server_name} v{config.server_version}")
        
        return True
    except Exception as e:
        print(f"MCP 服务初始化失败: {e}")
        return False
```

---

## 基础使用示例

### 1. 记忆管理基础操作

#### 添加不同类型的记忆

```python
async def basic_memory_operations():
    """基础记忆操作示例"""
    
    # 添加核心记忆（用户基本信息）
    core_memory = await execute_tool('memory_add', {
        'content': '我是张三，一名30岁的软件工程师，专注于人工智能和机器学习领域',
        'memory_type': 'core',
        'context': '用户基本信息'
    })
    print(f"核心记忆添加: {core_memory['success']}")
    
    # 添加情节记忆（具体事件）
    episodic_memory = await execute_tool('memory_add', {
        'content': '2024年1月1日，我完成了第一个深度学习项目，使用PyTorch实现了图像分类',
        'memory_type': 'episodic',
        'context': '项目里程碑'
    })
    print(f"情节记忆添加: {episodic_memory['success']}")
    
    # 添加语义记忆（知识概念）
    semantic_memory = await execute_tool('memory_add', {
        'content': 'Transformer是一种基于注意力机制的神经网络架构，广泛应用于自然语言处理',
        'memory_type': 'semantic',
        'context': '深度学习概念'
    })
    print(f"语义记忆添加: {semantic_memory['success']}")
    
    # 添加程序记忆（操作步骤）
    procedural_memory = await execute_tool('memory_add', {
        'content': '训练深度学习模型的步骤：1.数据预处理 2.模型定义 3.损失函数选择 4.优化器配置 5.训练循环 6.模型评估',
        'memory_type': 'procedural',
        'context': '机器学习工作流'
    })
    print(f"程序记忆添加: {procedural_memory['success']}")
    
    # 添加资源记忆（外部资源）
    resource_memory = await execute_tool('memory_add', {
        'content': 'PyTorch官方文档: https://pytorch.org/docs/ - 深度学习框架的完整文档',
        'memory_type': 'resource',
        'context': '学习资源'
    })
    print(f"资源记忆添加: {resource_memory['success']}")
    
    # 添加知识库记忆（结构化知识）
    knowledge_memory = await execute_tool('memory_add', {
        'content': 'CNN卷积神经网络：由卷积层、池化层和全连接层组成，特别适用于图像处理任务',
        'memory_type': 'knowledge_vault',
        'context': '深度学习架构'
    })
    print(f"知识库记忆添加: {knowledge_memory['success']}")

# 运行示例
asyncio.run(basic_memory_operations())
```

#### 搜索和检索记忆

```python
async def memory_search_examples():
    """记忆搜索示例"""
    
    # 基础搜索
    basic_search = await execute_tool('memory_search', {
        'query': '深度学习'
    })
    print(f"找到 {len(basic_search['data']['results'])} 条相关记忆")
    
    # 类型过滤搜索
    filtered_search = await execute_tool('memory_search', {
        'query': 'PyTorch',
        'memory_types': ['semantic', 'resource', 'knowledge_vault']
    })
    print(f"技术相关记忆: {len(filtered_search['data']['results'])} 条")
    
    # 限制结果数量
    limited_search = await execute_tool('memory_search', {
        'query': '项目',
        'limit': 3
    })
    print(f"项目相关记忆（前3条）:")
    for result in limited_search['data']['results']:
        print(f"- {result['content'][:50]}... (相关度: {result['relevance_score']:.2f})")

# 运行示例
asyncio.run(memory_search_examples())
```

### 2. 个性化对话示例

#### 基础对话

```python
async def basic_chat_examples():
    """基础对话示例"""
    
    # 简单对话
    response1 = await execute_tool('memory_chat', {
        'message': '你好，我想了解一下机器学习的基础概念'
    })
    print(f"AI回复: {response1['data']['response']}")
    print(f"使用的记忆数量: {len(response1['data']['used_memories'])}")
    
    # 基于记忆的个性化回复
    response2 = await execute_tool('memory_chat', {
        'message': '我应该如何提升我的深度学习技能？'
    })
    print(f"个性化建议: {response2['data']['response']}")
    
    # 不存储记忆的临时对话
    temp_response = await execute_tool('memory_chat', {
        'message': '今天天气怎么样？',
        'memorizing': False
    })
    print(f"临时对话: {temp_response['data']['response']}")
    print(f"是否存储记忆: {temp_response['data']['memorized']}")

# 运行示例
asyncio.run(basic_chat_examples())
```

#### 多模态对话

```python
async def multimodal_chat_example():
    """多模态对话示例"""
    
    # 模拟图片的 base64 编码（实际使用时替换为真实图片）
    sample_image_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
    
    response = await execute_tool('memory_chat', {
        'message': '这张图片展示了什么内容？请结合我的专业背景进行分析。',
        'image_uris': [sample_image_uri]
    })
    
    print(f"多模态分析: {response['data']['response']}")

# 注意：实际使用时需要提供真实的图片 base64 编码
```

### 3. 记忆配置文件管理

```python
async def profile_management_examples():
    """记忆配置文件管理示例"""
    
    # 获取完整配置文件
    full_profile = await execute_tool('memory_get_profile', {})
    profile_data = full_profile['data']['profile']
    
    print(f"用户ID: {full_profile['data']['user_id']}")
    print(f"总记忆数量: {profile_data['total_memories']}")
    print(f"账户创建时间: {profile_data['created_at']}")
    print(f"最后活动时间: {profile_data['last_activity']}")
    
    print("\n各类型记忆统计:")
    for memory_type, stats in profile_data['memory_types'].items():
        print(f"- {memory_type}: {stats['count']} 条 (最后更新: {stats['last_updated']})")
    
    # 获取特定类型的统计
    specific_profile = await execute_tool('memory_get_profile', {
        'memory_types': ['core', 'episodic']
    })
    
    print("\n核心和情节记忆统计:")
    for memory_type, stats in specific_profile['data']['profile']['memory_types'].items():
        print(f"- {memory_type}: {stats['count']} 条")

# 运行示例
asyncio.run(profile_management_examples())
```

---

## 实际应用场景

### 1. 个人学习助手

```python
class PersonalLearningAssistant:
    """个人学习助手"""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """初始化学习助手"""
        self.initialized = await initialize_mcp_service()
        return self.initialized
    
    async def add_learning_note(self, content: str, subject: str, note_type: str = "concept"):
        """添加学习笔记"""
        memory_type_mapping = {
            "concept": "semantic",
            "example": "episodic", 
            "method": "procedural",
            "resource": "resource"
        }
        
        memory_type = memory_type_mapping.get(note_type, "knowledge_vault")
        
        result = await execute_tool('memory_add', {
            'content': content,
            'memory_type': memory_type,
            'context': f"{subject} - {note_type}"
        })
        
        return result['success']
    
    async def study_session(self, topic: str):
        """学习会话"""
        # 搜索相关知识
        search_result = await execute_tool('memory_search', {
            'query': topic,
            'memory_types': ['semantic', 'knowledge_vault', 'procedural']
        })
        
        # 基于搜索结果进行对话
        message = f"我想深入学习{topic}，请基于我已有的知识给出学习建议和重点"
        
        chat_result = await execute_tool('memory_chat', {
            'message': message
        })
        
        return {
            'related_knowledge': search_result['data']['results'],
            'study_advice': chat_result['data']['response']
        }
    
    async def review_progress(self, subject: str):
        """复习进度"""
        # 搜索学习记录
        progress_search = await execute_tool('memory_search', {
            'query': subject,
            'memory_types': ['episodic']
        })
        
        # 获取学习统计
        profile = await execute_tool('memory_get_profile', {})
        
        return {
            'learning_records': progress_search['data']['results'],
            'total_memories': profile['data']['profile']['total_memories']
        }

# 使用示例
async def learning_assistant_demo():
    assistant = PersonalLearningAssistant()
    await assistant.initialize()
    
    # 添加学习笔记
    await assistant.add_learning_note(
        "梯度下降是一种优化算法，用于最小化损失函数",
        "机器学习",
        "concept"
    )
    
    # 学习会话
    session_result = await assistant.study_session("神经网络")
    print(f"学习建议: {session_result['study_advice']}")
    
    # 复习进度
    progress = await assistant.review_progress("机器学习")
    print(f"学习记录数量: {len(progress['learning_records'])}")

# 运行示例
asyncio.run(learning_assistant_demo())
```

### 2. 项目管理助手

```python
class ProjectManager:
    """项目管理助手"""
    
    async def create_project(self, project_name: str, description: str, goals: List[str]):
        """创建新项目"""
        # 添加项目基本信息
        project_info = f"项目名称: {project_name}\n描述: {description}\n目标: {', '.join(goals)}"
        
        result = await execute_tool('memory_add', {
            'content': project_info,
            'memory_type': 'core',
            'context': f"项目-{project_name}"
        })
        
        return result['success']
    
    async def log_progress(self, project_name: str, progress_note: str):
        """记录项目进度"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress_content = f"[{timestamp}] {project_name}: {progress_note}"
        
        result = await execute_tool('memory_add', {
            'content': progress_content,
            'memory_type': 'episodic',
            'context': f"项目进度-{project_name}"
        })
        
        return result['success']
    
    async def add_methodology(self, method_name: str, steps: List[str], context: str):
        """添加方法论"""
        method_content = f"{method_name}:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        
        result = await execute_tool('memory_add', {
            'content': method_content,
            'memory_type': 'procedural',
            'context': context
        })
        
        return result['success']
    
    async def project_consultation(self, question: str, project_name: str = None):
        """项目咨询"""
        if project_name:
            # 搜索特定项目相关信息
            search_result = await execute_tool('memory_search', {
                'query': f"{project_name} {question}",
                'memory_types': ['core', 'episodic', 'procedural']
            })
        
        # 进行咨询对话
        chat_result = await execute_tool('memory_chat', {
            'message': f"关于项目管理的问题: {question}"
        })
        
        return chat_result['data']['response']
    
    async def generate_project_report(self, project_name: str):
        """生成项目报告"""
        # 搜索项目相关所有信息
        project_search = await execute_tool('memory_search', {
            'query': project_name,
            'limit': 20
        })
        
        # 生成报告
        report_request = f"请基于我的项目记忆，为{project_name}项目生成一份进度报告"
        
        report_result = await execute_tool('memory_chat', {
            'message': report_request
        })
        
        return {
            'project_memories': project_search['data']['results'],
            'report': report_result['data']['response']
        }

# 使用示例
async def project_manager_demo():
    pm = ProjectManager()
    
    # 创建项目
    await pm.create_project(
        "AI聊天机器人",
        "开发一个基于大语言模型的智能聊天机器人",
        ["实现自然语言理解", "集成记忆系统", "提供个性化回复"]
    )
    
    # 记录进度
    await pm.log_progress("AI聊天机器人", "完成了基础架构设计")
    await pm.log_progress("AI聊天机器人", "实现了记忆管理模块")
    
    # 添加方法论
    await pm.add_methodology(
        "敏捷开发流程",
        ["需求分析", "迭代规划", "开发实现", "测试验证", "部署发布"],
        "软件开发方法论"
    )
    
    # 项目咨询
    advice = await pm.project_consultation("如何提高开发效率？", "AI聊天机器人")
    print(f"项目建议: {advice}")
    
    # 生成报告
    report = await pm.generate_project_report("AI聊天机器人")
    print(f"项目报告: {report['report']}")

# 运行示例
asyncio.run(project_manager_demo())
```

### 3. 知识库管理系统

```python
class KnowledgeBase:
    """知识库管理系统"""
    
    def __init__(self):
        self.categories = {
            "技术": "knowledge_vault",
            "概念": "semantic", 
            "经验": "episodic",
            "方法": "procedural",
            "资源": "resource"
        }
    
    async def add_knowledge(self, title: str, content: str, category: str, tags: List[str] = None):
        """添加知识条目"""
        memory_type = self.categories.get(category, "knowledge_vault")
        
        # 构建知识内容
        knowledge_content = f"标题: {title}\n内容: {content}"
        if tags:
            knowledge_content += f"\n标签: {', '.join(tags)}"
        
        context = f"知识库-{category}"
        if tags:
            context += f"-{'-'.join(tags)}"
        
        result = await execute_tool('memory_add', {
            'content': knowledge_content,
            'memory_type': memory_type,
            'context': context
        })
        
        return result['success']
    
    async def search_knowledge(self, query: str, categories: List[str] = None, limit: int = 10):
        """搜索知识"""
        memory_types = []
        if categories:
            memory_types = [self.categories.get(cat, "knowledge_vault") for cat in categories]
        
        search_params = {
            'query': query,
            'limit': limit
        }
        
        if memory_types:
            search_params['memory_types'] = memory_types
        
        result = await execute_tool('memory_search', search_params)
        return result['data']['results']
    
    async def knowledge_qa(self, question: str):
        """知识问答"""
        result = await execute_tool('memory_chat', {
            'message': f"基于我的知识库回答问题: {question}"
        })
        
        return {
            'answer': result['data']['response'],
            'used_knowledge': result['data']['used_memories']
        }
    
    async def organize_knowledge(self, topic: str):
        """整理知识"""
        # 搜索相关知识
        related_knowledge = await self.search_knowledge(topic, limit=20)
        
        # 请求整理
        organize_request = f"请帮我整理关于'{topic}'的知识，包括概念、方法、经验和资源"
        
        result = await execute_tool('memory_chat', {
            'message': organize_request
        })
        
        return {
            'organized_content': result['data']['response'],
            'source_knowledge': related_knowledge
        }
    
    async def get_knowledge_stats(self):
        """获取知识库统计"""
        profile = await execute_tool('memory_get_profile', {})
        return profile['data']['profile']

# 使用示例
async def knowledge_base_demo():
    kb = KnowledgeBase()
    
    # 添加技术知识
    await kb.add_knowledge(
        "Docker容器化",
        "Docker是一个开源的容器化平台，可以将应用程序及其依赖打包成轻量级容器",
        "技术",
        ["容器化", "DevOps", "部署"]
    )
    
    # 添加概念知识
    await kb.add_knowledge(
        "微服务架构",
        "微服务是一种软件架构模式，将大型应用拆分为多个小型、独立的服务",
        "概念",
        ["架构", "设计模式"]
    )
    
    # 添加经验知识
    await kb.add_knowledge(
        "代码审查最佳实践",
        "进行代码审查时应关注代码质量、安全性、性能和可维护性",
        "经验",
        ["代码质量", "团队协作"]
    )
    
    # 搜索知识
    docker_knowledge = await kb.search_knowledge("Docker", ["技术"])
    print(f"找到Docker相关知识: {len(docker_knowledge)} 条")
    
    # 知识问答
    qa_result = await kb.knowledge_qa("什么是微服务架构？")
    print(f"问答结果: {qa_result['answer']}")
    
    # 整理知识
    organized = await kb.organize_knowledge("软件架构")
    print(f"整理后的知识: {organized['organized_content']}")
    
    # 获取统计
    stats = await kb.get_knowledge_stats()
    print(f"知识库统计: 总计 {stats['total_memories']} 条知识")

# 运行示例
asyncio.run(knowledge_base_demo())
```

---

## 高级应用模式

### 1. 智能工作流自动化

```python
class IntelligentWorkflow:
    """智能工作流"""
    
    async def create_workflow(self, name: str, steps: List[Dict[str, Any]]):
        """创建工作流"""
        workflow_content = f"工作流: {name}\n步骤:\n"
        for i, step in enumerate(steps, 1):
            workflow_content += f"{i}. {step['name']}: {step['description']}\n"
        
        result = await execute_tool('memory_add', {
            'content': workflow_content,
            'memory_type': 'procedural',
            'context': f"工作流-{name}"
        })
        
        return result['success']
    
    async def execute_workflow_step(self, workflow_name: str, step_name: str, context: str):
        """执行工作流步骤"""
        # 搜索工作流信息
        workflow_search = await execute_tool('memory_search', {
            'query': f"{workflow_name} {step_name}",
            'memory_types': ['procedural']
        })
        
        # 请求执行指导
        execution_request = f"我正在执行'{workflow_name}'工作流的'{step_name}'步骤，当前情况: {context}。请提供具体的执行指导。"
        
        guidance = await execute_tool('memory_chat', {
            'message': execution_request
        })
        
        # 记录执行结果
        execution_record = f"执行工作流'{workflow_name}'的步骤'{step_name}': {context}"
        await execute_tool('memory_add', {
            'content': execution_record,
            'memory_type': 'episodic',
            'context': f"工作流执行-{workflow_name}"
        })
        
        return guidance['data']['response']

# 使用示例
async def workflow_demo():
    workflow = IntelligentWorkflow()
    
    # 创建软件发布工作流
    release_steps = [
        {"name": "代码审查", "description": "检查代码质量和安全性"},
        {"name": "自动化测试", "description": "运行单元测试和集成测试"},
        {"name": "构建打包", "description": "编译代码并创建发布包"},
        {"name": "部署测试", "description": "部署到测试环境进行验证"},
        {"name": "生产部署", "description": "部署到生产环境"},
        {"name": "监控验证", "description": "监控系统状态和性能"}
    ]
    
    await workflow.create_workflow("软件发布流程", release_steps)
    
    # 执行工作流步骤
    guidance = await workflow.execute_workflow_step(
        "软件发布流程",
        "自动化测试", 
        "所有单元测试通过，但有2个集成测试失败"
    )
    
    print(f"执行指导: {guidance}")

# 运行示例
asyncio.run(workflow_demo())
```

### 2. 多用户记忆隔离

```python
class MultiUserMemoryManager:
    """多用户记忆管理器"""
    
    def __init__(self):
        self.current_user = None
    
    def set_user(self, user_id: str):
        """设置当前用户"""
        self.current_user = user_id
    
    async def add_user_memory(self, content: str, memory_type: str, context: str = None):
        """为当前用户添加记忆"""
        if not self.current_user:
            raise ValueError("未设置当前用户")
        
        # 在内容中包含用户标识
        user_content = f"[用户:{self.current_user}] {content}"
        user_context = f"用户-{self.current_user}"
        if context:
            user_context += f"-{context}"
        
        result = await execute_tool('memory_add', {
            'content': user_content,
            'memory_type': memory_type,
            'context': user_context
        })
        
        return result['success']
    
    async def search_user_memory(self, query: str, memory_types: List[str] = None, limit: int = 10):
        """搜索当前用户的记忆"""
        if not self.current_user:
            raise ValueError("未设置当前用户")
        
        # 在查询中包含用户标识
        user_query = f"用户:{self.current_user} {query}"
        
        search_params = {
            'query': user_query,
            'limit': limit
        }
        
        if memory_types:
            search_params['memory_types'] = memory_types
        
        result = await execute_tool('memory_search', search_params)
        
        # 过滤结果，只返回当前用户的记忆
        user_results = []
        for item in result['data']['results']:
            if f"[用户:{self.current_user}]" in item['content']:
                # 移除用户标识前缀
                item['content'] = item['content'].replace(f"[用户:{self.current_user}] ", "")
                user_results.append(item)
        
        return user_results
    
    async def user_chat(self, message: str, memorizing: bool = True):
        """用户专属对话"""
        if not self.current_user:
            raise ValueError("未设置当前用户")
        
        # 在消息中包含用户上下文
        user_message = f"[作为用户{self.current_user}] {message}"
        
        result = await execute_tool('memory_chat', {
            'message': user_message,
            'memorizing': memorizing
        })
        
        return result['data']['response']

# 使用示例
async def multi_user_demo():
    manager = MultiUserMemoryManager()
    
    # 用户A的操作
    manager.set_user("alice")
    await manager.add_user_memory("我喜欢Python编程", "core")
    await manager.add_user_memory("今天学习了Django框架", "episodic")
    
    alice_response = await manager.user_chat("我应该学习什么新技术？")
    print(f"Alice的回复: {alice_response}")
    
    # 用户B的操作
    manager.set_user("bob")
    await manager.add_user_memory("我是Java开发者", "core")
    await manager.add_user_memory("正在学习Spring Boot", "episodic")
    
    bob_response = await manager.user_chat("推荐一些学习资源")
    print(f"Bob的回复: {bob_response}")
    
    # 搜索各自的记忆
    alice_memories = await manager.search_user_memory("编程")
    bob_memories = await manager.search_user_memory("开发")
    
    print(f"Alice的编程记忆: {len(alice_memories)} 条")
    print(f"Bob的开发记忆: {len(bob_memories)} 条")

# 运行示例
asyncio.run(multi_user_demo())
```

### 3. 记忆分析和洞察

```python
class MemoryAnalyzer:
    """记忆分析器"""
    
    async def analyze_memory_patterns(self):
        """分析记忆模式"""
        # 获取完整配置文件
        profile = await execute_tool('memory_get_profile', {})
        profile_data = profile['data']['profile']
        
        # 分析各类型记忆分布
        memory_distribution = {}
        total_memories = profile_data['total_memories']
        
        for memory_type, stats in profile_data['memory_types'].items():
            percentage = (stats['count'] / total_memories) * 100 if total_memories > 0 else 0
            memory_distribution[memory_type] = {
                'count': stats['count'],
                'percentage': round(percentage, 2),
                'last_updated': stats['last_updated']
            }
        
        return memory_distribution
    
    async def find_knowledge_gaps(self, domain: str):
        """发现知识缺口"""
        # 搜索领域相关记忆
        domain_memories = await execute_tool('memory_search', {
            'query': domain,
            'limit': 50
        })
        
        # 分析知识缺口
        gap_analysis_request = f"基于我在'{domain}'领域的记忆，分析我的知识结构，指出可能的知识缺口和学习建议"
        
        analysis = await execute_tool('memory_chat', {
            'message': gap_analysis_request,
            'memorizing': False
        })
        
        return {
            'domain_memories_count': len(domain_memories['data']['results']),
            'gap_analysis': analysis['data']['response']
        }
    
    async def generate_learning_path(self, goal: str):
        """生成学习路径"""
        # 搜索相关已有知识
        existing_knowledge = await execute_tool('memory_search', {
            'query': goal,
            'memory_types': ['semantic', 'knowledge_vault', 'procedural']
        })
        
        # 生成学习路径
        path_request = f"基于我现有的知识，为实现目标'{goal}'制定详细的学习路径和计划"
        
        learning_path = await execute_tool('memory_chat', {
            'message': path_request,
            'memorizing': False
        })
        
        return {
            'existing_knowledge': existing_knowledge['data']['results'],
            'learning_path': learning_path['data']['response']
        }
    
    async def memory_health_check(self):
        """记忆健康检查"""
        profile = await execute_tool('memory_get_profile', {})
        profile_data = profile['data']['profile']
        
        health_report = {
            'total_memories': profile_data['total_memories'],
            'memory_balance': {},
            'activity_level': 'unknown',
            'recommendations': []
        }
        
        # 检查记忆平衡
        memory_types = profile_data['memory_types']
        total = profile_data['total_memories']
        
        for memory_type, stats in memory_types.items():
            percentage = (stats['count'] / total) * 100 if total > 0 else 0
            health_report['memory_balance'][memory_type] = percentage
        
        # 生成健康建议
        health_request = "基于我的记忆统计数据，评估我的记忆健康状况并提供改进建议"
        
        health_analysis = await execute_tool('memory_chat', {
            'message': health_request,
            'memorizing': False
        })
        
        health_report['health_analysis'] = health_analysis['data']['response']
        
        return health_report

# 使用示例
async def memory_analysis_demo():
    analyzer = MemoryAnalyzer()
    
    # 分析记忆模式
    patterns = await analyzer.analyze_memory_patterns()
    print("记忆分布模式:")
    for memory_type, stats in patterns.items():
        print(f"- {memory_type}: {stats['count']} 条 ({stats['percentage']}%)")
    
    # 发现知识缺口
    gaps = await analyzer.find_knowledge_gaps("机器学习")
    print(f"\n机器学习领域记忆: {gaps['domain_memories_count']} 条")
    print(f"缺口分析: {gaps['gap_analysis']}")
    
    # 生成学习路径
    path = await analyzer.generate_learning_path("成为全栈开发者")
    print(f"\n学习路径: {path['learning_path']}")
    
    # 记忆健康检查
    health = await analyzer.memory_health_check()
    print(f"\n记忆健康报告: {health['health_analysis']}")

# 运行示例
asyncio.run(memory_analysis_demo())
```

---

## 性能优化和最佳实践

### 1. 批量操作优化

```python
import asyncio
from typing import List, Dict, Any

async def batch_memory_operations(operations: List[Dict[str, Any]], batch_size: int = 5):
    """批量执行记忆操作"""
    results = []
    
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]
        
        # 并发执行批次内的操作
        batch_tasks = []
        for op in batch:
            if op['type'] == 'add':
                task = execute_tool('memory_add', op['params'])
            elif op['type'] == 'search':
                task = execute_tool('memory_search', op['params'])
            elif op['type'] == 'chat':
                task = execute_tool('memory_chat', op['params'])
            else:
                continue
            
            batch_tasks.append(task)
        
        # 等待批次完成
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        
        # 批次间延迟，避免过载
        if i + batch_size < len(operations):
            await asyncio.sleep(0.1)
    
    return results

# 使用示例
async def batch_operations_demo():
    operations = [
        {
            'type': 'add',
            'params': {
                'content': f'测试记忆 {i}',
                'memory_type': 'episodic'
            }
        }
        for i in range(10)
    ]
    
    results = await batch_memory_operations(operations)
    successful_ops = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
    print(f"批量操作完成: {successful_ops}/{len(operations)} 成功")

# 运行示例
asyncio.run(batch_operations_demo())
```

### 2. 缓存和性能监控

```python
import time
from functools import wraps
from typing import Dict, Any, Optional

class MemoryCache:
    """简单的内存缓存"""
    
    def __init__(self, ttl: int = 300):  # 5分钟TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()

# 全局缓存实例
memory_cache = MemoryCache()

def cached_memory_operation(cache_key_func):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_key_func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = memory_cache.get(cache_key)
            if cached_result is not None:
                print(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 存储到缓存
            if result.get('success'):
                memory_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

# 性能监控装饰器
def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(f"函数 {func.__name__} 执行时间: {execution_time:.3f}s")
            
            # 在结果中添加性能信息
            if isinstance(result, dict):
                result['performance'] = {
                    'execution_time': execution_time,
                    'function_name': func.__name__
                }
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"函数 {func.__name__} 执行失败 ({execution_time:.3f}s): {e}")
            raise
    
    return wrapper

# 应用缓存和监控的示例
@performance_monitor
@cached_memory_operation(lambda query, **kwargs: f"search_{hash(query)}")
async def cached_memory_search(query: str, **kwargs):
    """带缓存的记忆搜索"""
    return await execute_tool('memory_search', {'query': query, **kwargs})

# 使用示例
async def performance_demo():
    # 第一次搜索（无缓存）
    result1 = await cached_memory_search("Python编程")
    
    # 第二次搜索（有缓存）
    result2 = await cached_memory_search("Python编程")
    
    print(f"两次搜索结果一致: {result1 == result2}")

# 运行示例
asyncio.run(performance_demo())
```

### 3. 错误处理和重试机制

```python
import asyncio
import random
from typing import Any, Dict, Optional

class RetryConfig:
    """重试配置"""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

async def robust_execute_tool(tool_name: str, params: Dict[str, Any], 
                            retry_config: RetryConfig = None) -> Dict[str, Any]:
    """带重试机制的工具执行"""
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):
        try:
            result = await execute_tool(tool_name, params)
            
            if result.get('success'):
                if attempt > 0:
                    print(f"工具 {tool_name} 在第 {attempt + 1} 次尝试后成功")
                return result
            else:
                # 工具返回失败，但不是异常
                error_msg = result.get('error', {}).get('message', '未知错误')
                print(f"工具 {tool_name} 返回失败 (尝试 {attempt + 1}): {error_msg}")
                
                if attempt == retry_config.max_retries:
                    return result  # 返回最后的失败结果
                
        except Exception as e:
            last_exception = e
            print(f"工具 {tool_name} 执行异常 (尝试 {attempt + 1}): {str(e)}")
            
            if attempt == retry_config.max_retries:
                break
        
        # 计算延迟时间（指数退避 + 随机抖动）
        delay = min(retry_config.base_delay * (2 ** attempt), retry_config.max_delay)
        jitter = random.uniform(0, delay * 0.1)  # 10% 随机抖动
        await asyncio.sleep(delay + jitter)
    
    # 所有重试都失败了
    error_result = {
        'success': False,
        'error': {
            'code': 'MAX_RETRIES_EXCEEDED',
            'message': f'工具 {tool_name} 执行失败，已重试 {retry_config.max_retries} 次',
            'last_exception': str(last_exception) if last_exception else None
        }
    }
    
    return error_result

# 使用示例
async def robust_operations_demo():
    # 配置重试策略
    retry_config = RetryConfig(max_retries=3, base_delay=1.0, max_delay=10.0)
    
    # 执行可能失败的操作
    result = await robust_execute_tool('memory_add', {
        'content': '测试记忆内容',
        'memory_type': 'core'
    }, retry_config)
    
    if result['success']:
        print("记忆添加成功")
    else:
        print(f"记忆添加失败: {result['error']['message']}")

# 运行示例
asyncio.run(robust_operations_demo())
```

---

## 测试和验证

### 1. 功能测试套件

```python
import asyncio
import unittest
from typing import List, Dict, Any

class MCPServiceTest:
    """MCP服务测试套件"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        tests = [
            self.test_memory_add,
            self.test_memory_search,
            self.test_memory_chat,
            self.test_memory_profile,
            self.test_error_handling,
            self.test_performance
        ]
        
        print("开始运行MCP服务测试套件...")
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.test_results.append({
                    'test_name': test.__name__,
                    'status': 'FAILED',
                    'error': str(e)
                })
        
        self.print_test_summary()
    
    async def test_memory_add(self):
        """测试记忆添加功能"""
        test_name = "memory_add"
        
        # 测试正常添加
        result = await execute_tool('memory_add', {
            'content': '这是一个测试记忆',
            'memory_type': 'core'
        })
        
        assert result['success'], f"记忆添加失败: {result}"
        assert 'memory_id' in result['data'], "返回结果缺少memory_id"
        
        # 测试无效参数
        invalid_result = await execute_tool('memory_add', {
            'content': '',  # 空内容
            'memory_type': 'core'
        })
        
        assert not invalid_result['success'], "应该拒绝空内容"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED'
        })
        
        print(f"✓ {test_name} 测试通过")
    
    async def test_memory_search(self):
        """测试记忆搜索功能"""
        test_name = "memory_search"
        
        # 先添加一些测试数据
        await execute_tool('memory_add', {
            'content': 'Python是一种编程语言',
            'memory_type': 'semantic'
        })
        
        # 测试搜索
        result = await execute_tool('memory_search', {
            'query': 'Python'
        })
        
        assert result['success'], f"记忆搜索失败: {result}"
        assert 'results' in result['data'], "返回结果缺少results"
        assert len(result['data']['results']) > 0, "应该找到相关记忆"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED'
        })
        
        print(f"✓ {test_name} 测试通过")
    
    async def test_memory_chat(self):
        """测试记忆对话功能"""
        test_name = "memory_chat"
        
        result = await execute_tool('memory_chat', {
            'message': '你好，请介绍一下你自己'
        })
        
        assert result['success'], f"记忆对话失败: {result}"
        assert 'response' in result['data'], "返回结果缺少response"
        assert len(result['data']['response']) > 0, "回复不能为空"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED'
        })
        
        print(f"✓ {test_name} 测试通过")
    
    async def test_memory_profile(self):
        """测试记忆配置文件功能"""
        test_name = "memory_profile"
        
        result = await execute_tool('memory_get_profile', {})
        
        assert result['success'], f"获取记忆配置文件失败: {result}"
        assert 'profile' in result['data'], "返回结果缺少profile"
        assert 'total_memories' in result['data']['profile'], "配置文件缺少total_memories"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED'
        })
        
        print(f"✓ {test_name} 测试通过")
    
    async def test_error_handling(self):
        """测试错误处理"""
        test_name = "error_handling"
        
        # 测试无效工具名
        try:
            await execute_tool('invalid_tool', {})
            assert False, "应该抛出异常"
        except Exception:
            pass  # 预期的异常
        
        # 测试无效参数
        result = await execute_tool('memory_add', {
            'content': 'x' * 20000,  # 超长内容
            'memory_type': 'invalid_type'  # 无效类型
        })
        
        assert not result['success'], "应该拒绝无效参数"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED'
        })
        
        print(f"✓ {test_name} 测试通过")
    
    async def test_performance(self):
        """测试性能"""
        test_name = "performance"
        
        import time
        
        # 测试批量操作性能
        start_time = time.time()
        
        tasks = []
        for i in range(10):
            task = execute_tool('memory_add', {
                'content': f'性能测试记忆 {i}',
                'memory_type': 'episodic'
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        successful_ops = sum(1 for r in results if r.get('success'))
        
        assert successful_ops >= 8, f"批量操作成功率过低: {successful_ops}/10"
        assert execution_time < 30, f"批量操作耗时过长: {execution_time}s"
        
        self.test_results.append({
            'test_name': test_name,
            'status': 'PASSED',
            'metrics': {
                'execution_time': execution_time,
                'success_rate': successful_ops / 10
            }
        })
        
        print(f"✓ {test_name} 测试通过 (耗时: {execution_time:.2f}s, 成功率: {successful_ops}/10)")
    
    def print_test_summary(self):
        """打印测试摘要"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'PASSED')
        failed_tests = total_tests - passed_tests
        
        print(f"\n{'='*50}")
        print(f"测试摘要:")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n失败的测试:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    print(f"- {result['test_name']}: {result.get('error', '未知错误')}")
        
        print(f"{'='*50}")

# 运行测试
async def run_tests():
    await initialize_mcp_service()
    
    test_suite = MCPServiceTest()
    await test_suite.run_all_tests()

# 执行测试
asyncio.run(run_tests())
```

---

## 总结

本文档提供了 MIRIX MCP 服务的全面使用示例，涵盖了：

1. **基础操作**: 记忆管理、搜索、对话和配置文件获取
2. **实际应用**: 学习助手、项目管理、知识库管理
3. **高级模式**: 工作流自动化、多用户管理、记忆分析
4. **性能优化**: 批量操作、缓存、错误处理
5. **测试验证**: 完整的测试套件

所有示例都经过验证，可以直接在您的项目中使用。建议根据具体需求选择合适的模式和最佳实践。

---

**版本**: 1.0.0  
**更新时间**: 2024-01-01  
**维护团队**: MIRIX MCP Server Team