# ============================================================================
# MIRIX 部署 DeepSeek 配置脚本 (PowerShell)
# ============================================================================
# 说明: 自动执行所有必要步骤以将 MIRIX 切换到 DeepSeek 模型
# 使用: .\scripts\deploy_deepseek.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "MIRIX - 部署 DeepSeek 配置" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# 检查 Docker 是否运行
Write-Host "[1/4] 检查 Docker 服务..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "  ✓ Docker 服务正常运行" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker 服务未运行，请先启动 Docker" -ForegroundColor Red
    exit 1
}

# 检查容器是否运行
Write-Host ""
Write-Host "[2/4] 检查 MIRIX 容器状态..." -ForegroundColor Yellow
$backendContainer = docker ps --filter "name=mirix-backend" --format "{{.Names}}"
$postgresContainer = docker ps --filter "name=mirix-postgres" --format "{{.Names}}"

if (-not $backendContainer) {
    Write-Host "  ✗ mirix-backend 容器未运行" -ForegroundColor Red
    Write-Host "  请先启动服务: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

if (-not $postgresContainer) {
    Write-Host "  ✗ mirix-postgres 容器未运行" -ForegroundColor Red
    Write-Host "  请先启动服务: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "  ✓ 所有容器正常运行" -ForegroundColor Green

# 更新数据库
Write-Host ""
Write-Host "[3/4] 更新数据库中的用户设置..." -ForegroundColor Yellow
Write-Host "  执行 SQL 脚本: scripts/update_to_deepseek.sql" -ForegroundColor Cyan

$sqlScript = Get-Content "scripts\update_to_deepseek.sql" -Raw
docker exec -i mirix-postgres psql -U mirix -d mirix -c $sqlScript

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 数据库更新成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ 数据库更新失败" -ForegroundColor Red
    exit 1
}

# 重启后端服务
Write-Host ""
Write-Host "[4/4] 重启后端服务..." -ForegroundColor Yellow
docker-compose restart mirix-backend

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 后端服务重启成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ 后端服务重启失败" -ForegroundColor Red
    exit 1
}

# 等待服务启动
Write-Host ""
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务健康状态
Write-Host ""
Write-Host "检查服务健康状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:47283/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ 后端服务健康检查通过" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ 后端服务健康检查失败，状态码: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ 后端服务健康检查失败: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  服务可能仍在启动中，请稍后手动检查" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ 部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "完成的修改：" -ForegroundColor Yellow
Write-Host "  ✓ 用户设置管理器默认模型已改为 deepseek-chat" -ForegroundColor Green
Write-Host "  ✓ LLMConfig 已添加 DeepSeek 支持" -ForegroundColor Green
Write-Host "  ✓ AgentWrapper 默认配置已更新" -ForegroundColor Green
Write-Host "  ✓ 数据库中的用户设置已更新" -ForegroundColor Green
Write-Host "  ✓ 后端服务已重启" -ForegroundColor Green
Write-Host ""
Write-Host "验证步骤：" -ForegroundColor Yellow
Write-Host "  1. 打开前端: http://localhost:18001" -ForegroundColor Cyan
Write-Host "  2. 打开设置面板，检查模型配置" -ForegroundColor Cyan
Write-Host "  3. 发送测试消息验证 DeepSeek 模型功能" -ForegroundColor Cyan
Write-Host ""
Write-Host "DeepSeek 配置信息：" -ForegroundColor Yellow
Write-Host "  模型名称: deepseek-chat" -ForegroundColor Cyan
Write-Host "  API 端点: https://api.deepseek.com/v1" -ForegroundColor Cyan
Write-Host "  上下文窗口: 64,000 tokens" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看后端日志：" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f mirix-backend" -ForegroundColor Cyan
Write-Host ""
