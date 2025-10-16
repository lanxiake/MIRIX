# Frontend-Backend Integration Experience

## 前后端数据交互最佳实践

### 1. API 请求体结构验证

#### 问题场景
前端向后端发送 PUT/POST 请求时，收到 422 Unprocessable Entity 错误。

#### 根本原因
前端请求体结构与后端 Pydantic Schema 定义不匹配。

#### 解决方案和经验

**步骤 1: 检查后端 Schema 定义**
```python
# 示例: mirix/schemas/user_settings.py
class UpdateUserSettingsRequest(BaseModel):
    """Request for updating user settings"""
    user_id: str
    settings: UserSettingsUpdate  # 嵌套结构
```

**步骤 2: 检查后端 API 端点**
```python
# 示例: mirix/server/fastapi_server.py
@app.put("/settings/users/{user_id}", response_model=UpdateUserSettingsResponse)
async def update_user_settings(user_id: str, request: UpdateUserSettingsRequest):
    # 验证 request 参数的类型就是 Schema 定义
    ...
```

**步骤 3: 调整前端请求体结构**
```javascript
// ❌ 错误的扁平结构
body: JSON.stringify({
  chat_model: settings.model,
  memory_model: settings.memoryModel,
  timezone: settings.timezone,
  ...
})

// ✅ 正确的嵌套结构
body: JSON.stringify({
  user_id: currentUser.id,  // 顶层字段
  settings: {                // 嵌套对象
    chat_model: settings.model,
    memory_model: settings.memoryModel,
    timezone: settings.timezone,
    ...
  }
})
```

#### 关键经验总结
1. **422 错误诊断流程**：
   - 查看后端 Schema 定义 (`schemas/` 目录)
   - 查看后端 API 端点参数类型 (`server/fastapi_server.py`)
   - 对比前端请求体结构
   - 确保字段名称、嵌套层级、数据类型完全一致

2. **Pydantic 验证规则**：
   - 字段名称必须完全匹配（区分大小写）
   - 嵌套结构必须对应
   - 可选字段使用 `Optional[Type]` 或提供默认值
   - 必需字段缺失会导致 422 错误

3. **调试技巧**：
   - 使用浏览器开发者工具查看实际发送的请求体
   - 在后端添加日志打印接收到的原始数据
   - 使用 Pydantic 的 `ValidationError` 详细信息

---

### 2. 用户数据隔离和上下文传递

#### 问题场景
用户上传的文件被错误地关联到 `default_user` 而不是当前用户。

#### 根本原因
后端服务在处理请求时，未正确获取或传递 `user_id` 参数。

#### 解决方案和经验

**前端：确保所有请求携带 user_id**
```javascript
// 方式 1: URL 路径参数
const response = await fetch(`${serverUrl}/api/users/${currentUser.id}/resource`, {
  method: 'POST',
  ...
});

// 方式 2: 请求体参数
const response = await fetch(`${serverUrl}/api/resource`, {
  method: 'POST',
  body: JSON.stringify({
    user_id: currentUser.id,
    ...otherData
  })
});

// 方式 3: Query 参数
const response = await fetch(`${serverUrl}/api/resource?user_id=${currentUser.id}`, {
  method: 'GET'
});
```

**后端：确保所有数据库操作使用正确的 user_id**
```python
# ✅ 正确：从请求中获取并验证 user_id
@app.post("/api/users/{user_id}/resource")
async def upload_resource(user_id: str, request: UploadRequest):
    # 验证请求体中的 user_id 与路径参数一致
    if request.user_id != user_id:
        raise HTTPException(status_code=400, detail="user_id mismatch")

    # 使用验证过的 user_id 进行数据库操作
    result = await resource_manager.save(
        user_id=user_id,  # 明确传递
        data=request.data
    )
    return result

# ❌ 错误：使用默认值或全局变量
async def upload_resource(request: UploadRequest):
    # 危险：使用硬编码的默认值
    result = await resource_manager.save(
        user_id="default_user",  # 会导致数据错误关联
        data=request.data
    )
```

#### 关键经验总结
1. **多租户数据隔离原则**：
   - 所有数据库表必须有 `user_id` 字段并建立索引
   - 所有查询必须带 `WHERE user_id = ?` 条件
   - 所有插入必须明确指定 `user_id`
   - 永远不要使用硬编码的默认用户 ID

2. **user_id 传递链路**：
   ```
   Frontend (currentUser.id)
     → HTTP Request (URL/Body/Query)
     → FastAPI Endpoint (path/request parameter)
     → Service Layer (explicit parameter)
     → Database Operation (WHERE/INSERT clause)
   ```

3. **验证检查点**：
   - API 入口：验证 user_id 格式和存在性
   - 服务层：确保 user_id 不为空且不是默认值
   - 数据库层：使用 ORM 级别的自动过滤器

---

### 3. React 组件状态管理和 UI 更新

#### 问题场景
实现"保存所有设置"功能，需要收集多个状态并提供用户反馈。

#### 最佳实践

**状态设计**
```javascript
// 保存状态
const [isSavingSettings, setIsSavingSettings] = useState(false);
// 反馈消息
const [saveSettingsMessage, setSaveSettingsMessage] = useState('');

// 使用 useCallback 避免不必要的重新渲染
const handleSaveAllSettings = useCallback(async () => {
  // 1. 前置验证
  if (!currentUser || !settings.serverUrl) {
    setSaveSettingsMessage('❌ No user selected or server not available');
    setTimeout(() => setSaveSettingsMessage(''), 3000);
    return;
  }

  // 2. 设置加载状态
  setIsSavingSettings(true);
  setSaveSettingsMessage('💾 Saving all settings...');

  try {
    // 3. 执行异步操作
    const response = await queuedFetch(`${settings.serverUrl}/api/save`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ /* data */ })
    });

    // 4. 处理成功响应
    if (response.ok) {
      const data = await response.json();
      console.log('Success:', data);
      setSaveSettingsMessage('✅ Settings saved successfully!');
    } else {
      // 5. 处理错误响应
      const errorData = await response.text();
      console.error('Failed:', errorData);
      setSaveSettingsMessage('❌ Failed to save settings');
    }
  } catch (error) {
    // 6. 处理网络错误
    console.error('Error:', error);
    setSaveSettingsMessage('❌ Error saving settings');
  } finally {
    // 7. 清理加载状态
    setIsSavingSettings(false);
    // 8. 自动清除消息
    setTimeout(() => setSaveSettingsMessage(''), 3000);
  }
}, [currentUser, settings, /* 其他依赖 */]);
```

**UI 反馈设计**
```javascript
<button
  onClick={handleSaveAllSettings}
  disabled={isSavingSettings || !currentUser}  // 防止重复点击
  className="save-all-settings-btn"
>
  {isSavingSettings ? '💾 Saving...' : '💾 Save All Settings'}
</button>

{saveSettingsMessage && (
  <span className={`update-message ${
    saveSettingsMessage.includes('✅') ? 'success' :
    saveSettingsMessage.includes('Saving') ? 'info' :
    'error'
  }`}>
    {saveSettingsMessage}
  </span>
)}
```

#### 关键经验总结
1. **异步操作模式**：
   - 前置验证 → 设置加载状态 → 执行操作 → 处理结果 → 清理状态
   - 使用 try-catch-finally 确保状态正确清理
   - 自动清除临时消息（3秒后）

2. **用户体验优化**：
   - 按钮禁用状态防止重复提交
   - 加载状态显示（Saving...）
   - 成功/失败消息区分（✅/❌）
   - 详细的控制台日志用于调试

3. **React 性能优化**：
   - 使用 `useCallback` 缓存回调函数
   - 正确声明依赖项数组
   - 避免不必要的组件重新渲染

---

### 4. 设置页面布局优化

#### 问题场景
需要调整设置页面的部分顺序，将用户选择移到模型配置上方。

#### 最佳实践

**组件结构组织**
```javascript
return (
  <div className="settings-panel">
    <div className="settings-content">
      {/* 1. 用户选择区域 - 最重要，放在最上方 */}
      <div className="settings-section user-section">
        <h3>👤 User Selection</h3>
        {/* 用户选择和创建功能 */}
      </div>

      {/* 2. 模型配置 - 核心功能 */}
      <div className="settings-section">
        <h3>🤖 Model Configuration</h3>
        {/* Chat Model, Memory Model 等 */}
      </div>

      {/* 3. 其他设置 - 辅助功能 */}
      <div className="settings-section">
        <h3>⚙️ Other Settings</h3>
        {/* Timezone, Persona 等 */}
      </div>

      {/* 4. 全局保存按钮 - 放在所有设置之后 */}
      <div className="settings-section save-settings-section">
        <button onClick={handleSaveAllSettings}>
          💾 Save All Settings
        </button>
      </div>

      {/* 5. 关于信息 - 放在最底部 */}
      <div className="settings-section">
        <h3>ℹ️ About</h3>
        {/* 版本信息等 */}
      </div>
    </div>
  </div>
);
```

#### 关键经验总结
1. **布局优先级原则**：
   - 用户相关 > 核心功能 > 辅助功能 > 操作按钮 > 信息展示
   - 按照用户操作流程组织（先选用户 → 配置设置 → 保存）

2. **代码重构技巧**：
   - 使用 Edit 工具移动大块代码
   - 确保删除原位置的重复代码
   - 保持 className 和事件处理器不变
   - 移动后测试功能是否正常

3. **可维护性**：
   - 使用清晰的注释标记各个区域
   - 保持一致的 className 命名
   - 每个 section 独立封装，便于调整顺序

---

### 5. Git 工作流和提交规范

#### Conventional Commits 规范

```bash
# 提交格式
<type>(<scope>): <subject>

<body>

<footer>
```

**常用类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构（既不是新功能也不是修复）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例提交**：
```bash
# 功能提交
git commit -m "$(cat <<'EOF'
feat: 优化设置页面布局并添加全局保存功能

- 将用户选择区域移至模型配置上方
- 新增"保存所有设置"按钮
- 实现设置数据与用户关联保存
- 添加保存状态反馈和错误处理

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 修复提交
git commit -m "$(cat <<'EOF'
fix: 修复设置保存422错误 - 调整请求体结构以匹配后端schema

- 修改 handleSaveAllSettings 函数的请求体结构
- 将 user_id 放在顶层，settings 数据包装在 settings 对象中
- 匹配后端 UpdateUserSettingsRequest schema 的嵌套结构要求
- 解决 PUT /settings/users/{user_id} 返回 422 Unprocessable Entity 错误

请求体结构变更：
Before: { chat_model: "xxx", memory_model: "xxx", ... }
After: { user_id: "user-xxx", settings: { chat_model: "xxx", ... } }

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

#### 关键经验总结
1. **提交信息结构**：
   - 第一行：简短描述（50字符内）
   - 空行分隔
   - 详细说明：具体改动内容（使用列表）
   - 问题描述和解决方案（如果是修复）
   - 技术细节（如果需要）

2. **提交粒度**：
   - 一个提交解决一个问题
   - 功能实现和 Bug 修复分开提交
   - 相关改动可以合并到一个提交

3. **推送策略**：
   - 功能开发在 feature 分支
   - 测试通过后再推送
   - 使用 `git push` 推送到远程

---

## 调试和问题诊断流程

### 问题诊断清单

1. **前端问题**：
   - [ ] 检查浏览器控制台错误
   - [ ] 检查 Network 面板的请求/响应
   - [ ] 确认 currentUser 状态是否正确
   - [ ] 确认 settings.serverUrl 是否配置

2. **API 通信问题**：
   - [ ] 确认请求 URL 正确
   - [ ] 确认请求方法（GET/POST/PUT/DELETE）
   - [ ] 确认 Content-Type 头部
   - [ ] 确认请求体格式（JSON.stringify）
   - [ ] 对比后端 Schema 定义

3. **后端问题**：
   - [ ] 检查后端日志输出
   - [ ] 确认 API 端点定义正确
   - [ ] 确认 Schema 验证规则
   - [ ] 确认数据库查询条件（特别是 user_id）
   - [ ] 确认服务层参数传递

4. **数据库问题**：
   - [ ] 检查表结构是否有 user_id 字段
   - [ ] 检查索引是否建立
   - [ ] 检查数据是否正确关联到用户
   - [ ] 使用 SQL 查询验证数据

### 常见错误代码速查

| 错误码 | 含义 | 常见原因 | 解决方案 |
|--------|------|----------|----------|
| 400 | Bad Request | 请求参数格式错误 | 检查参数名称和格式 |
| 422 | Unprocessable Entity | Schema 验证失败 | 检查请求体结构是否匹配 Schema |
| 500 | Internal Server Error | 后端代码错误 | 查看后端日志，检查异常堆栈 |

---

## 文件位置速查

### 前端关键文件
- **设置面板**: `frontend/src/components/SettingsPanel.js`
- **国际化**: `frontend/src/i18n.js`
- **样式**: `frontend/src/styles/`

### 后端关键文件
- **API 端点**: `mirix/server/fastapi_server.py`
- **Schema 定义**: `mirix/schemas/`
- **ORM 模型**: `mirix/orm/`
- **服务层**: `mirix/services/`
- **数据库访问**: `mirix/database/`

### 配置文件
- **主配置**: `mirix/configs/mirix.yaml`
- **环境变量**: `.env`
- **Docker**: `docker-compose.yml`

---

## 代码审查要点

### 前端代码审查
- [ ] 是否使用 `useCallback` 优化性能
- [ ] 是否正确声明依赖项数组
- [ ] 是否有加载状态提示
- [ ] 是否有错误处理
- [ ] 是否验证 currentUser 存在
- [ ] console.log 是否需要移除

### 后端代码审查
- [ ] 是否验证 user_id 参数
- [ ] 是否使用 user_id 过滤数据
- [ ] 是否有异常处理
- [ ] 是否返回正确的响应模型
- [ ] 是否添加日志记录
- [ ] Schema 定义是否完整

### 安全审查
- [ ] 是否防止 SQL 注入（使用 ORM）
- [ ] 是否防止跨用户数据访问
- [ ] 是否验证文件上传类型和大小
- [ ] 是否限制 API 调用频率
- [ ] 是否记录敏感操作日志

---

## 总结

本文档记录了 MIRIX 项目开发中的关键经验和最佳实践，包括：

1. **API 集成**: 前后端数据结构对齐，Schema 验证
2. **数据隔离**: 多用户环境下的 user_id 传递和验证
3. **状态管理**: React 异步操作和用户反馈
4. **UI 优化**: 组件布局和用户体验改进
5. **Git 工作流**: 提交规范和版本管理

这些经验可以直接应用到未来的功能开发和问题修复中。
