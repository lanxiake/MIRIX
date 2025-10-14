# MIRIX数据存储架构分析

## 1. 概述

MIRIX系统采用多层记忆架构，通过SQLAlchemy ORM管理数据持久化。本文档详细分析核心记忆表的结构、关系和存储机制。

### 技术栈
- **主数据库**: PostgreSQL (生产) / SQLite (开发)
- **向量存储**: pgvector扩展 (PostgreSQL) / CommonVector (SQLite)
- **ORM框架**: SQLAlchemy 2.x
- **嵌入模型**: 可配置的embedding模型
- **全文搜索**: PostgreSQL原生FTS / BM25算法

## 2. 核心记忆表详细分析

### 2.1 情景记忆表 (episodic_memory)

**表名**: `episodic_memory`
**用途**: 存储时间序列的用户活动和事件记忆

#### 核心字段结构
```sql
CREATE TABLE episodic_memory (
    id VARCHAR PRIMARY KEY,                    -- 唯一标识符
    organization_id VARCHAR NOT NULL,         -- 组织ID
    user_id VARCHAR NOT NULL,                 -- 用户ID
    occurred_at TIMESTAMP NOT NULL,           -- 事件发生时间
    last_modify JSON NOT NULL,                -- 最后修改信息
    actor VARCHAR NOT NULL,                   -- 事件参与者
    event_type VARCHAR NOT NULL,              -- 事件类型
    summary VARCHAR NOT NULL,                 -- 事件摘要
    details TEXT NOT NULL,                    -- 详细描述
    tree_path JSON NOT NULL,                  -- 分层分类路径
    metadata_ JSON,                           -- 扩展元数据
    embedding_config JSON,                    -- 嵌入配置
    details_embedding VECTOR(4096),           -- 详情向量
    summary_embedding VECTOR(4096),           -- 摘要向量
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **时间维度**: `occurred_at`字段支持时间范围查询
- **层次分类**: `tree_path`支持如`["个人", "工作", "会议"]`的分层组织
- **双向量索引**: 分别对摘要和详情建立向量索引
- **全文搜索**: 支持PostgreSQL原生FTS和BM25搜索

#### 查询优化
```sql
-- 时间范围索引
CREATE INDEX idx_episodic_occurred_at ON episodic_memory(occurred_at, user_id);
-- 向量相似度索引
CREATE INDEX idx_episodic_details_embedding ON episodic_memory 
USING ivfflat (details_embedding vector_cosine_ops);
```

### 2.2 语义记忆表 (semantic_memory)

**表名**: `semantic_memory`
**用途**: 存储概念性知识和理解

#### 核心字段结构
```sql
CREATE TABLE semantic_memory (
    id VARCHAR PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,                    -- 概念名称
    summary TEXT NOT NULL,                    -- 概念摘要
    details TEXT NOT NULL,                    -- 详细说明
    source VARCHAR,                           -- 信息来源
    tree_path JSON NOT NULL,                  -- 分层分类
    last_modify JSON NOT NULL,
    metadata_ JSON,
    embedding_config JSON,
    details_embedding VECTOR(4096),           -- 详情向量
    name_embedding VECTOR(4096),              -- 名称向量
    summary_embedding VECTOR(4096),           -- 摘要向量
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **三重向量索引**: 对名称、摘要、详情分别建立向量索引
- **概念关联**: 通过`tree_path`建立概念间的层次关系
- **来源追踪**: `source`字段记录知识来源

### 2.3 程序记忆表 (procedural_memory)

**表名**: `procedural_memory`
**用途**: 存储操作步骤和工作流程

#### 核心字段结构
```sql
CREATE TABLE procedural_memory (
    id VARCHAR PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    entry_type VARCHAR NOT NULL,              -- 条目类型(workflow/guide/script)
    summary VARCHAR NOT NULL,                 -- 过程描述
    steps JSON NOT NULL,                      -- 步骤列表
    tree_path JSON NOT NULL,                  -- 分层分类
    last_modify JSON NOT NULL,
    metadata_ JSON,
    embedding_config JSON,
    summary_embedding VECTOR(4096),           -- 摘要向量
    steps_embedding VECTOR(4096),             -- 步骤向量
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **结构化步骤**: `steps`字段存储JSON格式的操作序列
- **类型分类**: `entry_type`区分工作流、指南、脚本等类型
- **双向量索引**: 对摘要和步骤分别建立向量索引

### 2.4 资源记忆表 (resource_memory)

**表名**: `resource_memory`
**用途**: 存储文档和文件资源

#### 核心字段结构
```sql
CREATE TABLE resource_memory (
    id VARCHAR PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,                   -- 资源标题
    summary VARCHAR NOT NULL,                 -- 资源摘要
    resource_type VARCHAR NOT NULL,           -- 资源类型
    content TEXT NOT NULL,                    -- 完整内容
    tree_path JSON NOT NULL,                  -- 分层分类
    last_modify JSON NOT NULL,
    metadata_ JSON,
    embedding_config JSON,
    summary_embedding VECTOR(4096),           -- 摘要向量
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **完整内容存储**: `content`字段存储文档的完整文本内容
- **类型识别**: `resource_type`支持文档、图片、代码等多种类型
- **单向量索引**: 主要基于摘要进行向量搜索

### 2.5 知识库表 (knowledge_vault)

**表名**: `knowledge_vault`
**用途**: 存储结构化事实数据和凭证

#### 核心字段结构
```sql
CREATE TABLE knowledge_vault (
    id VARCHAR PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    entry_type VARCHAR NOT NULL,              -- 条目类型
    source VARCHAR NOT NULL,                  -- 数据来源
    sensitivity VARCHAR NOT NULL,             -- 敏感级别
    secret_value TEXT NOT NULL,               -- 加密存储值
    caption VARCHAR,                          -- 标题说明
    tree_path JSON,                           -- 分层分类
    metadata_ JSON,
    embedding_config JSON,
    caption_embedding VECTOR(4096),           -- 标题向量
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **安全存储**: `secret_value`字段加密存储敏感信息
- **敏感级别**: `sensitivity`字段控制访问权限
- **单向量索引**: 基于标题建立向量索引

### 2.6 核心记忆块表 (blocks)

**表名**: `blocks`
**用途**: 存储用户画像和助手人格

#### 核心字段结构
```sql
CREATE TABLE blocks (
    id VARCHAR PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    template_name VARCHAR,
    description TEXT,
    label VARCHAR NOT NULL,                   -- 块标识(human/persona)
    is_template BOOLEAN DEFAULT FALSE,
    value TEXT NOT NULL,                      -- 块内容
    char_limit INTEGER DEFAULT 2000,         -- 字符限制
    metadata_ JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### 关键特性
- **双块结构**: Human Block存储用户信息，Persona Block存储助手人格
- **字符限制**: `char_limit`控制块大小，防止过度膨胀
- **模板支持**: `is_template`支持预定义模板

## 3. 数据关系和架构

### 3.1 组织层次结构
```
Organizations (组织)
    ├── Users (用户)
    │   ├── Episodic Memory (情景记忆)
    │   ├── Semantic Memory (语义记忆)
    │   ├── Procedural Memory (程序记忆)
    │   ├── Resource Memory (资源记忆)
    │   ├── Knowledge Vault (知识库)
    │   └── Blocks (核心记忆块)
    └── Agents (智能体)
        └── Messages (消息历史)
```

### 3.2 外键关系
所有记忆表通过以下外键与核心表关联：
- `organization_id` → `organizations.id`
- `user_id` → `users.id`

### 3.3 Mixin模式
使用SQLAlchemy Mixin实现代码复用：
- `OrganizationMixin`: 提供组织关联
- `UserMixin`: 提供用户关联
- 所有记忆表继承这些Mixin

## 4. 向量存储和搜索机制

### 4.1 向量维度配置
- **标准维度**: 4096 (支持最新embedding模型)
- **兼容维度**: 768 (支持传统模型)
- **动态调整**: 通过`MAX_EMBEDDING_DIM`常量配置

### 4.2 向量搜索策略
1. **嵌入搜索** (embedding): 基于语义相似度
2. **BM25搜索** (bm25): 基于关键词匹配
3. **字符串匹配** (string_match): 基于文本包含

### 4.3 数据库适配
```python
# PostgreSQL with pgvector
if settings.mirix_pg_uri_no_default:
    from pgvector.sqlalchemy import Vector
    details_embedding = mapped_column(Vector(MAX_EMBEDDING_DIM), nullable=True)
# SQLite with CommonVector
else:
    details_embedding = Column(CommonVector, nullable=True)
```

## 5. 性能优化和索引策略

### 5.1 核心索引
```sql
-- 组织和用户索引
CREATE INDEX idx_memory_organization_user ON {table_name}(organization_id, user_id);

-- 时间范围索引
CREATE INDEX idx_memory_created_at ON {table_name}(created_at, id);

-- 向量相似度索引
CREATE INDEX idx_memory_embedding ON {table_name} 
USING ivfflat (embedding vector_cosine_ops);

-- 全文搜索索引 (PostgreSQL)
CREATE INDEX idx_memory_fts ON {table_name} 
USING gin(to_tsvector('english', details));
```

### 5.2 查询优化
1. **分页查询**: 使用`LIMIT`和`OFFSET`
2. **向量预过滤**: 先按用户ID过滤再进行向量搜索
3. **索引提示**: 利用复合索引优化查询路径

### 5.3 存储优化
- **JSON压缩**: 大型JSON字段使用压缩存储
- **向量量化**: 在保持精度的前提下减少向量存储空间
- **软删除**: 使用`is_deleted`标记而非物理删除

## 6. 数据迁移和版本管理

### 6.1 Schema演进
- 使用Alembic管理数据库版本
- 向后兼容的字段添加
- 渐进式数据迁移

### 6.2 向量迁移
```python
# 向量维度升级迁移示例
def upgrade_vector_dimension():
    # 1. 添加新的向量字段
    # 2. 重新计算现有数据的向量
    # 3. 删除旧的向量字段
    # 4. 重建向量索引
```

## 7. 安全性和隐私保护

### 7.1 数据加密
- **传输加密**: TLS 1.3
- **存储加密**: 数据库级别加密
- **字段加密**: 敏感字段单独加密

### 7.2 访问控制
```python
# 用户隔离查询示例
def get_user_memories(user_id: str):
    return session.query(EpisodicEvent).filter(
        EpisodicEvent.user_id == user_id,
        EpisodicEvent.is_deleted == False
    )
```

### 7.3 隐私合规
- **数据最小化**: 只存储必要信息
- **用户控制**: 支持数据导出和删除
- **审计日志**: 记录敏感操作

## 8. 故障排除和维护指南

### 8.1 常见问题
1. **向量维度不匹配**: 检查embedding配置
2. **搜索性能下降**: 重建向量索引
3. **内存占用过高**: 优化查询批次大小

### 8.2 监控指标
- 查询响应时间
- 向量索引效率
- 存储空间使用
- 并发连接数

### 8.3 维护任务
```sql
-- 定期清理软删除数据
DELETE FROM episodic_memory WHERE is_deleted = true AND updated_at < NOW() - INTERVAL '30 days';

-- 重建向量索引
REINDEX INDEX idx_memory_embedding;

-- 更新表统计信息
ANALYZE episodic_memory;
```

## 9. 扩展性考虑

### 9.1 水平扩展
- 按组织ID分片
- 读写分离
- 缓存层优化

### 9.2 垂直扩展
- 内存优化
- SSD存储
- CPU密集型向量计算

## 10. 总结

MIRIX的数据存储架构通过多层记忆模型实现了复杂的知识管理需求：

- **六大记忆类型**覆盖了从事实存储到概念理解的完整认知谱系
- **向量+全文搜索**的混合检索策略保证了搜索的准确性和性能
- **分层组织结构**支持大规模多租户部署
- **灵活的Schema设计**为未来功能扩展预留了空间

该架构在保证数据一致性的同时，通过合理的索引策略和缓存机制实现了良好的查询性能，为MIRIX系统的智能记忆功能提供了坚实的数据基础。
