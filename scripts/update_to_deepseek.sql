-- ============================================================================
-- MIRIX 数据库更新脚本：将所有用户的模型配置更新为 DeepSeek
-- ============================================================================
-- 说明: 此脚本将更新所有用户设置中的 chat_model 和 memory_model 为 deepseek-chat
-- 执行方式:
--   1. Docker 环境: docker exec -i mirix-postgres psql -U mirix -d mirix < scripts/update_to_deepseek.sql
--   2. 本地环境: psql -U mirix -d mirix -f scripts/update_to_deepseek.sql
-- ============================================================================

-- 开始事务
BEGIN;

-- 显示当前状态
SELECT
    '更新前的用户设置' as status,
    user_id,
    chat_model,
    memory_model
FROM user_settings
WHERE is_deleted = false;

-- 更新所有用户的聊天模型和记忆模型为 deepseek-chat
UPDATE user_settings
SET
    chat_model = 'deepseek-chat',
    memory_model = 'deepseek-chat',
    updated_at = NOW()
WHERE is_deleted = false
  AND (chat_model != 'deepseek-chat' OR memory_model != 'deepseek-chat');

-- 显示更新后的状态
SELECT
    '更新后的用户设置' as status,
    user_id,
    chat_model,
    memory_model
FROM user_settings
WHERE is_deleted = false;

-- 显示更新统计
SELECT
    COUNT(*) as total_updated
FROM user_settings
WHERE is_deleted = false
  AND chat_model = 'deepseek-chat'
  AND memory_model = 'deepseek-chat';

-- 提交事务
COMMIT;

-- 完成提示
SELECT '数据库更新完成！所有用户的模型配置已更新为 deepseek-chat' as message;
