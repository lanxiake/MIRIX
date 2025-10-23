# 快速配置 DeepSeek 为默认模型

## 一键配置（推荐）

执行以下命令即可自动配置：

```bash
cd /opt/MIRIX

# 步骤 1: 执行数据库迁移（只需执行一次）
./scripts/migrate_user_settings.sh

# 步骤 2: 配置 DeepSeek 为默认模型
./scripts/configure_deepseek_default.sh

# 步骤 3: 重启后端服务
docker-compose restart mirix-backend
```

## 手动配置

### 1. 修改用户设置管理器

**文件**: `mirix/services/user_settings_manager.py`

将第 44、45、85、86 行修改为：

```python
chat_model="deepseek-chat",      # 第 44、85 行
memory_model="deepseek-chat",    # 第 45、86 行
```

### 2. 添加 DeepSeek 配置到 LLMConfig

**文件**: `mirix/schemas/llm_config.py`

在第 198 行（`elif model_name == "letta":` 之前）添加：

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

### 3. 修改 AgentWrapper 默认配置

**文件**: `mirix/agent/agent_wrapper.py`

将第 114 行修改为：

```python
self.client.set_default_llm_config(LLMConfig.default_config("deepseek-chat"))
```

### 4. 配置 API 密钥

编辑 `docker-compose.yml`，在 `mirix-backend` 服务的 `environment` 部分添加：

```yaml
DEEPSEEK_API_KEY: sk-d44f718f3df9410ba5fd8e6164646777
```

### 5. 重启服务

```bash
docker-compose restart mirix-backend
```

## DeepSeek 配置信息

- **Base URL**: https://api.deepseek.com/v1
- **模型名称**: deepseek-chat
- **API 密钥**: sk-d44f718f3df9410ba5fd8e6164646777
- **上下文窗口**: 64,000 tokens

## 验证配置

1. 打开前端 http://localhost:18001
2. 进入"设置"面板
3. 查看"聊天模型"和"记忆管理模型"是否为 `deepseek-chat`
4. 发送测试消息验证功能
5. 重启后端，检查配置是否保留

## 问题排查

### 配置仍然丢失？

1. 确认已执行数据库迁移
2. 检查数据库表结构：
   ```bash
   docker exec -it mirix-postgres psql -U mirix -d mirix -c "\d user_settings"
   ```

### API 调用失败？

1. 检查 API 密钥是否正确配置
2. 查看后端日志：
   ```bash
   docker-compose logs -f mirix-backend
   ```

## 配置位置总结

| 配置项 | 文件路径 | 行号 |
|--------|---------|------|
| 用户默认设置 | `mirix/services/user_settings_manager.py` | 44-45, 85-86 |
| LLM 配置类 | `mirix/schemas/llm_config.py` | 198 (新增) |
| Agent 初始化 | `mirix/agent/agent_wrapper.py` | 114 |
| 环境变量 | `docker-compose.yml` | mirix-backend/environment |

## 详细文档

查看完整文档：`docs/configure_deepseek_default_model.md`

