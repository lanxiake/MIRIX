# MIRIX系统架构设计文档

## 架构概览

MIRIX是一个基于多智能体记忆系统的个人助手平台，采用分层微服务架构，支持多模态输入、隐私优先设计和实时交互。系统通过六层记忆架构和九种专业化智能体，提供智能化的个人助手服务。

**架构版本**: v0.1.4  
**设计原则**: 模块化、可扩展、隐私优先、高性能  
**部署模式**: 本地部署、云端部署、混合部署  

---

## 第一层：整体架构大纲

### 🏗️ 系统架构全景图

```mermaid
graph TB
    subgraph "用户界面层 - User Interface Layer"
        A[Web前端界面] --> B[Electron桌面应用]
        B --> C[移动端应用]
        C --> D[屏幕活动监控]
    end
    
    subgraph "API网关层 - API Gateway Layer"
        E[FastAPI主服务] --> F[MCP SSE服务]
        F --> G[认证授权中间件]
        G --> H[限流和监控中间件]
    end
    
    subgraph "智能体层 - Agent Layer"
        I[Agent核心引擎] --> J[9种专业化智能体]
        J --> K[智能体协作管理器]
        K --> L[LLM集成层]
    end
    
    subgraph "记忆系统层 - Memory System Layer"
        M[记忆管理器集群] --> N[六层记忆架构]
        N --> O[混合搜索引擎]
        O --> P[向量数据库]
    end
    
    subgraph "服务层 - Service Layer"
        Q[业务服务管理器] --> R[文档处理服务]
        R --> S[MCP协议服务]
        S --> T[工具集成服务]
    end
    
    subgraph "数据访问层 - Data Access Layer"
        U[ORM数据访问层] --> V[PostgreSQL主数据库]
        V --> W[Redis缓存层]
        W --> X[pgvector向量存储]
    end
    
    subgraph "基础设施层 - Infrastructure Layer"
        Y[Docker容器化] --> Z[日志监控系统]
        Z --> AA[配置管理]
        AA --> BB[安全和备份]
    end
    
    A --> E
    E --> I
    I --> M
    M --> Q
    Q --> U
    U --> Y
```

### 🎯 核心设计原则

#### 1. 模块化设计原则
- **高内聚低耦合**：每个模块职责单一，模块间依赖最小化
- **接口标准化**：统一的接口规范和数据格式
- **可插拔架构**：支持组件的动态加载和替换
- **服务化拆分**：按业务领域拆分独立服务

#### 2. 可扩展性原则
- **水平扩展**：支持多实例部署和负载均衡
- **垂直扩展**：支持单实例性能优化和资源扩容
- **功能扩展**：支持新智能体类型和记忆模型的添加
- **协议扩展**：支持新的通信协议和数据格式

#### 3. 隐私优先原则
- **本地优先**：核心数据和处理优先在本地进行
- **数据加密**：敏感数据的传输和存储加密
- **访问控制**：细粒度的权限管理和访问控制
- **审计日志**：完整的操作审计和数据访问记录

#### 4. 高性能原则
- **异步处理**：充分利用异步编程提高并发性能
- **缓存策略**：多层缓存减少数据库访问
- **连接池**：数据库和HTTP连接池优化
- **流式处理**：大数据量的流式传输和处理

### 📊 技术栈选型

#### 核心技术栈
```yaml
编程语言:
  - Python 3.11+: 主要开发语言
  - TypeScript: 前端开发语言
  - SQL: 数据库查询语言

Web框架:
  - FastAPI: 高性能异步Web框架
  - React: 前端UI框架
  - Electron: 桌面应用框架

数据存储:
  - PostgreSQL 16+: 主数据库
  - pgvector: 向量数据库扩展
  - Redis 7+: 缓存和会话存储
  - SQLite: 本地开发数据库

AI/ML技术:
  - OpenAI GPT-4: 主要LLM模型
  - Anthropic Claude: 备选LLM模型
  - Sentence Transformers: 文本向量化
  - LangChain: LLM应用框架

通信协议:
  - HTTP/HTTPS: RESTful API
  - WebSocket: 实时双向通信
  - Server-Sent Events: 流式数据推送
  - MCP Protocol: 模型上下文协议

部署运维:
  - Docker: 容器化部署
  - Docker Compose: 本地开发环境
  - Nginx: 反向代理和负载均衡
  - Prometheus + Grafana: 监控告警
```

### 🔄 数据流架构

#### 核心数据流图
```mermaid
sequenceDiagram
    participant User as 用户
    participant UI as 用户界面
    participant API as API网关
    participant Agent as 智能体引擎
    participant Memory as 记忆系统
    participant LLM as LLM服务
    participant DB as 数据库
    
    User->>UI: 输入消息/上传文档
    UI->>API: HTTP/WebSocket请求
    API->>Agent: 路由到对应智能体
    
    Agent->>Memory: 查询相关记忆
    Memory->>DB: 执行混合搜索
    DB-->>Memory: 返回搜索结果
    Memory-->>Agent: 返回相关记忆
    
    Agent->>LLM: 构建提示词并调用
    LLM-->>Agent: 返回生成内容
    
    Agent->>Memory: 存储新记忆
    Memory->>DB: 持久化记忆数据
    
    Agent-->>API: 返回响应（流式）
    API-->>UI: SSE流式响应
    UI-->>User: 实时显示结果
    
    Note over User,DB: 全流程异步处理，支持实时交互
```

#### 记忆系统数据流
```mermaid
graph LR
    subgraph "输入处理"
        A[用户输入] --> B[内容解析]
        B --> C[语义分析]
        C --> D[向量化处理]
    end
    
    subgraph "记忆检索"
        E[查询构建] --> F[混合搜索]
        F --> G[BM25文本搜索]
        F --> H[向量相似度搜索]
        G --> I[结果融合排序]
        H --> I
    end
    
    subgraph "记忆存储"
        J[记忆分类] --> K[Core Memory]
        J --> L[Episodic Memory]
        J --> M[Semantic Memory]
        J --> N[Procedural Memory]
        J --> O[Resource Memory]
        J --> P[Knowledge Vault]
    end
    
    subgraph "智能体处理"
        Q[记忆整合] --> R[上下文构建]
        R --> S[LLM推理]
        S --> T[响应生成]
    end
    
    D --> E
    I --> Q
    T --> J
```

---

## 第二层：技术设计支持

### 🏛️ 分层架构设计

#### 1. 用户界面层设计
```typescript
// 前端架构设计
interface UIArchitecture {
  // React组件架构
  components: {
    layout: 'MainLayout' | 'ChatLayout' | 'SettingsLayout';
    pages: 'ChatPage' | 'AgentsPage' | 'MemoryPage' | 'SettingsPage';
    widgets: 'MessageWidget' | 'AgentWidget' | 'MemoryWidget';
  };
  
  // 状态管理
  stateManagement: {
    global: 'Redux Toolkit';
    local: 'React Hooks';
    persistence: 'Redux Persist';
  };
  
  // 通信层
  communication: {
    http: 'Axios';
    websocket: 'Socket.IO Client';
    sse: 'EventSource API';
  };
  
  // Electron集成
  desktop: {
    main: 'Electron Main Process';
    renderer: 'React Renderer Process';
    ipc: 'Inter-Process Communication';
    native: 'Node.js Native Modules';
  };
}

// 屏幕监控架构
interface ScreenMonitoring {
  capture: {
    method: 'screenshot-desktop' | 'node-screenshots';
    frequency: number; // 截图频率（秒）
    quality: 'low' | 'medium' | 'high';
  };
  
  processing: {
    ocr: 'Tesseract.js';
    imageAnalysis: 'Canvas API';
    dataExtraction: 'Custom Algorithms';
  };
  
  privacy: {
    localProcessing: boolean;
    dataEncryption: boolean;
    userConsent: boolean;
  };
}
```

#### 2. API网关层设计
```python
# API网关架构设计
from typing import Protocol, Dict, Any
from abc import ABC, abstractmethod

class APIGatewayArchitecture:
    """API网关架构设计"""
    
    def __init__(self):
        self.middleware_stack = [
            'CORSMiddleware',
            'LoggingMiddleware', 
            'AuthenticationMiddleware',
            'RateLimitingMiddleware',
            'ValidationMiddleware'
        ]
        
        self.routing_strategy = {
            'agents': 'AgentServiceRouter',
            'memory': 'MemoryServiceRouter',
            'documents': 'DocumentServiceRouter',
            'mcp': 'MCPServiceRouter'
        }
        
        self.response_formats = {
            'sync': 'JSONResponse',
            'async': 'StreamingResponse',
            'sse': 'ServerSentEventsResponse'
        }

class MiddlewareProtocol(Protocol):
    """中间件协议定义"""
    
    async def process_request(self, request: Any) -> Any:
        """处理请求"""
        ...
    
    async def process_response(self, response: Any) -> Any:
        """处理响应"""
        ...

class AuthenticationMiddleware:
    """认证中间件实现"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.excluded_paths = ['/health', '/docs', '/openapi.json']
    
    async def process_request(self, request):
        """处理认证逻辑"""
        if request.url.path in self.excluded_paths:
            return request
        
        # API密钥验证
        api_key = request.headers.get('X-API-Key')
        if not api_key or not self.validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="无效的API密钥")
        
        return request
    
    def validate_api_key(self, api_key: str) -> bool:
        """验证API密钥"""
        # 实现API密钥验证逻辑
        return True

class RateLimitingMiddleware:
    """限流中间件实现"""
    
    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
    
    async def process_request(self, request):
        """处理限流逻辑"""
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        current_requests = await self.redis.get(key)
        if current_requests and int(current_requests) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="请求频率超限")
        
        # 增加请求计数
        await self.redis.incr(key)
        await self.redis.expire(key, 60)  # 1分钟过期
        
        return request
```

#### 3. 智能体层架构设计
```python
# 智能体层架构设计
from enum import Enum
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

class AgentType(Enum):
    """智能体类型枚举"""
    CORE_MEMORY = "core_memory"
    EPISODIC_MEMORY = "episodic_memory"
    SEMANTIC_MEMORY = "semantic_memory"
    PROCEDURAL_MEMORY = "procedural_memory"
    RESOURCE_MEMORY = "resource_memory"
    KNOWLEDGE_VAULT = "knowledge_vault"
    CHAT = "chat"
    SEARCH = "search"
    TOOL = "tool"

class AgentArchitecture:
    """智能体架构设计"""
    
    def __init__(self):
        self.agent_registry = {}
        self.collaboration_patterns = {
            'sequential': 'SequentialCollaboration',
            'parallel': 'ParallelCollaboration',
            'hierarchical': 'HierarchicalCollaboration',
            'peer_to_peer': 'PeerToPeerCollaboration'
        }
        
        self.communication_protocols = {
            'message_passing': 'MessagePassingProtocol',
            'shared_memory': 'SharedMemoryProtocol',
            'event_driven': 'EventDrivenProtocol'
        }

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState()
        self.memory_managers = {}
        self.tools = []
    
    @abstractmethod
    async def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """处理消息的抽象方法"""
        pass
    
    @abstractmethod
    async def collaborate(self, other_agents: List['BaseAgent'], task: str) -> Any:
        """智能体协作的抽象方法"""
        pass
    
    async def update_memory(self, memory_type: str, content: Any):
        """更新记忆"""
        if memory_type in self.memory_managers:
            await self.memory_managers[memory_type].store(content)
    
    async def retrieve_memory(self, query: str, memory_type: str = None) -> List[Any]:
        """检索记忆"""
        if memory_type and memory_type in self.memory_managers:
            return await self.memory_managers[memory_type].search(query)
        
        # 跨记忆类型搜索
        results = []
        for manager in self.memory_managers.values():
            results.extend(await manager.search(query))
        
        return results

class AgentCollaborationManager:
    """智能体协作管理器"""
    
    def __init__(self):
        self.active_collaborations = {}
        self.collaboration_history = []
    
    async def orchestrate_collaboration(
        self, 
        agents: List[BaseAgent], 
        task: str, 
        pattern: str = 'sequential'
    ) -> Any:
        """编排智能体协作"""
        
        collaboration_id = f"collab_{len(self.active_collaborations)}"
        
        if pattern == 'sequential':
            return await self._sequential_collaboration(agents, task, collaboration_id)
        elif pattern == 'parallel':
            return await self._parallel_collaboration(agents, task, collaboration_id)
        elif pattern == 'hierarchical':
            return await self._hierarchical_collaboration(agents, task, collaboration_id)
        else:
            raise ValueError(f"不支持的协作模式: {pattern}")
    
    async def _sequential_collaboration(
        self, 
        agents: List[BaseAgent], 
        task: str, 
        collaboration_id: str
    ) -> Any:
        """顺序协作模式"""
        result = task
        context = {"collaboration_id": collaboration_id, "step": 0}
        
        for agent in agents:
            context["step"] += 1
            result = await agent.process_message(result, context)
            
            # 记录协作步骤
            self.collaboration_history.append({
                "collaboration_id": collaboration_id,
                "agent_id": agent.agent_id,
                "step": context["step"],
                "input": task if context["step"] == 1 else "previous_result",
                "output": result
            })
        
        return result
    
    async def _parallel_collaboration(
        self, 
        agents: List[BaseAgent], 
        task: str, 
        collaboration_id: str
    ) -> Any:
        """并行协作模式"""
        import asyncio
        
        context = {"collaboration_id": collaboration_id, "mode": "parallel"}
        
        # 并行执行所有智能体
        tasks = [agent.process_message(task, context) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        merged_result = self._merge_parallel_results(results, agents)
        
        return merged_result
    
    def _merge_parallel_results(self, results: List[Any], agents: List[BaseAgent]) -> Any:
        """合并并行协作结果"""
        # 根据智能体类型和结果类型进行智能合并
        merged = {
            "collaboration_type": "parallel",
            "agent_results": {}
        }
        
        for agent, result in zip(agents, results):
            merged["agent_results"][agent.agent_id] = {
                "agent_type": agent.agent_type.value,
                "result": result
            }
        
        return merged
```

#### 4. 记忆系统架构设计
```python
# 记忆系统架构设计
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

class MemoryType(Enum):
    """记忆类型枚举"""
    CORE = "core"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    RESOURCE = "resource"
    KNOWLEDGE_VAULT = "knowledge_vault"

@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    memory_type: MemoryType
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    relevance_score: Optional[float] = None

class MemorySystemArchitecture:
    """记忆系统架构设计"""
    
    def __init__(self):
        self.memory_managers = {}
        self.search_engine = HybridSearchEngine()
        self.embedding_service = EmbeddingService()
        self.memory_consolidation = MemoryConsolidationService()
    
    def register_memory_manager(self, memory_type: MemoryType, manager):
        """注册记忆管理器"""
        self.memory_managers[memory_type] = manager
    
    async def store_memory(
        self, 
        content: str, 
        memory_type: MemoryType, 
        metadata: Dict[str, Any] = None
    ) -> MemoryItem:
        """存储记忆"""
        
        # 生成向量嵌入
        embedding = await self.embedding_service.generate_embedding(content)
        
        # 创建记忆项
        memory_item = MemoryItem(
            id=f"{memory_type.value}_{uuid.uuid4()}",
            content=content,
            memory_type=memory_type,
            embedding=embedding,
            metadata=metadata or {},
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # 存储到对应的记忆管理器
        if memory_type in self.memory_managers:
            await self.memory_managers[memory_type].store(memory_item)
        
        return memory_item
    
    async def search_memory(
        self, 
        query: str, 
        memory_types: List[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """搜索记忆"""
        
        # 生成查询向量
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # 执行混合搜索
        results = await self.search_engine.hybrid_search(
            query=query,
            query_embedding=query_embedding,
            memory_types=memory_types or list(MemoryType),
            limit=limit
        )
        
        return results

class HybridSearchEngine:
    """混合搜索引擎"""
    
    def __init__(self):
        self.bm25_weight = 0.3
        self.vector_weight = 0.7
        self.rerank_model = None
    
    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        memory_types: List[MemoryType],
        limit: int = 10
    ) -> List[MemoryItem]:
        """执行混合搜索"""
        
        # BM25文本搜索
        bm25_results = await self._bm25_search(query, memory_types, limit * 2)
        
        # 向量相似度搜索
        vector_results = await self._vector_search(query_embedding, memory_types, limit * 2)
        
        # 结果融合和重排序
        merged_results = self._merge_and_rerank(bm25_results, vector_results, limit)
        
        return merged_results
    
    async def _bm25_search(
        self, 
        query: str, 
        memory_types: List[MemoryType], 
        limit: int
    ) -> List[MemoryItem]:
        """BM25文本搜索"""
        # 实现BM25搜索逻辑
        # 这里应该调用PostgreSQL的全文搜索功能
        pass
    
    async def _vector_search(
        self, 
        query_embedding: List[float], 
        memory_types: List[MemoryType], 
        limit: int
    ) -> List[MemoryItem]:
        """向量相似度搜索"""
        # 实现向量搜索逻辑
        # 这里应该调用pgvector的相似度搜索功能
        pass
    
    def _merge_and_rerank(
        self, 
        bm25_results: List[MemoryItem], 
        vector_results: List[MemoryItem], 
        limit: int
    ) -> List[MemoryItem]:
        """合并和重排序搜索结果"""
        
        # 创建结果字典，避免重复
        result_dict = {}
        
        # 添加BM25结果
        for i, item in enumerate(bm25_results):
            bm25_score = (len(bm25_results) - i) / len(bm25_results)
            result_dict[item.id] = {
                'item': item,
                'bm25_score': bm25_score,
                'vector_score': 0.0
            }
        
        # 添加向量搜索结果
        for i, item in enumerate(vector_results):
            vector_score = (len(vector_results) - i) / len(vector_results)
            if item.id in result_dict:
                result_dict[item.id]['vector_score'] = vector_score
            else:
                result_dict[item.id] = {
                    'item': item,
                    'bm25_score': 0.0,
                    'vector_score': vector_score
                }
        
        # 计算综合得分并排序
        for result in result_dict.values():
            result['final_score'] = (
                result['bm25_score'] * self.bm25_weight + 
                result['vector_score'] * self.vector_weight
            )
            result['item'].relevance_score = result['final_score']
        
        # 按综合得分排序
        sorted_results = sorted(
            result_dict.values(), 
            key=lambda x: x['final_score'], 
            reverse=True
        )
        
        return [result['item'] for result in sorted_results[:limit]]
```

### 🔗 集成方案设计

#### 1. LLM集成架构
```python
# LLM集成架构设计
from typing import Protocol, Dict, Any, List, Optional
from abc import ABC, abstractmethod

class LLMProvider(Protocol):
    """LLM提供商协议"""
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """生成文本"""
        ...
    
    async def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        ...
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入"""
        ...

class LLMIntegrationArchitecture:
    """LLM集成架构"""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = None
        self.fallback_providers = []
        self.load_balancer = LLMLoadBalancer()
    
    def register_provider(self, name: str, provider: LLMProvider, is_default: bool = False):
        """注册LLM提供商"""
        self.providers[name] = provider
        if is_default:
            self.default_provider = name
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        provider: str = None,
        **kwargs
    ) -> str:
        """生成文本（带故障转移）"""
        
        target_provider = provider or self.default_provider
        
        try:
            return await self.providers[target_provider].generate(messages, **kwargs)
        except Exception as e:
            # 故障转移到备用提供商
            for fallback in self.fallback_providers:
                try:
                    return await self.providers[fallback].generate(messages, **kwargs)
                except Exception:
                    continue
            
            raise e

class OpenAIProvider:
    """OpenAI提供商实现"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成文本"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    async def generate_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式生成文本"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

class AnthropicProvider:
    """Anthropic提供商实现"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成文本"""
        # 转换消息格式
        anthropic_messages = self._convert_messages(messages)
        
        response = await self.client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            **kwargs
        )
        return response.content[0].text
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """转换消息格式以适配Anthropic API"""
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                # Anthropic将system消息合并到第一个user消息中
                continue
            converted.append(msg)
        return converted
```

#### 2. MCP协议集成
```python
# MCP协议集成架构
from typing import Dict, Any, List, Optional, Callable
import json
import asyncio

class MCPProtocolArchitecture:
    """MCP协议集成架构"""
    
    def __init__(self):
        self.servers = {}
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.event_handlers = {}
    
    async def register_server(self, server_name: str, server_config: Dict[str, Any]):
        """注册MCP服务器"""
        server = MCPServer(server_name, server_config)
        await server.initialize()
        
        self.servers[server_name] = server
        
        # 注册服务器的工具、资源和提示
        await self._register_server_capabilities(server_name, server)
    
    async def _register_server_capabilities(self, server_name: str, server: 'MCPServer'):
        """注册服务器能力"""
        
        # 注册工具
        tools = await server.list_tools()
        for tool in tools:
            tool_key = f"{server_name}.{tool['name']}"
            self.tools[tool_key] = {
                'server': server_name,
                'tool': tool,
                'handler': server.call_tool
            }
        
        # 注册资源
        resources = await server.list_resources()
        for resource in resources:
            resource_key = f"{server_name}.{resource['uri']}"
            self.resources[resource_key] = {
                'server': server_name,
                'resource': resource,
                'handler': server.read_resource
            }
        
        # 注册提示
        prompts = await server.list_prompts()
        for prompt in prompts:
            prompt_key = f"{server_name}.{prompt['name']}"
            self.prompts[prompt_key] = {
                'server': server_name,
                'prompt': prompt,
                'handler': server.get_prompt
            }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用MCP工具"""
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool_info = self.tools[tool_name]
        server = self.servers[tool_info['server']]
        
        return await server.call_tool(tool_info['tool']['name'], arguments)
    
    async def read_resource(self, resource_uri: str) -> Any:
        """读取MCP资源"""
        if resource_uri not in self.resources:
            raise ValueError(f"资源不存在: {resource_uri}")
        
        resource_info = self.resources[resource_uri]
        server = self.servers[resource_info['server']]
        
        return await server.read_resource(resource_info['resource']['uri'])
    
    def find_tools_by_capability(self, capability: str) -> List[str]:
        """根据能力查找工具"""
        matching_tools = []
        
        for tool_name, tool_info in self.tools.items():
            tool_description = tool_info['tool'].get('description', '').lower()
            if capability.lower() in tool_description:
                matching_tools.append(tool_name)
        
        return matching_tools

class MCPServer:
    """MCP服务器客户端"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.capabilities = {}
        self.session_id = None
    
    async def initialize(self):
        """初始化MCP服务器连接"""
        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "MIRIX",
                    "version": "0.1.4"
                }
            }
        }
        
        response = await self._send_request(init_request)
        self.capabilities = response.get("result", {}).get("capabilities", {})
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出可用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        return response.get("result")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出可用资源"""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list"
        }
        
        response = await self._send_request(request)
        return response.get("result", {}).get("resources", [])
    
    async def read_resource(self, resource_uri: str) -> Any:
        """读取资源"""
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            }
        }
        
        response = await self._send_request(request)
        return response.get("result")
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送MCP请求"""
        # 这里应该实现实际的网络通信
        # 可以是HTTP、WebSocket或其他协议
        
        # 模拟响应
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {}
        }
```

---

## 第三层：实施指导

### 🚀 部署架构实施

#### 1. Docker容器化部署
```yaml
# docker-compose.yml - 完整部署配置
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: pgvector/pgvector:pg16
    container_name: mirix-postgres
    environment:
      POSTGRES_DB: mirix
      POSTGRES_USER: mirix_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - mirix-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mirix_user -d mirix"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: mirix-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - mirix-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # MIRIX后端服务
  mirix-backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: mirix-backend
    environment:
      # 数据库配置
      DATABASE_URL: postgresql://mirix_user:${POSTGRES_PASSWORD}@postgres:5432/mirix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      
      # LLM配置
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      
      # 服务配置
      HOST: 0.0.0.0
      PORT: 47283
      DEBUG: false
      LOG_LEVEL: INFO
      
      # 安全配置
      SECRET_KEY: ${SECRET_KEY}
      API_KEY: ${API_KEY}
      
      # MCP配置
      MCP_SSE_URL: http://mcp-sse-service:8080
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./config:/app/config
    ports:
      - "47283:47283"
    networks:
      - mirix-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:47283/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # MCP SSE服务
  mcp-sse-service:
    build:
      context: ./mcp_sse_service
      dockerfile: Dockerfile
    container_name: mirix-mcp-sse
    environment:
      HOST: 0.0.0.0
      PORT: 8080
      DEBUG: false
      LOG_LEVEL: INFO
      MIRIX_BACKEND_URL: http://mirix-backend:47283
      ALLOWED_ORIGINS: "*"
      MCP_API_KEY: ${MCP_API_KEY}
    ports:
      - "8080:8080"
    networks:
      - mirix-network
    depends_on:
      - mirix-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: mirix-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - mirix-network
    depends_on:
      - mirix-backend
      - mcp-sse-service
    restart: unless-stopped

  # 监控服务
  prometheus:
    image: prom/prometheus:latest
    container_name: mirix-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - mirix-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mirix-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    networks:
      - mirix-network
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  mirix-network:
    driver: bridge
```

#### 2. Dockerfile优化配置
```dockerfile
# Dockerfile - 多阶段构建
FROM python:3.11-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-dev.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 开发阶段
FROM base as development

RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 47283

CMD ["python", "-m", "uvicorn", "mirix.server.fastapi_server:app", "--host", "0.0.0.0", "--port", "47283", "--reload"]

# 生产阶段
FROM base as production

# 创建非root用户
RUN useradd --create-home --shell /bin/bash mirix

# 复制应用代码
COPY --chown=mirix:mirix . .

# 创建必要目录
RUN mkdir -p /app/logs /app/uploads /app/config && \
    chown -R mirix:mirix /app

# 切换到非root用户
USER mirix

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:47283/health || exit 1

EXPOSE 47283

CMD ["python", "-m", "uvicorn", "mirix.server.fastapi_server:app", "--host", "0.0.0.0", "--port", "47283", "--workers", "4"]
```

#### 3. 环境配置管理
```bash
# .env.example - 环境变量模板
# 数据库配置
POSTGRES_PASSWORD=your_postgres_password
REDIS_PASSWORD=your_redis_password
DATABASE_URL=postgresql://mirix_user:your_postgres_password@localhost:5432/mirix

# LLM API密钥
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 服务配置
SECRET_KEY=your_secret_key_here
API_KEY=your_api_key_here
MCP_API_KEY=your_mcp_api_key

# 监控配置
GRAFANA_PASSWORD=your_grafana_password

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 性能配置
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=30
```

```python
# config/settings.py - 配置管理
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=47283, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    workers: int = Field(default=4, env="WORKERS")
    
    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # LLM配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    
    # 安全配置
    secret_key: str = Field(..., env="SECRET_KEY")
    api_key: Optional[str] = Field(None, env="API_KEY")
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    
    # MCP配置
    mcp_sse_url: str = Field(default="http://localhost:8080", env="MCP_SSE_URL")
    mcp_api_key: Optional[str] = Field(None, env="MCP_API_KEY")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # 性能配置
    max_connections: int = Field(default=100, env="MAX_CONNECTIONS")
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    request_timeout: int = Field(default=60, env="REQUEST_TIMEOUT")
    
    # 缓存配置
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 全局配置实例
settings = Settings()
```

#### 4. 数据库初始化脚本
```sql
-- init-scripts/01-init-database.sql
-- 创建数据库和用户
CREATE DATABASE mirix;
CREATE USER mirix_user WITH PASSWORD 'your_postgres_password';
GRANT ALL PRIVILEGES ON DATABASE mirix TO mirix_user;

-- 切换到mirix数据库
\c mirix;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建全文搜索配置
CREATE TEXT SEARCH CONFIGURATION chinese (COPY = simple);

-- 设置数据库参数
ALTER DATABASE mirix SET timezone TO 'UTC';
ALTER DATABASE mirix SET default_text_search_config TO 'chinese';

-- 创建基础表结构
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    llm_config JSONB NOT NULL,
    memory_config JSONB,
    system_prompt TEXT,
    persona TEXT,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_created_at ON agents(created_at);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 🔧 开发环境配置

#### 1. 本地开发环境搭建
```bash
#!/bin/bash
# scripts/setup-dev.sh - 开发环境搭建脚本

set -e

echo "🚀 开始设置MIRIX开发环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.11"

if [[ $(echo "$python_version $required_version" | tr ' ' '\n' | sort -V | head -n1) != "$required_version" ]]; then
    echo "❌ Python版本需要 >= $required_version，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装Python依赖..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker检查通过"

# 复制环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️ 请编辑 .env 文件，填入正确的配置值"
fi

# 启动数据库服务
echo "🗄️ 启动数据库服务..."
docker-compose up -d postgres redis

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
python -m alembic upgrade head

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p logs uploads config

# 安装pre-commit钩子
echo "🔧 安装pre-commit钩子..."
pre-commit install

echo "🎉 开发环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件，填入API密钥等配置"
echo "2. 运行 'python -m uvicorn mirix.server.fastapi_server:app --reload' 启动开发服务器"
echo "3. 访问 http://localhost:47283/docs 查看API文档"
echo ""
echo "🛠️ 常用开发命令："
echo "- 启动开发服务器: make dev"
echo "- 运行测试: make test"
echo "- 代码格式化: make format"
echo "- 类型检查: make typecheck"
```

#### 2. Makefile开发工具
```makefile
# Makefile - 开发工具命令
.PHONY: help dev test format typecheck lint clean build docker-build docker-run

# 默认目标
help:
	@echo "MIRIX开发工具命令："
	@echo "  dev          - 启动开发服务器"
	@echo "  test         - 运行测试"
	@echo "  format       - 代码格式化"
	@echo "  typecheck    - 类型检查"
	@echo "  lint         - 代码检查"
	@echo "  clean        - 清理临时文件"
	@echo "  build        - 构建应用"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 运行Docker容器"

# 启动开发服务器
dev:
	@echo "🚀 启动开发服务器..."
	python -m uvicorn mirix.server.fastapi_server:app --reload --host 0.0.0.0 --port 47283

# 运行测试
test:
	@echo "🧪 运行测试..."
	python -m pytest tests/ -v --cov=mirix --cov-report=html --cov-report=term

# 代码格式化
format:
	@echo "🎨 代码格式化..."
	black mirix/ tests/
	isort mirix/ tests/

# 类型检查
typecheck:
	@echo "🔍 类型检查..."
	mypy mirix/

# 代码检查
lint:
	@echo "🔍 代码检查..."
	flake8 mirix/ tests/
	pylint mirix/

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

# 构建应用
build:
	@echo "🏗️ 构建应用..."
	python -m build

# 构建Docker镜像
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t mirix:latest .

# 运行Docker容器
docker-run:
	@echo "🐳 运行Docker容器..."
	docker-compose up -d

# 停止Docker容器
docker-stop:
	@echo "🛑 停止Docker容器..."
	docker-compose down

# 数据库迁移
migrate:
	@echo "🔄 运行数据库迁移..."
	python -m alembic upgrade head

# 创建新的数据库迁移
migration:
	@echo "📝 创建数据库迁移..."
	python -m alembic revision --autogenerate -m "$(MSG)"

# 安装依赖
install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# 更新依赖
update:
	@echo "⬆️ 更新依赖..."
	pip-compile requirements.in
	pip-compile requirements-dev.in
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
```

---

## 📊 监控和运维

### 性能监控配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'mirix-backend'
    static_configs:
      - targets: ['mirix-backend:47283']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'mcp-sse-service'
    static_configs:
      - targets: ['mcp-sse-service:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### 日志管理配置
```python
# config/logging.py
import logging
import logging.config
from typing import Dict, Any

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/mirix.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": "logs/mirix_error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "mirix": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

def setup_logging():
    """设置日志配置"""
    logging.config.dictConfig(LOGGING_CONFIG)
```

### 安全配置
```python
# config/security.py
from typing import List, Optional
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta

class SecurityConfig:
    """安全配置管理"""
    
    def __init__(self):
        self.api_key_length = 32
        self.session_timeout = 3600  # 1小时
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15分钟
        
        # 密码策略
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special_chars = True
    
    def generate_api_key(self) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(self.api_key_length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """密码哈希"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )
        
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)
    
    def validate_password_strength(self, password: str) -> List[str]:
        """验证密码强度"""
        errors = []
        
        if len(password) < self.min_password_length:
            errors.append(f"密码长度至少{self.min_password_length}位")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("密码必须包含大写字母")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("密码必须包含小写字母")
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            errors.append("密码必须包含数字")
        
        if self.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("密码必须包含特殊字符")
        
        return errors

# 全局安全配置
security_config = SecurityConfig()
```

---

## 🚨 故障排查和解决方案

### 常见问题诊断
```python
# utils/diagnostics.py
import asyncio
import psutil
import logging
from typing import Dict, Any, List
from datetime import datetime

class SystemDiagnostics:
    """系统诊断工具"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """运行完整系统诊断"""
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": await self._check_system_resources(),
            "database": await self._check_database_connection(),
            "redis": await self._check_redis_connection(),
            "llm": await self._check_llm_services(),
            "memory": await self._check_memory_system(),
            "agents": await self._check_agent_system(),
        }
        
        return diagnostics
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
        }
    
    async def _check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 这里应该实际测试数据库连接
            return {
                "status": "healthy",
                "response_time_ms": 50,
                "active_connections": 10,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def _check_redis_connection(self) -> Dict[str, Any]:
        """检查Redis连接"""
        try:
            # 这里应该实际测试Redis连接
            return {
                "status": "healthy",
                "response_time_ms": 5,
                "memory_usage": "50MB",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def _check_llm_services(self) -> Dict[str, Any]:
        """检查LLM服务"""
        try:
            # 这里应该实际测试LLM服务
            return {
                "openai": {"status": "healthy", "response_time_ms": 1500},
                "anthropic": {"status": "healthy", "response_time_ms": 1200},
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    async def collect_metrics(self):
        """收集性能指标"""
        self.metrics.update({
            "timestamp": datetime.utcnow().isoformat(),
            "response_times": await self._collect_response_times(),
            "throughput": await self._collect_throughput(),
            "error_rates": await self._collect_error_rates(),
            "resource_usage": await self._collect_resource_usage(),
        })
    
    async def check_alerts(self):
        """检查告警条件"""
        # 响应时间告警
        avg_response_time = self.metrics.get("response_times", {}).get("average", 0)
        if avg_response_time > 5000:  # 5秒
            self.alerts.append({
                "type": "high_response_time",
                "message": f"平均响应时间过高: {avg_response_time}ms",
                "severity": "warning",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # 错误率告警
        error_rate = self.metrics.get("error_rates", {}).get("total", 0)
        if error_rate > 0.05:  # 5%
            self.alerts.append({
                "type": "high_error_rate",
                "message": f"错误率过高: {error_rate*100:.2f}%",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat(),
            })
```

---

## 📈 性能优化策略

### 数据库优化
```sql
-- 性能优化SQL脚本
-- 创建复合索引
CREATE INDEX CONCURRENTLY idx_messages_agent_created 
ON messages(agent_id, created_at DESC) 
WHERE is_deleted = FALSE;

-- 创建部分索引
CREATE INDEX CONCURRENTLY idx_active_agents 
ON agents(user_id, agent_type) 
WHERE is_deleted = FALSE;

-- 创建向量索引
CREATE INDEX CONCURRENTLY idx_memory_embedding 
ON memory_items USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 创建全文搜索索引
CREATE INDEX CONCURRENTLY idx_memory_content_fts 
ON memory_items USING gin(to_tsvector('chinese', content));

-- 分区表设置（按时间分区）
CREATE TABLE messages_y2024m01 PARTITION OF messages 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 定期维护脚本
-- 更新表统计信息
ANALYZE;

-- 重建索引
REINDEX INDEX CONCURRENTLY idx_messages_agent_created;

-- 清理无用数据
DELETE FROM messages 
WHERE is_deleted = TRUE 
AND updated_at < NOW() - INTERVAL '30 days';
```

### 缓存策略
```python
# utils/cache.py
import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1小时
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
            
            # 尝试JSON解析，失败则使用pickle
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return pickle.loads(value)
        except Exception:
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存"""
        try:
            # 尝试JSON序列化，失败则使用pickle
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            ttl_seconds = ttl or self.default_ttl
            if isinstance(ttl_seconds, timedelta):
                ttl_seconds = int(ttl_seconds.total_seconds())
            
            return await self.redis.setex(key, ttl_seconds, serialized_value)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(await self.redis.delete(key))
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False
    
    def cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

# 缓存装饰器
def cached(ttl: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()  # 获取缓存管理器实例
            
            # 生成缓存键
            cache_key = cache_manager.cache_key(
                key_prefix or func.__name__,
                *args,
                **sorted(kwargs.items())
            )
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
```

---

## 🔄 持续集成和部署

### CI/CD配置
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: mirix_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/mirix_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        python -m pytest tests/ -v --cov=mirix --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Run type checking
      run: mypy mirix/
    
    - name: Run linting
      run: |
        flake8 mirix/ tests/
        pylint mirix/

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          mirix/mirix:latest
          mirix/mirix:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "部署到生产环境"
        # 这里添加实际的部署脚本
```

---

## 📚 总结

MIRIX系统架构设计文档提供了完整的三层知识体系：

1. **第一层 - 整体架构大纲**：系统全景图、核心设计原则、技术栈选型、数据流架构
2. **第二层 - 技术设计支持**：分层架构设计、集成方案设计、LLM集成、MCP协议集成
3. **第三层 - 实施指导**：部署架构、开发环境配置、监控运维、故障排查、性能优化

该架构设计确保了MIRIX系统的：
- **可扩展性**：支持水平和垂直扩展
- **可维护性**：模块化设计，便于维护和升级
- **高性能**：异步处理、缓存策略、数据库优化
- **安全性**：多层安全防护、数据加密、访问控制
- **可观测性**：完整的监控、日志、告警体系

通过这个架构设计，开发团队可以：
- 理解系统的整体设计思路和技术选型
- 获得具体的技术实施指导
- 掌握系统的部署、监控和运维方法
- 解决常见的技术问题和性能优化