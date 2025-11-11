# MIRIX 项目 .claude 配置集成计划与执行记录

## 背景与目标
- 目标：在 MIRIX 项目根目录下生成一套符合项目实际结构的 `.claude` 配置，用于启用 Claude Code 的技能自动激活与文件变更跟踪。
- 来源：参考 `claude-template` 目录中的思想与内容（技能、钩子、设置示例），抽取适用于 MIRIX 的最小必要集成。

## 模板要点（梳理）
- 技能（skills）：通过 `skill-rules.json` 定义触发规则（关键词、意图正则、文件路径/内容触发）。
- 钩子（hooks）：
  - 必备：`skill-activation-prompt`（UserPromptSubmit 阶段自动建议技能）、`post-tool-use-tracker`（PostToolUse 阶段记录文件变更）。
  - 可选：`tsc-check`、`trigger-build-resolver` 等面向 TypeScript 多服务单仓结构，不适合 MIRIX 现状。
- 设置（settings.json）：注册钩子、权限、（示例里包含 MCP servers，需按项目调整）。

## MIRIX 项目评估
- 后端：Python 为主（目录 `mirix/`、`mcp_server/`、`tests/` 等），非 TypeScript 单仓结构。
- 前端：React（`frontend/src/*.js`），无 TypeScript 配置。
- 结论：采用“最小可用集成”，仅启用必备钩子，技能规则聚焦于 Python/JS 文件路径与通用关键词，避免 TypeScript 专用的 Stop 钩子。

## 配置决策
- `.claude/settings.json`
  - 注册 `UserPromptSubmit` → `skill-activation-prompt.sh`
  - 注册 `PostToolUse` → `post-tool-use-tracker.sh`
  - 暂不注册 Stop 钩子（避免 TS/Monorepo 假设带来误触发）。
  - 权限默认 `acceptEdits`，允许编辑类工具执行。
- `.claude/hooks/`
  - 引入 `skill-activation-prompt.sh` + `skill-activation-prompt.ts`（读取 `skill-rules.json` 按优先级输出建议）。
  - 引入 `post-tool-use-tracker.sh`（记录变更、缓存受影响的 repo，保留脚本中日志输出与注释）。
  - 注：脚本为 Bash，在 Windows 环境建议通过 Git Bash/WSL 运行；保留脚本内详细注释与基础日志。
- `.claude/skills/skill-rules.json`
  - 规则适配 MIRIX 路径模式：`mirix/**/*.py`、`mcp_server/**/*.py`、`frontend/src/**/*.js`、`frontend/src/**/*.jsx`。
  - 技能集合以通用型为主：`documentation-architect`、`code-architecture-reviewer`、`frontend-dev-guidelines`、`route-tester`、`auth-route-tester`、`error-tracking`（非强制）。
  - 执行策略全部采用 `suggest`，避免在现阶段阻塞工作流。

## 执行步骤
1. 创建 `.claude/` 目录结构：`settings.json`、`hooks/`、`skills/`、`README.md`。
2. 拷贝并定制必要钩子脚本（增加注释/保持日志输出）。
3. 编写 `skill-rules.json`，对 MIRIX 路径与关键词进行适配。
4. 验证配置文件语法与相对路径正确性。

## Windows 环境注意事项
- 钩子脚本为 Bash：建议在 Git Bash 或 WSL 下运行。
- 执行 PowerShell 连续命令时使用 `;` 分隔，例如：`cd .claude/hooks; npm install`。
- 如需在 Windows 下调试钩子，建议先安装 Node.js 与 `tsx`、`typescript`（`npm i -D tsx typescript`）。

## 验证与回滚策略
- 验证：
  - 在编辑 `frontend/src/*.js` 或 `mirix/**/*.py` 时，观察 UserPromptSubmit 阶段是否出现技能建议输出。
  - 执行编辑/写入操作后，检查 `.claude/tsc-cache/` 是否记录会话缓存（文件路径、受影响 repo）。
- 回滚：
  - 删除/重命名 `.claude/` 目录即可撤销集成。
  - 停用 hooks：从 `.claude/settings.json` 移除对应钩子配置。

## 后续改进（可选）
- 根据实际开发场景，逐步细化 `skill-rules.json` 的关键词与路径匹配，加入 Python/SQL/测试相关触发。
- 若前端迁移至 TypeScript，再评估加入 Stop 阶段的 `tsc-check` 与构建错误引导钩子。

## 执行记录
- 2025-11-05：完成 `.claude` 目录初始化与最小可用集成配置；文档编写与落地执行完成。