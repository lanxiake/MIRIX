# MIRIX 数据库初始化更新总结

## 📊 更新日期
2025-10-21

## ✅ 完成的工作

### 1. 导出现有数据库结构
- ✅ 从运行中的 PostgreSQL 数据库导出完整 schema
- ✅ 识别所有 22 个表及其关系
- ✅ 保留所有扩展、类型和索引定义

### 2. 创建完整的初始化脚本

#### database/init_complete.sql
**完整的 SQL 初始化脚本**，包含:
- ✅ 数据库扩展（uuid-ossp, vector）
- ✅ 自定义类型（sandboxtype）
- ✅ 所有 22 个表的完整定义
- ✅ 表注释和文档
- ✅ 性能索引
- ✅ 默认用户和组织数据

**表结构**（22 个表）:
1. users - 用户信息
2. user_settings - 用户设置
3. organizations - 组织管理
4. agents - Agent 配置
5. agents_tags - Agent 标签
6. agent_environment_variables - Agent 环境变量
7. messages - 消息记录
8. steps - 工作流步骤
9. episodic_memory - 情景记忆
10. semantic_memory - 语义记忆
11. procedural_memory - 程序记忆
12. resource_memory - 资源记忆
13. knowledge_vault - 知识库
14. files - 文件管理
15. cloud_file_mapping - 云文件映射
16. tools - 工具定义
17. tools_agents - 工具-Agent 关联
18. providers - 提供商配置
19. sandbox_configs - 沙箱配置
20. sandbox_environment_variables - 沙箱环境变量
21. block - Block 配置
22. blocks_agents - Block-Agent 关联

#### database/init_db.py
**Python 初始化工具**，提供:
- ✅ 交互式初始化流程
- ✅ 自动验证扩展和表
- ✅ 统计信息显示
- ✅ 完整的错误处理
- ✅ 强制重置选项

### 3. 更新 Docker Compose 配置

#### docker-compose.yml
- ✅ 更新 PostgreSQL 初始化脚本路径
- ✅ 使用 `init_complete.sql` 替代旧的 `init.sql`

#### docker-compose.registry.yml
- ✅ 添加数据库初始化脚本挂载
- ✅ 确保私有仓库部署也能正确初始化

### 4. 创建文档

#### database/README.md
**完整的数据库文档**，包含:
- ✅ 数据库架构说明
- ✅ 3 种初始化方法
- ✅ 备份和恢复指南
- ✅ 性能优化建议
- ✅ 故障排除指南

#### database/schema_dump.sql
- ✅ 完整的 schema 导出（1079 行）
- ✅ 包含所有表定义和索引
- ✅ 作为参考和对比用途

## 📂 文件清单

### 新增文件
1. `database/init_complete.sql` - 完整初始化脚本
2. `database/init_db.py` - Python 初始化工具
3. `database/README.md` - 数据库文档
4. `database/schema_dump.sql` - Schema 导出
5. `database/DATABASE_INITIALIZATION_SUMMARY.md` - 本文档

### 修改文件
1. `docker-compose.yml` - 更新初始化脚本路径
2. `docker-compose.registry.yml` - 添加初始化脚本挂载

## 🎯 关键特性

### 1. 完整性
- ✅ 包含所有现有表结构
- ✅ 保留所有索引和约束
- ✅ 包含向量扩展配置

### 2. 用户隔离
所有数据表都包含 `user_id` 字段，支持:
- ✅ 多用户数据隔离
- ✅ 基于用户的查询优化
- ✅ 用户级别的数据管理

### 3. 向量支持
Memory 表（5 个）都包含向量字段:
- ✅ 4096 维向量（支持多种 embedding 模型）
- ✅ 为每种内容类型提供独立的 embedding 字段
- ✅ 预留向量索引扩展空间

### 4. 软删除
所有表都支持软删除:
- ✅ `is_deleted` 标记
- ✅ 索引排除已删除记录
- ✅ 保留历史数据

## 🚀 使用方法

### Docker Compose 自动初始化（推荐）

```bash
# 首次启动会自动初始化
docker-compose up -d

# 或只启动数据库
docker-compose up -d postgres
```

### Python 脚本初始化

```bash
# 设置数据库连接
export MIRIX_PG_URI='postgresql://mirix:mirix123@localhost:5432/mirix'

# 运行初始化
python database/init_db.py

# 强制重新初始化
python database/init_db.py --force
```

### 手动 SQL 初始化

```bash
# 直接执行 SQL
psql -U mirix -d mirix -f database/init_complete.sql

# 或通过 Docker
docker-compose exec -T postgres psql -U mirix -d mirix < database/init_complete.sql
```

## 🔍 验证初始化

```bash
# 使用 Python 工具查看状态
python database/init_db.py

# 或直接查询
docker-compose exec postgres psql -U mirix -d mirix -c "\dt"
```

预期输出:
- 22 个表
- 2 个扩展（uuid-ossp, vector）
- 默认用户和组织

## 📝 默认数据

### 默认用户
```
ID: user-00000000-0000-4000-8000-000000000000
名称: Default User
```

### 默认组织
```
ID: org-00000000-0000-4000-8000-000000000000
名称: Default Organization
```

## ⚠️ 注意事项

1. **首次运行**: Docker Compose 只在首次创建容器时执行初始化脚本
2. **重置数据**: 如需重新初始化，需删除数据卷或使用 `--force` 选项
3. **备份**: 在生产环境修改前务必备份数据
4. **向量索引**: 对于大量数据，建议创建 HNSW 或 IVFFlat 索引

## 🔄 迁移策略

将来的 schema 变更应该:
1. 创建迁移脚本 `database/migrations/XXX_description.sql`
2. 在迁移脚本中包含向前和向后迁移
3. 更新 `init_complete.sql` 以反映最新 schema
4. 更新文档说明变更

## 🎉 成果

- ✅ 完整的数据库架构定义
- ✅ 自动化初始化流程
- ✅ 详细的文档和指南
- ✅ 灵活的初始化选项
- ✅ 生产就绪的配置

## 📚 相关文档

- [database/README.md](README.md) - 完整数据库文档
- [database/init_complete.sql](init_complete.sql) - SQL 初始化脚本
- [database/init_db.py](init_db.py) - Python 初始化工具

---

**更新完成！现在 MIRIX 拥有完整、规范的数据库初始化系统。**
