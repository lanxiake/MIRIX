#!/bin/bash

# MIRIX DeepSeek 配置脚本
# 该脚本帮助用户快速配置 DeepSeek 模型

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
CONFIG_FILE="$PROJECT_ROOT/mirix/configs/mirix.yaml"
DEEPSEEK_CONFIG="$PROJECT_ROOT/mirix/configs/mirix_deepseek.yaml"

echo "=========================================="
echo "   MIRIX DeepSeek 配置向导"
echo "=========================================="
echo ""

# 检查是否已存在 .env 文件
if [ -f "$ENV_FILE" ]; then
    echo "✓ 发现已存在的 .env 文件"
    read -p "是否要更新 DeepSeek API 密钥? (y/n): " update_key
    if [ "$update_key" != "y" ] && [ "$update_key" != "Y" ]; then
        echo "跳过 API 密钥配置"
    else
        # 读取 DeepSeek API 密钥
        read -p "请输入 DeepSeek API 密钥: " deepseek_key
        
        # 更新或添加 DEEPSEEK_API_KEY
        if grep -q "^DEEPSEEK_API_KEY=" "$ENV_FILE"; then
            # 使用临时文件来更新
            sed "s|^DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$deepseek_key|" "$ENV_FILE" > "$ENV_FILE.tmp"
            mv "$ENV_FILE.tmp" "$ENV_FILE"
            echo "✓ 已更新 DeepSeek API 密钥"
        else
            echo "" >> "$ENV_FILE"
            echo "# DeepSeek API 密钥" >> "$ENV_FILE"
            echo "DEEPSEEK_API_KEY=$deepseek_key" >> "$ENV_FILE"
            echo "✓ 已添加 DeepSeek API 密钥"
        fi
    fi
else
    echo "未找到 .env 文件，将创建新文件..."
    
    # 从 .env.example 复制或创建新的 .env 文件
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        echo "✓ 已从 .env.example 创建 .env 文件"
    else
        cat > "$ENV_FILE" << 'ENVEOF'
# MIRIX 环境变量配置

# 数据库配置
POSTGRES_PASSWORD=mirix123
REDIS_PASSWORD=redis123

# DeepSeek API 密钥
DEEPSEEK_API_KEY=

# 其他 LLM API 密钥
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_AI_API_KEY=

# 网络代理配置（如需要）
HTTP_PROXY=http://10.157.152.63:7890
HTTPS_PROXY=http://10.157.152.63:7890
NO_PROXY=localhost,127.0.0.1,10.157.152.40,10.157.152.63,chromium,postgres,redis,mirix-frontend,mirix-mcp

# 日志配置
LOG_LEVEL=INFO
MCP_DEBUG=false
ENVEOF
        echo "✓ 已创建新的 .env 文件"
    fi
    
    # 读取 DeepSeek API 密钥
    read -p "请输入 DeepSeek API 密钥: " deepseek_key
    
    # 更新密钥
    sed "s|^DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$deepseek_key|" "$ENV_FILE" > "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE"
    echo "✓ 已配置 DeepSeek API 密钥"
fi

echo ""
echo "----------------------------------------"
read -p "是否要将主配置切换到 DeepSeek 模型? (y/n): " switch_model

if [ "$switch_model" = "y" ] || [ "$switch_model" = "Y" ]; then
    # 备份当前配置
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✓ 已备份当前配置"
    fi
    
    # 复制 DeepSeek 配置
    if [ -f "$DEEPSEEK_CONFIG" ]; then
        cp "$DEEPSEEK_CONFIG" "$CONFIG_FILE"
        echo "✓ 已切换到 DeepSeek 配置"
    else
        # 如果没有预设的 DeepSeek 配置，创建一个
        cat > "$CONFIG_FILE" << 'YAMLEOF'
agent_name: mirix
model_name: deepseek-chat
model_endpoint: https://api.deepseek.com/v1
# API密钥从环境变量 DEEPSEEK_API_KEY 读取，请在 .env 文件中配置
model_endpoint_type: openai
generation_config:
  temperature: 1.0
  max_tokens: 8192
  context_window: 64000
YAMLEOF
        echo "✓ 已创建并应用 DeepSeek 配置"
    fi
else
    echo "保持当前配置不变"
fi

echo ""
echo "=========================================="
echo "   配置完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 检查 .env 文件中的配置: cat $ENV_FILE"
echo "2. 检查模型配置: cat $CONFIG_FILE"
echo "3. 启动或重启 MIRIX 服务:"
echo "   cd $PROJECT_ROOT"
echo "   docker-compose down"
echo "   docker-compose up -d"
echo ""
echo "或者重新构建镜像:"
echo "   cd $PROJECT_ROOT"
echo "   docker-compose down"
echo "   docker-compose build"
echo "   docker-compose up -d"
echo ""
