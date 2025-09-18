-- MIRIX 开发环境数据库初始化脚本
-- 此脚本在开发环境首次启动时执行

-- 创建 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建开发用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mirix_dev') THEN
        CREATE ROLE mirix_dev WITH LOGIN PASSWORD 'dev_password';
    END IF;
END
$$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE mirix_dev TO mirix_dev;
GRANT ALL PRIVILEGES ON SCHEMA public TO mirix_dev;

-- 创建开发环境特定的配置表
CREATE TABLE IF NOT EXISTS dev_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入开发环境配置
INSERT INTO dev_config (key, value, description) VALUES
    ('environment', 'development', '当前环境标识'),
    ('debug_mode', 'true', '调试模式开关'),
    ('log_level', 'DEBUG', '日志级别'),
    ('auto_reload', 'true', '自动重载开关')
ON CONFLICT (key) DO NOTHING;

-- 创建测试数据表（可选）
CREATE TABLE IF NOT EXISTS test_memories (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    embedding vector(1536),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入一些测试数据
INSERT INTO test_memories (title, content, tags) VALUES
    ('测试记忆1', '这是一个测试记忆内容，用于开发环境测试。', ARRAY['test', 'development']),
    ('测试记忆2', '另一个测试记忆，包含更多详细信息。', ARRAY['test', 'sample']),
    ('开发笔记', 'MIRIX 项目开发相关的笔记和想法。', ARRAY['development', 'notes'])
ON CONFLICT DO NOTHING;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_test_memories_tags ON test_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_test_memories_created_at ON test_memories(created_at);

-- 创建更新时间戳的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表创建更新时间戳触发器
DROP TRIGGER IF EXISTS update_dev_config_updated_at ON dev_config;
CREATE TRIGGER update_dev_config_updated_at
    BEFORE UPDATE ON dev_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_test_memories_updated_at ON test_memories;
CREATE TRIGGER update_test_memories_updated_at
    BEFORE UPDATE ON test_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '=== MIRIX 开发环境数据库初始化完成 ===';
    RAISE NOTICE '数据库: mirix_dev';
    RAISE NOTICE '用户: mirix_dev';
    RAISE NOTICE '扩展: pgvector';
    RAISE NOTICE '测试数据: 已插入';
    RAISE NOTICE '========================================';
END
$$;