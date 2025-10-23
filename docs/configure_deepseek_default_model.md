# 配置 DeepSeek 为默认模型

本指南说明如何将 MIRIX 系统的默认模型从 GPT-4o-mini 改为 DeepSeek。

## 问题说明

当前系统每次重启后端应用后，模型配置会丢失，需要重新在前端配置。这是因为：

1. **数据库表结构问题**：旧的 `user_settings` 表结构与新的 ORM 模型不匹配
2. **默认模型硬编码**：系统多处硬编码了默认模型为 `gpt-4o-mini`

## 解决方案

### 第一步：执行数据库迁移

首先需要更新数据库表结构以正确保存用户配置。

```bash
# 在项目根目录执行
cd /opt/MIRIX
./scripts/migrate_user_settings.sh
```

这个脚本会：
- 备份现有数据库
- 更新 `user_settings` 表结构
- 迁移现有数据
- 添加新字段支持 `chat_model` 和 `memory_model`

### 第二步：修改默认模型配置

有三个地方需要修改默认模型配置：

#### 1. 用户设置管理器（主要配置）

**文件：** `/opt/MIRIX/mirix/services/user_settings_manager.py`

将第 44-45 行和第 85-86 行的默认模型改为 deepseek：

```python
# 第 44-45 行（get_or_create_user_settings 方法）
chat_model="deepseek-chat",  # 原来是 "gpt-4o-mini"
memory_model="deepseek-chat",  # 原来是 "gemini-2.5-flash-lite"

# 第 85-86 行（update_user_settings 方法）
chat_model="deepseek-chat",  # 原来是 "gpt-4o-mini"
memory_model="deepseek-chat",  # 原来是 "gemini-2.5-flash-lite"
```

#### 2. AgentWrapper 初始化配置（可选）

**文件：** `/opt/MIRIX/mirix/agent/agent_wrapper.py`

第 114 行可以改为使用自定义配置：

```python
# 原来：
self.client.set_default_llm_config(LLMConfig.default_config("gpt-4o-mini"))

# 改为：
self.client.set_default_llm_config(LLMConfig(
    model="deepseek-chat",
    model_endpoint_type="openai",
    model_endpoint="https://api.deepseek.com/v1",
    model_wrapper=None,
    context_window=64000,
))
```

#### 3. LLMConfig 添加 deepseek 默认配置（推荐）

**文件：** `/opt/MIRIX/mirix/schemas/llm_config.py`

在 `default_config` 方法中添加 deepseek 支持（第 206 行之前）：

```python
elif model_name == "deepseek-chat":
    return cls(
        model="deepseek-chat",
        model_endpoint_type="openai",
        model_endpoint="https://api.deepseek.com/v1",
        model_wrapper=None,
        context_window=64000,
    )
```

### 第三步：添加 DeepSeek API 密钥

有两种方式配置 API 密钥：

#### 方式 1：通过环境变量（推荐）

编辑 `.env` 文件或 `docker-compose.yml`：

```bash
# .env 文件
DEEPSEEK_API_KEY=sk-d44f718f3df9410ba5fd8e6164646777
```

或在 `docker-compose.yml` 的 `mirix-backend` 服务中添加：

```yaml
environment:
  DEEPSEEK_API_KEY: sk-d44f718f3df9410ba5fd8e6164646777
```

#### 方式 2：通过自定义模型配置文件

将 DeepSeek 配置保存到用户目录：

```bash
# 在容器中执行
mkdir -p ~/.mirix/custom_models
cp /opt/MIRIX/mirix/configs/mirix_deepseek.yaml ~/.mirix/custom_models/
```

### 第四步：重启服务

```bash
cd /opt/MIRIX
docker-compose restart mirix-backend
```

## 验证配置

### 1. 检查数据库表结构

```bash
docker exec -it mirix-postgres psql -U mirix -d mirix -c "\d user_settings"
```

应该看到以下字段：
- `id` (主键)
- `user_id` (外键)
- `chat_model`
- `memory_model`
- `timezone`
- `persona`
- 等等

### 2. 检查默认配置

创建新用户时应该使用 deepseek 作为默认模型：

```bash
# 查询用户设置
docker exec -it mirix-postgres psql -U mirix -d mirix -c "SELECT user_id, chat_model, memory_model FROM user_settings;"
```

### 3. 前端验证

1. 打开前端设置面板
2. 检查"聊天模型"和"记忆管理模型"是否显示为 `deepseek-chat`
3. 重启后端后，再次检查配置是否保留

## DeepSeek 配置信息

- **Base URL**: https://api.deepseek.com/v1
- **模型名称**: deepseek-chat
- **API 密钥**: sk-d44f718f3df9410ba5fd8e6164646777
- **上下文窗口**: 64,000 tokens
- **兼容性**: OpenAI API 兼容

## 常见问题

### Q1: 修改后配置仍然丢失？

**A**: 确保已经执行数据库迁移，并且重启了后端服务。

### Q2: API 密钥错误？

**A**: 检查环境变量是否正确设置，或者自定义模型配置文件中的 API 密钥是否正确。

### Q3: 如何添加多个模型？

**A**: 在 `~/.mirix/custom_models/` 目录下创建多个 YAML 配置文件，每个文件对应一个模型。

### Q4: 如何回滚到原来的配置？

**A**: 使用数据库备份文件回滚：

```bash
# 找到备份文件
ls -lt /opt/MIRIX/database/backups/

# 回滚
docker exec -i mirix-postgres psql -U mirix -d mirix < /opt/MIRIX/database/backups/backup_xxx.sql
```

## 相关文件

- 用户设置管理器: `mirix/services/user_settings_manager.py`
- LLM 配置: `mirix/schemas/llm_config.py`
- Agent 包装器: `mirix/agent/agent_wrapper.py`
- DeepSeek 配置: `mirix/configs/mirix_deepseek.yaml`
- 数据库迁移: `database/migrations/001_update_user_settings_table.sql`

## 技术说明

### 配置优先级

系统中的模型配置优先级如下：

1. **用户设置**（最高优先级）- 存储在 `user_settings` 表
2. **自定义模型配置** - `~/.mirix/custom_models/*.yaml`
3. **默认配置** - 代码中硬编码的默认值

### 数据持久化

用户设置现在存储在 PostgreSQL 数据库的 `user_settings` 表中，通过 Docker volume 持久化：

```yaml
volumes:
  postgres_data:
    driver: local
```

只要不删除 Docker volume，配置就会永久保存。

