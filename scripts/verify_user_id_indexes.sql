-- 用户数据隔离索引验证和创建脚本
-- 用途: 确保所有需要用户隔离的表在user_id字段上有索引
-- 执行方式: psql -U postgres -d mirix -f scripts/verify_user_id_indexes.sql

-- 检查并创建情景记忆表的user_id索引
CREATE INDEX IF NOT EXISTS idx_episodic_memory_user_id ON episodic_memory(user_id);

-- 检查并创建语义记忆表的user_id索引
CREATE INDEX IF NOT EXISTS idx_semantic_memory_user_id ON semantic_memory(user_id);

-- 检查并创建程序记忆表的user_id索引
CREATE INDEX IF NOT EXISTS idx_procedural_memory_user_id ON procedural_memory(user_id);

-- 检查并创建资源记忆表的user_id索引
CREATE INDEX IF NOT EXISTS idx_resource_memory_user_id ON resource_memory(user_id);

-- 检查并创建智能体表的user_id索引
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);

-- 检查并创建消息表的user_id索引
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);

-- 验证索引已创建
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname IN (
    'idx_episodic_memory_user_id',
    'idx_semantic_memory_user_id',
    'idx_procedural_memory_user_id',
    'idx_resource_memory_user_id',
    'idx_agents_user_id',
    'idx_messages_user_id'
)
ORDER BY tablename;

-- 检查各表的user_id字段统计信息
SELECT 
    'episodic_memory' as table_name,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as total_records
FROM episodic_memory
UNION ALL
SELECT 
    'semantic_memory',
    COUNT(DISTINCT user_id),
    COUNT(*)
FROM semantic_memory
UNION ALL
SELECT 
    'procedural_memory',
    COUNT(DISTINCT user_id),
    COUNT(*)
FROM procedural_memory
UNION ALL
SELECT 
    'resource_memory',
    COUNT(DISTINCT user_id),
    COUNT(*)
FROM resource_memory
UNION ALL
SELECT 
    'agents',
    COUNT(DISTINCT user_id),
    COUNT(*)
FROM agents
UNION ALL
SELECT 
    'messages',
    COUNT(DISTINCT user_id),
    COUNT(*)
FROM messages;

