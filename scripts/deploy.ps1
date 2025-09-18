# MIRIX Docker 部署脚本 (PowerShell)
# 用法: .\scripts\deploy.ps1 [选项]
# 选项: -Environment [dev|prod] -Action [build|start|stop|restart|logs|clean]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "prod",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("build", "start", "stop", "restart", "logs", "clean", "status", "backup")]
    [string]$Action = "start",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

# 检查 Docker 和 Docker Compose
function Test-DockerInstallation {
    Write-Info "检查 Docker 安装..."
    
    try {
        $dockerVersion = docker --version
        Write-Success "Docker 已安装: $dockerVersion"
    }
    catch {
        Write-Error "Docker 未安装或未启动，请先安装 Docker Desktop"
        exit 1
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose 已安装: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose 未安装"
        exit 1
    }
}

# 检查环境文件
function Test-EnvironmentFile {
    Write-Info "检查环境配置文件..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Warning "未找到 .env 文件，正在从 .env.example 复制..."
            Copy-Item ".env.example" ".env"
            Write-Success "已创建 .env 文件，请根据需要修改配置"
        }
        else {
            Write-Error "未找到 .env.example 文件"
            exit 1
        }
    }
    else {
        Write-Success "环境配置文件存在"
    }
}

# 创建必要的目录
function New-RequiredDirectories {
    Write-Info "创建必要的目录..."
    
    $directories = @("data", "data/postgres", "data/redis", "logs", "uploads", "certs")
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "已创建目录: $dir"
        }
    }
}

# 构建服务
function Build-Services {
    Write-Info "构建 Docker 镜像..."
    
    $composeFiles = @("docker-compose.yml")
    if ($Environment -eq "dev") {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    
    try {
        if ($Force) {
            & docker-compose @composeArgs build --no-cache
        }
        else {
            & docker-compose @composeArgs build
        }
        Write-Success "镜像构建完成"
    }
    catch {
        Write-Error "镜像构建失败: $_"
        exit 1
    }
}

# 启动服务
function Start-Services {
    Write-Info "启动 MIRIX 服务..."
    
    $composeFiles = @("docker-compose.yml")
    if ($Environment -eq "dev") {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    
    try {
        & docker-compose @composeArgs up -d
        Write-Success "服务启动完成"
        
        # 等待服务就绪
        Write-Info "等待服务就绪..."
        Start-Sleep -Seconds 10
        
        # 检查服务状态
        Show-ServiceStatus
        
        # 显示访问地址
        Write-Info "服务访问地址:"
        Write-ColorOutput "  前端应用: http://localhost:3000" "Cyan"
        Write-ColorOutput "  后端 API: http://localhost:8000/docs" "Cyan"
        Write-ColorOutput "  MCP SSE: http://localhost:8001/health" "Cyan"
        
        if ($Environment -eq "dev") {
            Write-ColorOutput "  pgAdmin: http://localhost:5050" "Cyan"
            Write-ColorOutput "  Redis Commander: http://localhost:8081" "Cyan"
            Write-ColorOutput "  Mailhog: http://localhost:8025" "Cyan"
        }
    }
    catch {
        Write-Error "服务启动失败: $_"
        exit 1
    }
}

# 停止服务
function Stop-Services {
    Write-Info "停止 MIRIX 服务..."
    
    $composeFiles = @("docker-compose.yml")
    if ($Environment -eq "dev") {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    
    try {
        & docker-compose @composeArgs down
        Write-Success "服务已停止"
    }
    catch {
        Write-Error "服务停止失败: $_"
        exit 1
    }
}

# 重启服务
function Restart-Services {
    Write-Info "重启 MIRIX 服务..."
    Stop-Services
    Start-Sleep -Seconds 5
    Start-Services
}

# 显示日志
function Show-Logs {
    Write-Info "显示服务日志..."
    
    $composeFiles = @("docker-compose.yml")
    if ($Environment -eq "dev") {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    
    try {
        & docker-compose @composeArgs logs -f --tail=100
    }
    catch {
        Write-Error "无法显示日志: $_"
    }
}

# 清理资源
function Clear-Resources {
    Write-Warning "这将删除所有容器、镜像和数据卷！"
    
    if (-not $Force) {
        $confirmation = Read-Host "确定要继续吗？(y/N)"
        if ($confirmation -ne "y" -and $confirmation -ne "Y") {
            Write-Info "操作已取消"
            return
        }
    }
    
    Write-Info "清理 Docker 资源..."
    
    try {
        # 停止并删除容器
        & docker-compose down -v --remove-orphans
        
        # 删除镜像
        $images = docker images "mirix*" -q
        if ($images) {
            & docker rmi $images -f
        }
        
        # 清理系统
        & docker system prune -f
        
        Write-Success "资源清理完成"
    }
    catch {
        Write-Error "资源清理失败: $_"
    }
}

# 显示服务状态
function Show-ServiceStatus {
    Write-Info "服务状态:"
    
    $composeFiles = @("docker-compose.yml")
    if ($Environment -eq "dev") {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    $composeArgs = $composeFiles | ForEach-Object { "-f", $_ }
    
    try {
        & docker-compose @composeArgs ps
        
        Write-Info "健康检查状态:"
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "mirix"
        $containers | ForEach-Object {
            Write-ColorOutput $_.ToString() "White"
        }
    }
    catch {
        Write-Error "无法获取服务状态: $_"
    }
}

# 备份数据
function Backup-Data {
    Write-Info "备份数据库..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_$timestamp.sql"
    
    try {
        & docker-compose exec -T postgres pg_dump -U mirix mirix > $backupFile
        Write-Success "数据库备份完成: $backupFile"
        
        # 压缩备份文件
        Compress-Archive -Path $backupFile -DestinationPath "$backupFile.zip"
        Remove-Item $backupFile
        Write-Success "备份文件已压缩: $backupFile.zip"
    }
    catch {
        Write-Error "数据库备份失败: $_"
    }
}

# 主函数
function Main {
    Write-ColorOutput "🚀 MIRIX Docker 部署脚本" "Magenta"
    Write-ColorOutput "环境: $Environment | 操作: $Action" "White"
    Write-ColorOutput "=" * 50 "Gray"
    
    # 检查先决条件
    Test-DockerInstallation
    Test-EnvironmentFile
    New-RequiredDirectories
    
    # 执行操作
    switch ($Action) {
        "build" {
            Build-Services
        }
        "start" {
            Build-Services
            Start-Services
        }
        "stop" {
            Stop-Services
        }
        "restart" {
            Restart-Services
        }
        "logs" {
            Show-Logs
        }
        "clean" {
            Clear-Resources
        }
        "status" {
            Show-ServiceStatus
        }
        "backup" {
            Backup-Data
        }
        default {
            Write-Error "未知操作: $Action"
            exit 1
        }
    }
    
    Write-ColorOutput "=" * 50 "Gray"
    Write-Success "操作完成！"
}

# 执行主函数
try {
    Main
}
catch {
    Write-Error "脚本执行失败: $_"
    exit 1
}