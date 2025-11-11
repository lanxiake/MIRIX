-- ============================================================================
-- MIRIX Database Migration - Add Missing Message Columns
-- ============================================================================
-- 此脚本用于修复现有数据库中 messages 表缺少的列
-- 生成时间: 2025-11-11
-- 问题: messages 表缺少 content, step_id, otid, tool_returns, group_id, sender_id 列
-- ============================================================================

-- 添加 content 列（JSON类型，用于存储消息内容部分）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'content'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN content json;
        RAISE NOTICE 'Added column: content';
    ELSE
        RAISE NOTICE 'Column content already exists, skipping';
    END IF;
END $$;

-- 添加 step_id 列（关联到 steps 表）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'step_id'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN step_id character varying;
        RAISE NOTICE 'Added column: step_id';
    ELSE
        RAISE NOTICE 'Column step_id already exists, skipping';
    END IF;
END $$;

-- 添加 otid 列（离线线程ID）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'otid'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN otid character varying;
        RAISE NOTICE 'Added column: otid';
    ELSE
        RAISE NOTICE 'Column otid already exists, skipping';
    END IF;
END $$;

-- 添加 tool_returns 列（工具返回值）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'tool_returns'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN tool_returns json;
        RAISE NOTICE 'Added column: tool_returns';
    ELSE
        RAISE NOTICE 'Column tool_returns already exists, skipping';
    END IF;
END $$;

-- 添加 group_id 列（多代理组ID）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'group_id'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN group_id character varying;
        RAISE NOTICE 'Added column: group_id';
    ELSE
        RAISE NOTICE 'Column group_id already exists, skipping';
    END IF;
END $$;

-- 添加 sender_id 列（发送者ID）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'sender_id'
    ) THEN
        ALTER TABLE public.messages ADD COLUMN sender_id character varying;
        RAISE NOTICE 'Added column: sender_id';
    ELSE
        RAISE NOTICE 'Column sender_id already exists, skipping';
    END IF;
END $$;

-- 验证所有列是否已添加
DO $$
DECLARE
    missing_columns text[] := ARRAY[]::text[];
    col text;
BEGIN
    RAISE NOTICE 'Verifying all columns exist...';

    FOREACH col IN ARRAY ARRAY['content', 'step_id', 'otid', 'tool_returns', 'group_id', 'sender_id']
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'messages' AND column_name = col
        ) THEN
            missing_columns := array_append(missing_columns, col);
        END IF;
    END LOOP;

    IF array_length(missing_columns, 1) > 0 THEN
        RAISE WARNING 'Still missing columns: %', array_to_string(missing_columns, ', ');
    ELSE
        RAISE NOTICE 'All required columns have been successfully added!';
    END IF;
END $$;

-- 显示 messages 表的当前结构
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'messages'
ORDER BY ordinal_position;
