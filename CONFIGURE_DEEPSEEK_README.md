# MIRIX DeepSeek 模型配置指南

本指南介绍如何在 MIRIX 中配置和使用 DeepSeek 模型。

## 快速配置

使用自动配置脚本（推荐）：

```bash
cd /opt/MIRIX
./scripts/configure_deepseek.sh
```

该脚本会引导你完成以下操作：
1. 创建或更新 `.env` 文件
2. 配置 DeepSeek API 密钥
3. 切换到 DeepSeek 模型配置

## 手动配置

### 步骤 1: 配置环境变量

创建或编辑 `.env` 文件：

```bash
cp .env.example .env
```

在 `.env` 文件中设置 DeepSeek API 密钥：

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 步骤 2: 配置模型

编辑 `/opt/MIRIX/mirix/configs/mirix.yaml`：

```yaml
agent_name: mirix
model_name: deepseek-chat
model_endpoint: https://api.deepseek.com/v1
# API密钥从环境变量 DEEPSEEK_API_KEY 读取
model_endpoint_type: openai
generation_config:
  temperature: 1.0
  max_tokens: 8192
  context_window: 64000
```

### 步骤 3: 重启服务

```bash
cd /opt/MIRIX
docker-compose down
docker-compose up -d
```

## 配置说明

### 模型参数

- **model_name**: `deepseek-chat` - DeepSeek 对话模型
- **model_endpoint**: `https://api.deepseek.com/v1` - DeepSeek API 端点
- **model_endpoint_type**: `openai` - 使用 OpenAI 兼容接口
- **temperature**: `1.0` - 生成温度（0.0-2.0）
- **max_tokens**: `8192` - 最大生成 token 数
- **context_window**: `64000` - 上下文窗口大小

### API 密钥优先级

系统按以下优先级读取 API 密钥：
1. 环境变量 `DEEPSEEK_API_KEY`（推荐）
2. 配置文件中的 `api_key` 字段（不推荐，密钥会被提交到代码库）

**⚠️ 安全提示**: 始终使用环境变量配置 API 密钥，不要在配置文件中硬编码密钥！

## 其他支持的模型

MIRIX 支持多种模型配置，您可以在 `mirix/configs/` 目录下找到预设配置：

- `mirix_deepseek.yaml` - DeepSeek 模型
- `mirix_gemini.yaml` - Google Gemini 模型
- `mirix_gpt4.yaml` - OpenAI GPT-4 模型
- `mirix_gpt4o-mini.yaml` - OpenAI GPT-4o-mini 模型
- `mirix_azure_example.yaml` - Azure OpenAI 模型示例
- `mirix_custom_model.yaml` - 自定义模型模板

## 切换模型

要切换到不同的模型，只需复制对应的配置文件：

```bash
# 切换到 DeepSeek
cp mirix/configs/mirix_deepseek.yaml mirix/configs/mirix.yaml

# 切换到 Gemini
cp mirix/configs/mirix_gemini.yaml mirix/configs/mirix.yaml

# 切换到 GPT-4
cp mirix/configs/mirix_gpt4.yaml mirix/configs/mirix.yaml
```

然后重启服务：

```bash
docker-compose restart mirix-backend
```

## 故障排查

### 问题 1: API 密钥无效

**症状**: 服务启动失败或请求返回认证错误

**解决方案**:
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 确保密钥没有多余的空格或换行符
3. 验证密钥在 DeepSeek 平台是否有效

### 问题 2: 配置未生效

**症状**: 修改配置后仍使用旧模型

**解决方案**:
1. 确认修改了正确的配置文件 (`mirix/configs/mirix.yaml`)
2. 重启 Docker 容器: `docker-compose restart`
3. 如果问题持续，尝试重新构建镜像: `docker-compose up -d --build`

### 问题 3: 网络连接问题

**症状**: 无法连接到 DeepSeek API

**解决方案**:
1. 检查网络代理配置（`.env` 中的 `HTTP_PROXY` 和 `HTTPS_PROXY`）
2. 确认可以访问 `https://api.deepseek.com`
3. 检查防火墙设置

## 技术支持

如遇到问题，请检查：
1. Docker 容器日志: `docker-compose logs mirix-backend`
2. 配置文件语法是否正确
3. 环境变量是否正确加载

更多信息请参考项目文档或提交 Issue。
