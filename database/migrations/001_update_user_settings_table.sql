-- ============================================================================
-- Migration: 更新 user_settings 表结构
-- ============================================================================
-- 说明: 将旧的 user_settings 表结构迁移到新的结构
-- 创建时间: 2025-10-23
-- ============================================================================

BEGIN;

-- 步骤 1: 创建临时表保存旧数据
CREATE TEMP TABLE user_settings_backup AS 
SELECT * FROM user_settings;

-- 步骤 2: 删除旧表
DROP TABLE IF EXISTS user_settings CASCADE;

-- 步骤 3: 创建新的 user_settings 表结构
CREATE TABLE public.user_settings (
    id character varying NOT NULL PRIMARY KEY,
    user_id character varying NOT NULL,
    chat_model character varying(100),
    memory_model character varying(100),
    timezone character varying(100),
    persona character varying(100),
    persona_text character varying,
    ui_preferences json DEFAULT '{}'::json,
    custom_settings json DEFAULT '{}'::json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    CONSTRAINT fk_user_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_settings_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- 添加注释
COMMENT ON TABLE public.user_settings IS '用户个性化设置表';
COMMENT ON COLUMN public.user_settings.id IS '设置记录唯一标识符';
COMMENT ON COLUMN public.user_settings.user_id IS '用户ID（外键）';
COMMENT ON COLUMN public.user_settings.chat_model IS '聊天模型名称';
COMMENT ON COLUMN public.user_settings.memory_model IS '记忆管理模型名称';
COMMENT ON COLUMN public.user_settings.timezone IS '用户时区';
COMMENT ON COLUMN public.user_settings.persona IS '角色名称';
COMMENT ON COLUMN public.user_settings.persona_text IS '自定义角色文本';
COMMENT ON COLUMN public.user_settings.ui_preferences IS '界面偏好设置（JSON）';
COMMENT ON COLUMN public.user_settings.custom_settings IS '自定义设置（JSON）';

-- 步骤 4: 创建索引
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON public.user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_organization_id ON public.user_settings(organization_id);

-- 步骤 5: 迁移旧数据（如果存在）
-- 从旧数据中提取模型配置并转换为新格式
INSERT INTO public.user_settings (
    id,
    user_id,
    chat_model,
    memory_model,
    timezone,
    persona,
    persona_text,
    ui_preferences,
    custom_settings,
    created_at,
    updated_at,
    is_deleted,
    _created_by_id,
    _last_updated_by_id,
    organization_id
)
SELECT
    gen_random_uuid()::character varying AS id,
    user_id,
    COALESCE(
        (llm_config->>'model')::character varying,
        'gpt-4o-mini'
    ) AS chat_model,
    COALESCE(
        (llm_config->>'model')::character varying,
        'gemini-2.5-flash-lite'
    ) AS memory_model,
    'UTC' AS timezone,
    COALESCE(default_persona, 'helpful_assistant') AS persona,
    NULL AS persona_text,
    '{}'::json AS ui_preferences,
    '{}'::json AS custom_settings,
    created_at,
    updated_at,
    is_deleted,
    _created_by_id,
    _last_updated_by_id,
    organization_id
FROM user_settings_backup
WHERE EXISTS (SELECT 1 FROM users WHERE id = user_settings_backup.user_id);

-- 步骤 6: 清理临时表
DROP TABLE IF EXISTS user_settings_backup;

COMMIT;

-- ============================================================================
-- 迁移完成
-- ============================================================================
RAISE NOTICE 'user_settings 表结构迁移完成';

