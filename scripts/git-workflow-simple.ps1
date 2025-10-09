# Git 工作流简化脚本
param(
    [string]$Action,
    [string]$BranchName,
    [string]$Message
)

function Show-Usage {
    Write-Host "Git 工作流脚本使用说明:" -ForegroundColor Green
    Write-Host ""
    Write-Host "创建新功能分支:"
    Write-Host "  .\git-workflow-simple.ps1 create-branch feature/my-feature"
    Write-Host ""
    Write-Host "同步上游更改:"
    Write-Host "  .\git-workflow-simple.ps1 sync-upstream"
    Write-Host ""
    Write-Host "推送当前分支:"
    Write-Host "  .\git-workflow-simple.ps1 push"
    Write-Host ""
}

if ($Action -eq "create-branch" -and $BranchName) {
    Write-Host "创建新功能分支: $BranchName"
    git checkout develop-mcp-server
    git pull origin develop-mcp-server
    git checkout -b $BranchName
}
elseif ($Action -eq "sync-upstream") {
    Write-Host "同步上游仓库更改..."
    git fetch upstream
    git merge upstream/main
}
elseif ($Action -eq "push") {
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "推送当前分支: $currentBranch"
    git push origin $currentBranch
}
else {
    Show-Usage
}
