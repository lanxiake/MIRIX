# MIRIX 数据库初始化指南

## 概述

MIRIX 使用 PostgreSQL 16 with pgvector 扩展作为主数据库，支持向量存储和高级查询功能。

## 数据库架构

### 核心表结构

1. **用户和组织**
   - `users` - 用户基础信息
   - `user_settings` - 用户配置和偏好
   - `organizations` - 组织/租户管理

2. **Agent 系统**
   - `agents` - Agent 配置
   - `agents_tags` - Agent 标签
   - `agent_environment_variables` - Agent 环境变量

3. **消息和通信**
   - `messages` - 对话消息
   - `steps` - 工作流步骤

4. **Memory 系统**（6种记忆类型）
   - `episodic_memory` - 情景记忆（事件和经历）
   - `semantic_memory` - 语义记忆（概念和知识）
   - `procedural_memory` - 程序记忆（技能和步骤）
   - `resource_memory` - 资源记忆（文档和资源）
   - `knowledge_vault` - 知识库（结构化知识）
   - 每种记忆都包含向量嵌入字段（4096 维）

5. **文件管理**
   - `files` - 文件元数据
   - `cloud_file_mapping` - 云端文件映射

6. **工具和集成**
   - `tools` - 工具定义
   - `tools_agents` - 工具-Agent 关联
   - `providers` - LLM 提供商配置

7. **沙箱环境**
   - `sandbox_configs` - 沙箱配置
   - `sandbox_environment_variables` - 沙箱环境变量

8. **Block 系统**
   - `block` - Block 配置
   - `blocks_agents` - Block-Agent 关联

### 扩展

- **uuid-ossp**: UUID 生成
- **vector (pgvector)**: 向量数据类型和索引

## 初始化方法

### 方法 1: Docker Compose 自动初始化（推荐）

Docker Compose 会在首次启动 PostgreSQL 容器时自动执行初始化脚本。

```bash
# 启动服务（首次运行会自动初始化）
docker-compose up -d postgres

# 或启动所有服务
docker-compose up -d
```

### 方法 2: 手动执行 Python 脚本

```bash
# 确保已设置数据库连接
export MIRIX_PG_URI='postgresql://mirix:mirix123@localhost:5432/mirix'

# 执行初始化脚本
python database/init_db.py

# 强制重新初始化（会删除现有数据）
python database/init_db.py --force
```

### 方法 3: 直接执行 SQL

```bash
# 使用 psql
psql -U mirix -d mirix -f database/init_complete.sql

# 或通过 Docker
docker-compose exec -T postgres psql -U mirix -d mirix < database/init_complete.sql
```

## 初始化脚本说明

### database/init_complete.sql

完整的数据库初始化脚本，包含:
- 扩展创建（uuid-ossp, vector）
- 自定义类型定义
- 所有表结构创建
- 索引创建
- 默认数据插入

### database/init_db.py

Python 初始化工具，提供:
- 交互式初始化流程
- 自动验证
- 统计信息显示
- 错误处理

### database/schema_dump.sql

从运行中的数据库导出的完整 schema（仅供参考）

## 默认账户

初始化后会创建默认账户:

- **默认用户 ID**: `user-00000000-0000-4000-8000-000000000000`
- **默认组织 ID**: `org-00000000-0000-4000-8000-000000000000`

## 验证初始化

### 检查扩展

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector');
```

### 检查表

```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### 检查数据

```sql
SELECT * FROM users;
SELECT * FROM organizations;
```

## 重置数据库

### 完全重置（删除所有数据）

```bash
# 停止服务
docker-compose down

# 删除数据卷
docker volume rm mirix_postgres_data

# 重新启动（会自动重新初始化）
docker-compose up -d
```

### 仅重置表结构（保留卷）

```bash
# 连接到数据库
docker-compose exec postgres psql -U mirix -d mirix

# 在 psql 中执行
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q

# 重新启动容器触发初始化
docker-compose restart postgres
```

## 备份和恢复

### 备份

```bash
# 备份完整数据库
docker-compose exec -T postgres pg_dump -U mirix -d mirix > backup_$(date +%Y%m%d).sql

# 仅备份 schema
docker-compose exec -T postgres pg_dump -U mirix -d mirix --schema-only > schema_backup.sql

# 仅备份数据
docker-compose exec -T postgres pg_dump -U mirix -d mirix --data-only > data_backup.sql
```

### 恢复

```bash
# 从备份恢复
docker-compose exec -T postgres psql -U mirix -d mirix < backup.sql
```

## 迁移

### 版本升级

当数据库 schema 发生变化时:

1. **备份现有数据**
   ```bash
   docker-compose exec -T postgres pg_dump -U mirix -d mirix > backup_before_migration.sql
   ```

2. **应用迁移脚本**
   ```bash
   # 如果有迁移脚本
   docker-compose exec -T postgres psql -U mirix -d mirix < database/migrations/001_add_new_fields.sql
   ```

3. **验证迁移**
   ```bash
   python database/init_db.py  # 会显示当前状态
   ```

## 性能优化

### 索引

所有 memory 表都已建立索引:
- user_id 索引（支持用户隔离查询）
- category/event_type 索引（支持分类查询）
- created_at 索引（支持时间范围查询）
- 向量索引（待创建，用于相似度搜索）

### 向量索引（可选）

对于大量数据，可以创建 HNSW 或 IVFFlat 索引:

```sql
-- 为 episodic_memory 创建 HNSW 索引
CREATE INDEX episodic_details_embedding_idx
ON episodic_memory
USING hnsw (details_embedding vector_cosine_ops)
WHERE NOT is_deleted;

-- 为其他 memory 表创建类似索引
CREATE INDEX semantic_details_embedding_idx
ON semantic_memory
USING hnsw (details_embedding vector_cosine_ops)
WHERE NOT is_deleted;
```

## 故障排除

### 连接失败

```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U mirix -d mirix -c "SELECT version();"
```

### 扩展未安装

```bash
# 手动创建扩展
docker-compose exec postgres psql -U mirix -d mirix -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker-compose exec postgres psql -U mirix -d mirix -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### 权限问题

```bash
# 检查数据卷权限
ls -la data/postgres

# 修复权限（Linux）
sudo chown -R 999:999 data/postgres
```

## 开发建议

1. **使用迁移**: 对 schema 的修改应该通过迁移脚本进行
2. **定期备份**: 在开发环境也要定期备份重要数据
3. **版本控制**: 所有 SQL 脚本都应纳入版本控制
4. **测试环境**: 在单独的测试数据库测试迁移

## 相关文件

- `database/init_complete.sql` - 完整初始化脚本
- `database/init_db.py` - Python 初始化工具
- `database/schema_dump.sql` - Schema 导出（参考）
- `docker-compose.yml` - Docker Compose 配置
- `docker-compose.registry.yml` - 私有仓库部署配置

## 更多信息

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/16/)
- [pgvector 扩展](https://github.com/pgvector/pgvector)
- [Docker Compose](https://docs.docker.com/compose/)
