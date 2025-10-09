#!/bin/bash
"""
LLM API配置修复脚本

这个脚本帮助配置有效的LLM API以解决Gemini配额超限问题
"""

echo "🔧 MIRIX LLM API配置修复工具"
echo "=================================="
echo ""
echo "问题：Gemini API配额已超限（429错误）"
echo "解决方案：配置其他LLM API作为备用"
echo ""

# 检查当前配置
echo "📋 当前API配置:"
grep -E "(API_KEY|MODEL)" .env 2>/dev/null | head -5

echo ""
echo "🎯 可选的解决方案:"
echo "1. 配置OpenAI API (推荐 - 性价比最高)"
echo "2. 配置Anthropic Claude API" 
echo "3. 配置有效的Gemini API Key"
echo "4. 等待明天配额重置 (UTC午夜)"
echo ""

read -p "请选择解决方案 (1-4): " choice

case $choice in
  1)
    echo ""
    echo "🔑 配置OpenAI API"
    echo "请访问 https://platform.openai.com/api-keys 获取API Key"
    echo ""
    read -p "请输入您的OpenAI API Key: " openai_key
    
    if [ -n "$openai_key" ]; then
      # 备份原配置
      cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
      
      # 添加OpenAI配置
      echo "" >> .env
      echo "# OpenAI配置 - 添加于 $(date)" >> .env
      echo "OPENAI_API_KEY=$openai_key" >> .env
      echo "OPENAI_MODEL=gpt-4o-mini" >> .env
      
      echo "✅ OpenAI配置已添加"
      echo "正在重启后端服务..."
      docker-compose restart mirix-backend
      echo "✅ 服务重启完成"
    else
      echo "❌ 未输入API Key，操作取消"
    fi
    ;;
    
  2)
    echo ""
    echo "🔑 配置Anthropic Claude API"
    echo "请访问 https://console.anthropic.com/ 获取API Key"
    echo ""
    read -p "请输入您的Anthropic API Key: " anthropic_key
    
    if [ -n "$anthropic_key" ]; then
      # 备份原配置
      cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
      
      # 添加Anthropic配置
      echo "" >> .env
      echo "# Anthropic配置 - 添加于 $(date)" >> .env
      echo "ANTHROPIC_API_KEY=$anthropic_key" >> .env
      echo "ANTHROPIC_MODEL=claude-3-haiku-20240307" >> .env
      
      echo "✅ Anthropic配置已添加"
      echo "正在重启后端服务..."
      docker-compose restart mirix-backend
      echo "✅ 服务重启完成"
    else
      echo "❌ 未输入API Key，操作取消"
    fi
    ;;
    
  3)
    echo ""
    echo "🔑 配置Gemini API"
    echo "请访问 https://aistudio.google.com/app/apikey 获取API Key"
    echo "注意：需要升级到付费计划以获得更多配额"
    echo ""
    read -p "请输入您的Gemini API Key: " gemini_key
    
    if [ -n "$gemini_key" ]; then
      # 备份原配置
      cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
      
      # 更新Gemini配置
      sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$gemini_key/" .env
      
      echo "✅ Gemini配置已更新"
      echo "正在重启后端服务..."
      docker-compose restart mirix-backend
      echo "✅ 服务重启完成"
    else
      echo "❌ 未输入API Key，操作取消"
    fi
    ;;
    
  4)
    echo ""
    echo "⏰ 等待配额重置"
    echo "Gemini免费配额将在UTC午夜（北京时间上午8点）重置"
    echo "当前时间: $(date)"
    echo "配额重置时间: 明天UTC 00:00 (北京时间 08:00)"
    echo ""
    echo "💡 临时建议:"
    echo "- 暂停MCP功能测试"
    echo "- 明天再继续测试"
    echo "- 或者配置其他LLM API作为备用"
    ;;
    
  *)
    echo "❌ 无效选择"
    exit 1
    ;;
esac

echo ""
echo "🧪 配置完成后，请运行以下命令测试:"
echo "curl -X POST http://localhost:47283/send_message \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"hello\", \"memorizing\": false}'"
echo ""
echo "如果配置正确，应该返回正常响应而不是429错误"
