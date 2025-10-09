# Gemini API配额超限解决方案

## 🚨 问题根源

**Gemini API每日免费配额已用完**：
- 配额限制：每天200次请求（免费层）
- 当前状态：已超出配额
- 影响：所有需要LLM响应的功能都会失败

## 📊 错误详情

```
HTTP 429 Client Error: Too Many Requests
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Limit: 200 requests per day
Status: RESOURCE_EXHAUSTED
```

## 🛠️ 解决方案（按优先级）

### 方案1：等待配额重置（免费）
**最简单的解决方案**：
```
等待时间：到UTC午夜（北京时间上午8点）
配额重置：每24小时自动重置200次请求
费用：免费
```

### 方案2：升级到付费计划（推荐）
**访问Google AI Studio**：
1. 访问 https://aistudio.google.com/
2. 进入API Keys页面
3. 升级到付费计划
4. 付费后配额大幅增加（每分钟数千次请求）

### 方案3：切换到其他LLM提供商
**配置其他API（立即可用）**：

#### 选项A：OpenAI API
```bash
# 在.env文件中添加
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # 或 gpt-3.5-turbo (更便宜)
```

#### 选项B：Anthropic Claude API
```bash
# 在.env文件中添加  
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307  # 或其他Claude模型
```

#### 选项C：其他开源模型
- Ollama本地部署
- OpenRouter聚合服务
- Azure OpenAI服务

## ⚡ 立即解决步骤

### 步骤1：检查环境配置
```bash
cd /opt/MIRIX

# 查看当前LLM配置
cat .env | grep -E "(API_KEY|MODEL)"

# 查看docker-compose中的环境变量
docker-compose config | grep -E "(API_KEY|MODEL)"
```

### 步骤2：配置备用LLM
```bash
# 编辑环境变量文件
nano .env

# 添加OpenAI配置（示例）
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 或添加Anthropic配置
ANTHROPIC_API_KEY=your_api_key_here  
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### 步骤3：重启服务
```bash
# 重启后端服务以加载新配置
docker-compose restart mirix-backend

# 检查服务状态
docker-compose logs mirix-backend --tail 20
```

## 🧪 验证修复

配置新API后测试：
```bash
# 测试简单对话
curl -X POST http://localhost:47283/send_message \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "memorizing": false}'

# 应该返回正常响应而不是配额错误
```

## 📋 API成本对比

| 提供商 | 模型 | 输入价格/1M tokens | 输出价格/1M tokens |
|--------|------|------------------|------------------|
| Google | Gemini 2.0 Flash | 免费200次/天 → $0.075 | $0.30 |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 |
| OpenAI | GPT-3.5-turbo | $0.50 | $1.50 |
| Anthropic | Claude 3 Haiku | $0.25 | $1.25 |

## 🎯 推荐方案

### 开发测试阶段
1. **立即**：配置OpenAI GPT-4o-mini（性价比最高）
2. **短期**：升级Gemini到付费计划（原有配置不变）
3. **长期**：根据使用量选择最适合的方案

### 生产环境
1. **配置多个LLM后备**：避免单点故障
2. **实施智能路由**：根据任务类型选择最适合的模型
3. **监控配额使用**：设置告警避免意外中断

## 🔧 临时解决方案

如果暂时无法配置新API，可以：

1. **等待明天**：配额会在UTC午夜重置
2. **减少测试频率**：避免不必要的API调用
3. **使用现有功能**：记忆添加不消耗LLM配额（仅存储）

## 💡 优化建议

1. **缓存响应**：避免重复相同查询
2. **批量处理**：合并多个小请求
3. **智能重试**：遇到429错误时等待后重试
4. **配额监控**：实时监控API使用量

配置完新的LLM API后，所有MCP功能都应该恢复正常工作！
