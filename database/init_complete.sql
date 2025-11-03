-- ============================================================================
-- MIRIX Complete Database Initialization Script
-- ============================================================================
-- 此脚本基于当前运行的数据库导出，包含完整的表结构
-- 生成时间: 2025-10-21
-- PostgreSQL 版本: 16.10 with pgvector extension
-- ============================================================================

-- 设置客户端编码和参数
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ============================================================================
-- 扩展 (Extensions)
-- ============================================================================

-- UUID 生成扩展
DO $$ 
BEGIN
    -- 尝试创建扩展
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        CREATE EXTENSION "uuid-ossp" WITH SCHEMA public;
        RAISE NOTICE 'Extension uuid-ossp created successfully';
    ELSE
        RAISE NOTICE 'Extension uuid-ossp already exists, skipping';
    END IF;
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE 'Extension uuid-ossp: % (may already exist in system)', SQLERRM;
END $$;

-- 为扩展添加注释（如果存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';
    END IF;
END $$;

-- 向量数据类型扩展 (用于embedding存储)
DO $$ 
BEGIN
    -- 尝试创建扩展
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE EXTENSION vector WITH SCHEMA public;
        RAISE NOTICE 'Extension vector created successfully';
    ELSE
        RAISE NOTICE 'Extension vector already exists, skipping';
    END IF;
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE 'Extension vector: % (may already exist in system)', SQLERRM;
END $$;

-- 为扩展添加注释（如果存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';
    END IF;
END $$;

-- ============================================================================
-- 自定义类型 (Custom Types)
-- ============================================================================

-- 沙箱类型枚举
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sandboxtype') THEN
        CREATE TYPE public.sandboxtype AS ENUM (
            'E2B',
            'LOCAL'
        );
        RAISE NOTICE 'Type sandboxtype created successfully';
    ELSE
        RAISE NOTICE 'Type sandboxtype already exists, skipping';
    END IF;
END $$;

-- ============================================================================
-- 表结构 (Tables)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 用户相关表
-- ----------------------------------------------------------------------------

-- 用户表
CREATE TABLE IF NOT EXISTS public.users (
    id character varying NOT NULL PRIMARY KEY,
    name character varying,
    status character varying,
    timezone character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.users IS '用户基础信息表';

-- 用户设置表
CREATE TABLE IF NOT EXISTS public.user_settings (
    user_id character varying NOT NULL PRIMARY KEY,
    llm_config json,
    embedding_config json,
    default_persona character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.user_settings IS '用户配置和偏好设置';

-- 组织表
CREATE TABLE IF NOT EXISTS public.organizations (
    id character varying NOT NULL PRIMARY KEY,
    name character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying
);

COMMENT ON TABLE public.organizations IS '组织/租户表';

-- ----------------------------------------------------------------------------
-- Agent 相关表
-- ----------------------------------------------------------------------------

-- Agent 主表
CREATE TABLE IF NOT EXISTS public.agents (
    id character varying NOT NULL PRIMARY KEY,
    agent_type character varying,
    name character varying,
    description character varying,
    system character varying,
    topic character varying,
    message_ids json,
    metadata_ json,
    llm_config json,
    embedding_config json,
    tool_rules json,
    mcp_tools json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.agents IS 'Agent 配置表';

-- Agent 标签关联表
CREATE TABLE IF NOT EXISTS public.agents_tags (
    agent_id character varying NOT NULL,
    tag character varying NOT NULL,
    PRIMARY KEY (agent_id, tag)
);

COMMENT ON TABLE public.agents_tags IS 'Agent 标签多对多关联';

-- Agent 环境变量表
CREATE TABLE IF NOT EXISTS public.agent_environment_variables (
    id character varying NOT NULL PRIMARY KEY,
    key character varying NOT NULL,
    value character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    agent_id character varying NOT NULL
);

COMMENT ON TABLE public.agent_environment_variables IS 'Agent 专用环境变量';

-- ----------------------------------------------------------------------------
-- 消息和通信相关表
-- ----------------------------------------------------------------------------

-- 消息表
CREATE TABLE IF NOT EXISTS public.messages (
    id character varying NOT NULL PRIMARY KEY,
    role character varying NOT NULL,
    name character varying,
    text character varying,
    model character varying,
    user_id character varying,
    agent_id character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    tool_calls json,
    tool_call_id character varying
);

COMMENT ON TABLE public.messages IS '对话消息记录';

-- Step 表（工作流步骤）
CREATE TABLE IF NOT EXISTS public.steps (
    id character varying NOT NULL PRIMARY KEY,
    message_id character varying NOT NULL,
    tool_calls json,
    completed_at timestamp without time zone,
    model character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.steps IS '消息处理步骤记录';

-- ----------------------------------------------------------------------------
-- Memory 系统表
-- ----------------------------------------------------------------------------

-- 情景记忆表 (Episodic Memory)
CREATE TABLE IF NOT EXISTS public.episodic_memory (
    id character varying NOT NULL PRIMARY KEY,
    occurred_at timestamp without time zone NOT NULL,
    last_modify json NOT NULL,
    actor character varying NOT NULL,
    event_type character varying NOT NULL,
    summary character varying NOT NULL,
    details character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    details_embedding public.vector(4096),
    summary_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);

COMMENT ON TABLE public.episodic_memory IS '情景记忆 - 存储具体事件和经历';

-- 语义记忆表 (Semantic Memory)
CREATE TABLE IF NOT EXISTS public.semantic_memory (
    id character varying NOT NULL PRIMARY KEY,
    category character varying NOT NULL,
    subcategory character varying,
    concept character varying NOT NULL,
    details character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    details_embedding public.vector(4096),
    concept_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);

COMMENT ON TABLE public.semantic_memory IS '语义记忆 - 存储概念和知识';

-- 程序记忆表 (Procedural Memory)
CREATE TABLE IF NOT EXISTS public.procedural_memory (
    id character varying NOT NULL PRIMARY KEY,
    category character varying NOT NULL,
    subcategory character varying,
    task character varying NOT NULL,
    steps character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    steps_embedding public.vector(4096),
    task_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);

COMMENT ON TABLE public.procedural_memory IS '程序记忆 - 存储技能和操作步骤';

-- 资源记忆表 (Resource Memory)
CREATE TABLE IF NOT EXISTS public.resource_memory (
    id character varying NOT NULL PRIMARY KEY,
    resource_type character varying NOT NULL,
    title character varying NOT NULL,
    content character varying NOT NULL,
    source character varying,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    content_embedding public.vector(4096),
    title_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);

COMMENT ON TABLE public.resource_memory IS '资源记忆 - 存储文档和资源';

-- 知识库表 (Knowledge Vault)
CREATE TABLE IF NOT EXISTS public.knowledge_vault (
    id character varying NOT NULL PRIMARY KEY,
    domain character varying NOT NULL,
    topic character varying NOT NULL,
    question character varying NOT NULL,
    answer character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    answer_embedding public.vector(4096),
    question_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);

COMMENT ON TABLE public.knowledge_vault IS '知识库 - 存储结构化知识';

-- ----------------------------------------------------------------------------
-- 文件管理表
-- ----------------------------------------------------------------------------

-- 文件表
CREATE TABLE IF NOT EXISTS public.files (
    id character varying NOT NULL PRIMARY KEY,
    user_id character varying,
    file_name character varying,
    file_path character varying,
    file_type character varying,
    file_size bigint,
    checksum character varying,
    metadata_ json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.files IS '文件元数据表';

-- 云文件映射表
CREATE TABLE IF NOT EXISTS public.cloud_file_mapping (
    id character varying NOT NULL PRIMARY KEY,
    cloud_file_id character varying NOT NULL,
    local_file_id character varying NOT NULL,
    status character varying NOT NULL,
    "timestamp" character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.cloud_file_mapping IS '云端和本地文件映射关系';

-- ----------------------------------------------------------------------------
-- 工具和集成相关表
-- ----------------------------------------------------------------------------

-- 工具表
CREATE TABLE IF NOT EXISTS public.tools (
    id character varying NOT NULL PRIMARY KEY,
    name character varying,
    tool_type character varying DEFAULT 'custom',
    return_char_limit integer,
    description character varying,
    tags json,
    source_type character varying DEFAULT 'json',
    json_schema json,
    source_code character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    module character varying,
    CONSTRAINT uix_name_organization UNIQUE (name, organization_id)
);

COMMENT ON TABLE public.tools IS '工具定义表';

-- 工具-Agent 关联表
CREATE TABLE IF NOT EXISTS public.tools_agents (
    agent_id character varying NOT NULL,
    tool_name character varying NOT NULL,
    tool_id character varying NOT NULL,
    PRIMARY KEY (agent_id, tool_id)
);

COMMENT ON TABLE public.tools_agents IS '工具和 Agent 多对多关联';

-- 提供商配置表
CREATE TABLE IF NOT EXISTS public.providers (
    id character varying NOT NULL PRIMARY KEY,
    user_id character varying,
    name character varying,
    base_url character varying,
    api_key character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.providers IS 'LLM 提供商配置';

-- ----------------------------------------------------------------------------
-- 沙箱和执行环境表
-- ----------------------------------------------------------------------------

-- 沙箱配置表
CREATE TABLE IF NOT EXISTS public.sandbox_configs (
    id character varying NOT NULL PRIMARY KEY,
    type public.sandboxtype NOT NULL,
    config json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);

COMMENT ON TABLE public.sandbox_configs IS '代码执行沙箱配置';

-- 沙箱环境变量表
CREATE TABLE IF NOT EXISTS public.sandbox_environment_variables (
    id character varying NOT NULL PRIMARY KEY,
    key character varying NOT NULL,
    value character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    sandbox_config_id character varying NOT NULL
);

COMMENT ON TABLE public.sandbox_environment_variables IS '沙箱专用环境变量';

-- ----------------------------------------------------------------------------
-- Block 系统表
-- ----------------------------------------------------------------------------

-- Block 表
CREATE TABLE IF NOT EXISTS public.block (
    id character varying NOT NULL PRIMARY KEY,
    template_name character varying,
    description character varying,
    label character varying NOT NULL,
    is_template boolean NOT NULL,
    value character varying NOT NULL,
    "limit" integer NOT NULL,
    metadata_ json,
    organization_id character varying,
    user_id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying
);

COMMENT ON TABLE public.block IS 'Block 配置和模板';

-- Block-Agent 关联表
CREATE TABLE IF NOT EXISTS public.blocks_agents (
    agent_id character varying NOT NULL,
    block_id character varying NOT NULL,
    block_label character varying NOT NULL,
    PRIMARY KEY (agent_id, block_id)
);

COMMENT ON TABLE public.blocks_agents IS 'Block 和 Agent 多对多关联';

-- ============================================================================
-- 索引 (Indexes)
-- ============================================================================

-- 用户索引
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_users_organization_id ON public.users(organization_id) WHERE NOT is_deleted;
    CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Users indexes: % (may not exist or already created)', SQLERRM;
END $$;

-- Agent 索引
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_agents_organization_id ON public.agents(organization_id) WHERE NOT is_deleted;
    CREATE INDEX IF NOT EXISTS idx_agents_type ON public.agents(agent_type) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Agents indexes: % (may not exist or already created)', SQLERRM;
END $$;

-- 消息索引
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id) WHERE NOT is_deleted;
    CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON public.messages(agent_id) WHERE NOT is_deleted;
    CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Messages indexes: % (may not exist or already created)', SQLERRM;
END $$;

-- Memory 表索引（包含向量索引）
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_episodic_user_id ON public.episodic_memory(user_id) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Episodic memory user_id index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_episodic_event_type ON public.episodic_memory(event_type) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Episodic memory event_type index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_semantic_user_id ON public.semantic_memory(user_id) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Semantic memory user_id index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_semantic_category ON public.semantic_memory(category) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Semantic memory category index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_procedural_user_id ON public.procedural_memory(user_id) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Procedural memory user_id index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_procedural_category ON public.procedural_memory(category) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Procedural memory category index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_resource_user_id ON public.resource_memory(user_id) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Resource memory user_id index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_resource_type ON public.resource_memory(resource_type) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Resource memory type index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON public.knowledge_vault(user_id) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Knowledge vault user_id index: % (may not exist or already created)', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON public.knowledge_vault(domain) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Knowledge vault domain index: % (may not exist or already created)', SQLERRM;
END $$;

-- 文件索引
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_files_user_id ON public.files(user_id) WHERE NOT is_deleted;
    CREATE INDEX IF NOT EXISTS idx_files_type ON public.files(file_type) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Files indexes: % (may not exist or already created)', SQLERRM;
END $$;

-- 工具索引
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_tools_source_type ON public.tools(source_type) WHERE NOT is_deleted;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Tools indexes: % (may not exist or already created)', SQLERRM;
END $$;

-- ============================================================================
-- 初始化数据 (Initial Data)
-- ============================================================================

-- 插入默认用户（如果不存在）
INSERT INTO public.users (id, name, status, timezone, created_at, updated_at, is_deleted, organization_id)
VALUES ('user-00000000-0000-4000-8000-000000000000', 'Default User', 'active', 'UTC', now(), now(), false, NULL)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE public.users IS '用户表 - 包含默认用户';

-- 插入默认组织（如果不存在）
INSERT INTO public.organizations (id, name, created_at, updated_at, is_deleted)
VALUES ('org-00000000-0000-4000-8000-000000000000', 'Default Organization', now(), now(), false)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 完成初始化
-- ============================================================================

-- 更新用户的组织关联
UPDATE public.users
SET organization_id = 'org-00000000-0000-4000-8000-000000000000'
WHERE id = 'user-00000000-0000-4000-8000-000000000000'
  AND organization_id IS NULL;

-- 显示完成信息
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'MIRIX Database Initialization Complete!';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Extensions: uuid-ossp, vector';
    RAISE NOTICE 'Tables: 22 tables created';
    RAISE NOTICE 'Default User ID: user-00000000-0000-4000-8000-000000000000';
    RAISE NOTICE 'Default Org ID: org-00000000-0000-4000-8000-000000000000';
    RAISE NOTICE '==============================================';
END $$;
