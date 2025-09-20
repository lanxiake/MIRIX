# Git 工作流脚本
# 用于简化按照规范进行 Git 操作

param(
    [Parameter(Mandatory=$false)]
    [string]$Action,
    [Parameter(Mandatory=$false)]
    [string]$BranchName,
    [Parameter(Mandatory=$false)]
    [string]$Message
)

function Show-Usage {
    Write-Host "Git 工作流脚本使用说明:" -ForegroundColor Green
    Write-Host ""
    Write-Host "创建新功能分支:" -ForegroundColor Yellow
    Write-Host "  .\git-workflow.ps1 -Action create-branch -BranchName 'feature/my-feature'"
    Write-Host ""
    Write-Host "同步上游更改:" -ForegroundColor Yellow
    Write-Host "  .\git-workflow.ps1 -Action sync-upstream"
    Write-Host ""
    Write-Host "推送当前分支:" -ForegroundColor Yellow
    Write-Host "  .\git-workflow.ps1 -Action push"
    Write-Host ""
    Write-Host "提交规范检查:" -ForegroundColor Yellow
    Write-Host "  .\git-workflow.ps1 -Action check-commit -Message 'feat(frontend): add new feature'"
    Write-Host ""
}

function Create-FeatureBranch {
    param([string]$BranchName)
    
    Write-Host "创建新功能分支: $BranchName" -ForegroundColor Green
    
    # 切换到 develop-mcp-server 分支
    git checkout develop-mcp-server
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: 无法切换到 develop-mcp-server 分支" -ForegroundColor Red
        return
    }
    
    # 拉取最新更改
    git pull origin develop-mcp-server
    if ($LASTEXITCODE -ne 0) {
        Write-Host "警告: 无法从 origin 拉取最新更改" -ForegroundColor Yellow
    }
    
    # 创建并切换到新分支
    git checkout -b $BranchName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "成功创建分支: $BranchName" -ForegroundColor Green
    } else {
        Write-Host "错误: 创建分支失败" -ForegroundColor Red
    }
}

function Sync-Upstream {
    Write-Host "同步上游仓库更改..." -ForegroundColor Green
    
    # 获取上游更改
    git fetch upstream
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: 无法获取上游更改" -ForegroundColor Red
        return
    }
    
    # 合并上游主分支
    git merge upstream/main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "成功合并上游更改" -ForegroundColor Green
    } else {
        Write-Host "合并过程中可能存在冲突，请手动解决" -ForegroundColor Yellow
    }
}

function Push-CurrentBranch {
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "推送当前分支: $currentBranch" -ForegroundColor Green
    
    git push origin $currentBranch
    if ($LASTEXITCODE -eq 0) {
        Write-Host "成功推送分支: $currentBranch" -ForegroundColor Green
    } else {
        Write-Host "错误: 推送失败" -ForegroundColor Red
    }
}

function Check-CommitMessage {
    param([string]$Message)
    
    Write-Host "检查提交消息格式: $Message" -ForegroundColor Green
    
    # 提交消息格式检查正则表达式
    $pattern = '^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}$'
    
    if ($Message -match $pattern) {
        Write-Host "✓ 提交消息格式正确" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ 提交消息格式不正确" -ForegroundColor Red
        Write-Host "正确格式: <类型>(<范围>): <主题>" -ForegroundColor Yellow
        Write-Host "例如: feat(frontend): add dark mode toggle" -ForegroundColor Yellow
        return $false
    }
}

# 主逻辑
switch ($Action) {
    "create-branch" {
        if (-not $BranchName) {
            Write-Host "错误: 请提供分支名称" -ForegroundColor Red
            Show-Usage
            exit 1
        }
        Create-FeatureBranch -BranchName $BranchName
    }
    "sync-upstream" {
        Sync-Upstream
    }
    "push" {
        Push-CurrentBranch
    }
    "check-commit" {
        if (-not $Message) {
            Write-Host "错误: 请提供提交消息" -ForegroundColor Red
            Show-Usage
            exit 1
        }
        Check-CommitMessage -Message $Message
    }
    default {
        Show-Usage
    }
}
