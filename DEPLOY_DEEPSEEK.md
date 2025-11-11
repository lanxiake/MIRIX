# 配置 DeepSeek 为默认模型

本指南说明如何将 MIRIX 系统切换到使用 DeepSeek 作为默认 LLM 模型。

## 快速开始

### 自动部署（推荐）

在项目根目录执行以下命令：

```powershell
# PowerShell (Windows)
.\scripts\deploy_deepseek.ps1
```

```bash
# Bash (Linux/macOS)
./scripts/configure_deepseek_default.sh
```

自动部署脚本将执行以下操作：
1. 检查 Docker 服务和容器状态
2. 更新数据库中的用户设置
3. 重启后端服务
4. 验证服务健康状态

### 手动部署

如果自动脚本失败，可以手动执行以下步骤：

#### 1. 更新数据库

```bash
# Docker 环境
docker exec -i mirix-postgres psql -U mirix -d mirix < scripts/update_to_deepseek.sql

# 本地环境
psql -U mirix -d mirix -f scripts/update_to_deepseek.sql
```

#### 2. 重启后端服务

```bash
# Docker 环境
docker-compose restart mirix-backend

# 本地环境
# 停止当前运行的进程，然后重新启动
python main.py
```

#### 3. 验证配置

```bash
# 检查服务健康状态
curl http://localhost:47283/health

# 查看后端日志
docker-compose logs -f mirix-backend
```

## 已完成的代码修改

本次更新已经修改了以下代码文件：

### 1. `mirix/services/user_settings_manager.py`
- 第 44-45 行：将新用户的默认模型改为 `deepseek-chat`
- 第 85-86 行：将用户设置更新时的默认模型改为 `deepseek-chat`

### 2. `mirix/agent/agent_wrapper.py`
- 第 158 行：将后备默认配置改为 `deepseek-chat`
- 第 139-140 行：已支持从环境变量 `DEEPSEEK_API_KEY` 读取 API 密钥

### 3. `mirix/schemas/llm_config.py`
- 第 205-212 行：添加了 `deepseek-chat` 的默认配置支持

### 4. `mirix/configs/mirix.yaml`
- 已配置为使用 `deepseek-chat` 模型

### 5. `.env`
- 已配置 `DEEPSEEK_API_KEY`

### 6. `docker-compose.yml`
- 第 62 行：已配置环境变量传递 `DEEPSEEK_API_KEY`

## DeepSeek 配置信息

| 配置项 | 值 |
|--------|-----|
| **模型名称** | `deepseek-chat` |
| **API 端点** | `https://api.deepseek.com/v1` |
| **API 密钥环境变量** | `DEEPSEEK_API_KEY` |
| **上下文窗口** | 64,000 tokens |
| **兼容性** | OpenAI API 兼容 |
| **端点类型** | `openai` |

## 验证配置

### 1. 检查前端设置

1. 打开前端界面：http://localhost:18001
2. 进入设置面板
3. 检查"聊天模型"和"记忆管理模型"是否显示为 `deepseek-chat`

### 2. 测试模型功能

1. 在聊天界面发送测试消息："你好"
2. 检查日志中是否调用了 DeepSeek API
3. 验证响应是否正常

### 3. 查看日志

```bash
# 实时查看后端日志
docker-compose logs -f mirix-backend

# 查找 DeepSeek 相关日志
docker-compose logs mirix-backend | grep -i "deepseek"

# 查找错误日志
docker-compose logs mirix-backend | grep -i "error"
```

## 故障排除

### 问题1: API 连接超时

**症状：** 日志显示 `Request timed out` 或 `Connection timeout`

**原因：**
- DeepSeek API 密钥未配置或无效
- 网络代理配置问题

**解决方法：**
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 检查代理设置（`HTTP_PROXY` 和 `HTTPS_PROXY`）
3. 尝试禁用代理测试：
   ```bash
   # 临时禁用代理
   docker-compose down
   # 编辑 docker-compose.yml，注释掉 HTTP_PROXY 和 HTTPS_PROXY
   docker-compose up -d
   ```

### 问题2: 数据库更新失败

**症状：** SQL 脚本执行失败

**解决方法：**
1. 检查 PostgreSQL 容器是否运行：
   ```bash
   docker ps | grep mirix-postgres
   ```
2. 手动连接数据库测试：
   ```bash
   docker exec -it mirix-postgres psql -U mirix -d mirix
   ```
3. 检查数据库表结构：
   ```sql
   \d user_settings
   SELECT * FROM user_settings LIMIT 5;
   ```

### 问题3: 配置在重启后丢失

**症状：** 重启后端后，模型配置恢复为旧值

**原因：** 数据库中的用户设置未更新

**解决方法：**
```bash
# 重新执行数据库更新脚本
docker exec -i mirix-postgres psql -U mirix -d mirix < scripts/update_to_deepseek.sql
```

### 问题4: 前端显示模型不正确

**症状：** 前端设置面板显示的模型不是 `deepseek-chat`

**解决方法：**
1. 清除浏览器缓存
2. 检查后端 API 响应：
   ```bash
   curl http://localhost:47283/api/v1/settings
   ```
3. 重启前端服务：
   ```bash
   docker-compose restart mirix-frontend
   ```

## 回滚到原配置

如果需要回滚到原来的配置（gpt-4o-mini）：

### 1. 使用 Git 恢复代码

```bash
git checkout HEAD -- mirix/services/user_settings_manager.py
git checkout HEAD -- mirix/agent/agent_wrapper.py
git checkout HEAD -- mirix/schemas/llm_config.py
```

### 2. 更新数据库

```sql
-- 恢复用户设置为原默认模型
UPDATE user_settings
SET
    chat_model = 'gpt-4o-mini',
    memory_model = 'gemini-2.5-flash-lite',
    updated_at = NOW()
WHERE is_deleted = false;
```

### 3. 重启服务

```bash
docker-compose restart mirix-backend
```

## 相关文件

- **部署脚本**
  - PowerShell: `scripts/deploy_deepseek.ps1`
  - Bash: `scripts/configure_deepseek_default.sh`
- **数据库脚本**: `scripts/update_to_deepseek.sql`
- **配置文件**: `mirix/configs/mirix.yaml`
- **环境变量**: `.env`
- **详细文档**: `docs/configure_deepseek_default_model.md`

## 支持的模型列表

MIRIX 现在支持以下模型：

| 模型名称 | 提供商 | API 密钥环境变量 | 上下文窗口 |
|---------|--------|-----------------|-----------|
| `deepseek-chat` | DeepSeek | `DEEPSEEK_API_KEY` | 64K |
| `gpt-4o-mini` | OpenAI | `OPENAI_API_KEY` | 128K |
| `gpt-4o` | OpenAI | `OPENAI_API_KEY` | 128K |
| `gemini-2.5-flash` | Google AI | `GOOGLE_AI_API_KEY` | 1M |
| `claude-3-5-sonnet` | Anthropic | `ANTHROPIC_API_KEY` | 200K |

## 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f mirix-backend`
2. 查看详细文档：`docs/configure_deepseek_default_model.md`
3. 提交 Issue：https://github.com/your-repo/MIRIX/issues

## 更新日志

- **2025-11-11**: 初始版本，支持 DeepSeek 作为默认模型
  - 添加代码修改
  - 添加数据库更新脚本
  - 添加自动部署脚本
  - 添加故障排除指南
