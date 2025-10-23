# DeepSeek 配置完整指南

## 问题背景

您遇到的问题是：**每次重启后端应用后，前端配置的 DeepSeek 模型会丢失，需要重新配置。**

这是由两个原因造成的：

1. **数据库表结构不匹配**：旧的 `user_settings` 表结构与新的 ORM 模型不一致，导致配置无法正确保存
2. **默认模型硬编码**：代码中多处硬编码了 `gpt-4o-mini` 作为默认模型

## 解决方案概览

我们提供了完整的解决方案，包括：

1. ✅ 数据库迁移脚本 - 更新表结构以支持模型配置持久化
2. ✅ 一键配置脚本 - 自动修改代码将 DeepSeek 设为默认模型
3. ✅ 配置验证脚本 - 检查所有配置是否正确
4. ✅ 详细文档 - 手动配置和问题排查指南

## 快速开始（推荐）

### 一键配置

```bash
cd /opt/MIRIX

# 步骤 1: 数据库迁移（只需执行一次）
./scripts/migrate_user_settings.sh

# 步骤 2: 配置 DeepSeek 为默认模型
./scripts/configure_deepseek_default.sh

# 步骤 3: 重启后端服务
docker-compose restart mirix-backend

# 步骤 4: 验证配置
./scripts/verify_deepseek_config.sh
```

执行完成后：
- ✅ 新用户默认使用 DeepSeek 模型
- ✅ 模型配置会保存到数据库，重启后不会丢失
- ✅ 前端可以正常切换和保存模型配置

## DeepSeek 配置信息

根据您提供的信息：

| 配置项 | 值 |
|--------|-----|
| Base URL | https://api.deepseek.com/v1 |
| 模型名称 | deepseek-chat |
| API 密钥 | sk-d44f718f3df9410ba5fd8e6164646777 |
| 上下文窗口 | 64,000 tokens |
| 兼容性 | OpenAI API 兼容 |

## 文件结构

```
/opt/MIRIX/
├── CONFIGURE_DEEPSEEK.md                    # 快速配置指南
├── README_DEEPSEEK.md                       # 本文件
├── mirix/
│   └── configs/
│       └── mirix_deepseek.yaml              # DeepSeek 配置文件
├── docs/
│   └── configure_deepseek_default_model.md  # 详细配置文档
├── database/
│   └── migrations/
│       ├── 001_update_user_settings_table.sql  # 数据库迁移脚本
│       └── run_migration.sh                    # 迁移执行脚本
└── scripts/
    ├── migrate_user_settings.sh             # 数据库迁移（Docker环境）
    ├── configure_deepseek_default.sh        # 一键配置脚本
    └── verify_deepseek_config.sh            # 配置验证脚本
```

## 详细步骤说明

### 第一步：数据库迁移

**为什么需要？**
- 旧的 `user_settings` 表使用 `user_id` 作为主键，没有 `chat_model` 和 `memory_model` 字段
- 新的表结构支持保存聊天模型和记忆模型配置

**执行方法：**
```bash
./scripts/migrate_user_settings.sh
```

**操作内容：**
1. 自动备份现有数据库
2. 删除旧的 `user_settings` 表
3. 创建新的表结构（包含 `chat_model`, `memory_model` 等字段）
4. 迁移旧数据到新表
5. 创建必要的索引

### 第二步：配置默认模型

**为什么需要？**
- 系统在多个地方硬编码了默认模型为 `gpt-4o-mini`
- 需要统一修改为 `deepseek-chat`

**执行方法：**
```bash
./scripts/configure_deepseek_default.sh
```

**修改的文件：**

1. **mirix/services/user_settings_manager.py** (2处)
   - 第 44 行: `chat_model="deepseek-chat"`
   - 第 45 行: `memory_model="deepseek-chat"`
   - 第 85 行: `chat_model="deepseek-chat"`
   - 第 86 行: `memory_model="deepseek-chat"`

2. **mirix/schemas/llm_config.py** (新增)
   - 添加 `deepseek-chat` 的默认配置方法

3. **mirix/agent/agent_wrapper.py** (1处)
   - 第 114 行: 改为使用 `deepseek-chat` 默认配置

4. **docker-compose.yml** (新增)
   - 添加 `DEEPSEEK_API_KEY` 环境变量

### 第三步：重启服务

```bash
docker-compose restart mirix-backend
```

等待服务启动完成（约 10-30 秒）。

### 第四步：验证配置

```bash
./scripts/verify_deepseek_config.sh
```

该脚本会检查：
- ✅ 数据库表结构是否正确
- ✅ 代码配置是否已修改
- ✅ 环境变量是否已设置
- ✅ 配置文件是否存在
- ✅ 服务是否正常运行

## 手动配置（可选）

如果您希望手动配置，请参考：`CONFIGURE_DEEPSEEK.md`

## 验证效果

### 前端验证

1. 打开前端：http://localhost:18001
2. 点击"设置"图标
3. 查看"模型配置"部分：
   - 聊天模型应显示：`deepseek-chat`
   - 记忆管理模型应显示：`deepseek-chat`

### 功能验证

1. 发送测试消息，验证 DeepSeek 是否正常工作
2. 重启后端：`docker-compose restart mirix-backend`
3. 刷新前端，检查模型配置是否保留

### 数据库验证

```bash
# 查看用户设置
docker exec -it mirix-postgres psql -U mirix -d mirix -c \
  "SELECT user_id, chat_model, memory_model FROM user_settings;"
```

应该看到 `deepseek-chat` 的配置。

## 常见问题

### Q1: 执行迁移脚本时提示找不到 gen_random_uuid 函数

**A**: 这是因为 PostgreSQL 的 uuid-ossp 扩展未安装。解决方法：

```bash
docker exec -it mirix-postgres psql -U mirix -d mirix -c \
  "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

然后重新执行迁移。

### Q2: 配置后仍然显示 gpt-4o-mini

**A**: 可能的原因：
1. 后端服务未重启：`docker-compose restart mirix-backend`
2. 浏览器缓存：强制刷新页面（Ctrl+Shift+R）
3. 旧的用户记录：删除旧用户设置后重新创建

### Q3: DeepSeek API 调用失败

**A**: 检查：
1. API 密钥是否正确配置
2. 网络是否可以访问 https://api.deepseek.com
3. 查看后端日志：`docker-compose logs -f mirix-backend`

### Q4: 如何回滚配置？

**A**: 
```bash
# 查看备份目录
ls -lt /opt/MIRIX/backups/

# 找到最新的备份，恢复文件
cp /opt/MIRIX/backups/config_XXXXXX/*.bak <原文件路径>

# 重启服务
docker-compose restart mirix-backend
```

### Q5: 如何为不同用户配置不同的模型？

**A**: 
1. 保持默认配置为 DeepSeek
2. 用户可以在前端设置中选择其他模型
3. 每个用户的配置独立保存在 `user_settings` 表中

## 配置优先级

系统中的模型配置优先级（从高到低）：

1. **用户设置**（最高）- `user_settings` 表中的配置
2. **自定义模型配置** - `~/.mirix/custom_models/*.yaml`
3. **代码默认配置**（最低）- 代码中的 default_config

这意味着：
- 用户在前端设置的模型会覆盖默认配置
- 如果用户未设置，则使用代码中的默认配置（现在是 DeepSeek）

## 数据持久化

配置数据存储在 PostgreSQL 数据库中，通过 Docker volume 持久化：

```yaml
# docker-compose.yml
volumes:
  postgres_data:
    driver: local
```

只要不删除 `postgres_data` volume，所有配置都会永久保存。

## 技术细节

### 数据库 Schema

```sql
CREATE TABLE public.user_settings (
    id character varying PRIMARY KEY,
    user_id character varying NOT NULL,
    chat_model character varying(100),      -- 聊天模型
    memory_model character varying(100),    -- 记忆模型
    timezone character varying(100),
    persona character varying(100),
    persona_text character varying,
    ui_preferences json,
    custom_settings json,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    is_deleted boolean,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### LLMConfig 配置

```python
LLMConfig(
    model="deepseek-chat",
    model_endpoint_type="openai",
    model_endpoint="https://api.deepseek.com/v1",
    model_wrapper=None,
    context_window=64000,
)
```

## 相关文档

- [快速配置指南](CONFIGURE_DEEPSEEK.md)
- [详细配置文档](docs/configure_deepseek_default_model.md)
- [数据库迁移脚本](database/migrations/001_update_user_settings_table.sql)

## 支持

如有问题，请检查：

1. 后端日志：`docker-compose logs -f mirix-backend`
2. 数据库日志：`docker-compose logs -f postgres`
3. 验证脚本输出：`./scripts/verify_deepseek_config.sh`

---

**最后更新**: 2025-10-23
**版本**: 1.0.0

