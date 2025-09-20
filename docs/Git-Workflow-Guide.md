# Git 工作流指南

本文档说明如何在 MIRIX 项目中按照规范进行 Git 操作。

## 远程仓库配置

项目已配置以下远程仓库：

- `origin`: 您的 fork 仓库 (https://github.com/lanxiake/MIRIX.git)
- `upstream`: 上游原始仓库 (https://github.com/Mirix-AI/MIRIX.git)

## 提交消息规范

### 格式
```
<类型>(<范围>): <主题>

<详细描述>

<页脚>
```

### 提交类型
- `feat`: 新增功能 (feature)
- `fix`: 修复 bug
- `docs`: 文档变更 (documentation)
- `style`: 代码格式化、不影响代码逻辑的更改
- `refactor`: 代码重构，不引入新功能也不修复 bug
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

### 提交范围（可选）
- `frontend`: 前端相关
- `backend`: 后端相关
- `mcp-sse-service`: MCP SSE 服务相关
- `docs`: 文档相关
- `database`: 数据库相关
- `config`: 配置相关

### 示例
```bash
feat(frontend): add dark mode toggle

This commit introduces a new dark mode toggle to the application settings.
Users can now switch between light and dark themes.

Closes #789
```

## 开发工作流

### 1. 创建新功能分支

```powershell
# 切换到基础分支
git checkout develop-mcp-server

# 拉取最新更改
git pull origin develop-mcp-server

# 创建新功能分支
git checkout -b feature/your-feature-name
```

或使用提供的脚本：

```powershell
.\scripts\git-workflow.ps1 -Action create-branch -BranchName "feature/your-feature-name"
```

### 2. 开发和提交

```bash
# 进行代码修改
# ...

# 添加更改
git add .

# 提交（会自动使用模板）
git commit

# 或直接指定消息
git commit -m "feat(frontend): add new functionality"
```

### 3. 同步上游更改

```bash
# 获取上游更改
git fetch upstream

# 合并上游主分支
git merge upstream/main
```

或使用脚本：

```powershell
.\scripts\git-workflow.ps1 -Action sync-upstream
```

### 4. 推送到您的仓库

```bash
git push origin feature/your-feature-name
```

或使用脚本：

```powershell
.\scripts\git-workflow.ps1 -Action push
```

### 5. 创建 Pull Request

1. 在 GitHub 上访问您的 fork 仓库
2. 点击 "Compare & pull request"
3. 填写 PR 标题和描述
4. 选择目标分支（通常是 `develop-mcp-server`）
5. 提交 PR 等待审查

## 工具使用

### Git 工作流脚本

位置：`scripts/git-workflow.ps1`

```powershell
# 显示使用说明
.\scripts\git-workflow.ps1

# 创建新分支
.\scripts\git-workflow.ps1 -Action create-branch -BranchName "feature/my-feature"

# 同步上游
.\scripts\git-workflow.ps1 -Action sync-upstream

# 推送当前分支
.\scripts\git-workflow.ps1 -Action push

# 检查提交消息格式
.\scripts\git-workflow.ps1 -Action check-commit -Message "feat(frontend): add new feature"
```

### 提交消息模板

项目已配置提交消息模板（`.gitmessage`），使用 `git commit` 时会自动显示。

### 提交消息格式检查

提交时会自动检查消息格式是否符合规范（通过 Git 钩子）。

## 常用命令速查

```bash
# 查看当前状态
git status

# 查看分支
git branch -a

# 查看远程仓库
git remote -v

# 查看提交历史
git log --oneline

# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 修改最后一次提交消息
git commit --amend
```

## 注意事项

1. **分支命名**：使用描述性名称，如 `feature/add-user-auth`、`fix/database-connection`
2. **提交频率**：小而频繁的提交比大的提交更好
3. **代码审查**：所有 PR 都需要至少一名其他开发者审查
4. **测试**：提交前确保所有测试通过
5. **冲突解决**：及时解决合并冲突，保持代码库整洁

## 故障排除

### 提交被拒绝
- 检查提交消息格式是否正确
- 确保没有违反项目编码规范

### 合并冲突
1. 查看冲突文件：`git status`
2. 手动编辑冲突文件
3. 添加解决后的文件：`git add <file>`
4. 完成合并：`git commit`

### 远程仓库问题
- 检查远程仓库配置：`git remote -v`
- 重新设置远程仓库：`git remote set-url origin <url>`
