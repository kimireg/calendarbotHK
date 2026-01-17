# Zeabur 部署指南

> 详细的分步部署说明，确保零错误部署

**版本**: 3.0.0
**更新时间**: 2026-01-17

---

## 📋 部署前准备

### 1. 确认环境变量

在部署前，请准备好以下信息：

#### Calendar Bot 环境变量清单

```bash
# 必需
TELEGRAM_TOKEN=你的Bot Token
ALLOWED_USER_IDS=123456789,987654321  # 你的Telegram用户ID，逗号分隔
OPENROUTER_API_KEY=你的OpenRouter API Key
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}  # 完整JSON，单行
GOOGLE_CALENDAR_ID=你的主日历ID

# 可选（如有配置）
LLM_MODEL_NAME=google/gemini-3-flash-preview
GOOGLE_CALENDAR_ID_KIKI=Kiki的日历ID
GOOGLE_CALENDAR_ID_JASON=Jason的日历ID
GOOGLE_CALENDAR_ID_JANET=Janet的日历ID
GOOGLE_CALENDAR_ID_FAMILY=家庭日历ID
DEFAULT_HOME_TZ=Asia/Singapore
LOG_LEVEL=INFO

# Zeabur远程控制（可选）
ZEABUR_API_TOKEN=你的Zeabur Token
ZEABUR_TARGETS={"singbox":{"service_id":"xxx","env_id":"yyy","name":"Singbox Updater"}}
```

#### Singbox Updater 环境变量清单

```bash
# 必需
SINGBOX_SUBSCRIPTION_URL=你的订阅URL

# Telegram通知（推荐）
SINGBOX_ENABLE_TELEGRAM=true
SINGBOX_TELEGRAM_BOT_TOKEN=你的Bot Token
SINGBOX_TELEGRAM_CHAT_ID=你的Chat ID

# 可选
SINGBOX_CHECK_INTERVAL_HOURS=6
SINGBOX_LOG_LEVEL=INFO
```

### 2. 准备 GitHub 仓库

确保代码已推送到 GitHub：

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Refactor to v3.0.0 - Modular architecture"

# 4. 添加远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 5. 推送
git push -u origin main
```

---

## 🚀 部署步骤

### 阶段 1: 部署 Singbox Updater

> **为什么先部署这个？**
> - 影响较小，独立运行
> - 可以先验证 Zeabur 配置流程
> - 不影响你的日常使用

#### Step 1: 创建 Zeabur 服务

1. 登录 [Zeabur Dashboard](https://dash.zeabur.com)

2. 进入你的项目（Project）

3. 点击 **"Add Service"** → 选择 **"Git"**

4. 选择你的 GitHub 仓库

5. 配置服务：
   - **Service Name**: `singbox-updater`
   - **Root Directory**: `services/singbox_updater`
   - **Branch**: `main`

6. 点击 **"Deploy"**

#### Step 2: 配置环境变量

1. 在服务页面，点击 **"Variables"** 标签

2. 点击 **"Add Variable"**，逐个添加：

   **必需变量**:
   ```
   名称: SINGBOX_SUBSCRIPTION_URL
   值: [你的订阅URL]
   ```

   **Telegram 通知变量**（推荐）:
   ```
   名称: SINGBOX_ENABLE_TELEGRAM
   值: true
   ```
   ```
   名称: SINGBOX_TELEGRAM_BOT_TOKEN
   值: [你的Bot Token]
   ```
   ```
   名称: SINGBOX_TELEGRAM_CHAT_ID
   值: [你的Chat ID]
   ```

   **可选变量**:
   ```
   名称: SINGBOX_CHECK_INTERVAL_HOURS
   值: 6
   ```

3. 保存后，Zeabur 会自动重启服务

#### Step 3: 验证部署

1. 点击 **"Logs"** 标签

2. 查看日志，应该看到：
   ```
   ✅ Telegram notifier initialized
   🚀 Running initial update check...
   📥 Downloading subscription...
   ✅ Downloaded: XX servers
   🆕 First run, saving initial version
   💾 Saved new version: subscription_20260117_XXXXXX
   ...
   ✅ Update completed successfully!
   ⏰ Scheduled to check every 6 hours
   ```

3. **如果看到错误**:
   - 检查 `SINGBOX_SUBSCRIPTION_URL` 是否正确
   - 检查网络是否可以访问订阅地址
   - 查看详细错误信息

4. **成功标志**:
   - 日志显示 "Update completed successfully"
   - 如果配置了 Telegram，应该收到通知消息

#### Step 4: 记录服务信息（用于 Calendar Bot 远程控制）

如果你想通过 Calendar Bot 远程重启这个服务：

1. 在 Zeabur，点击服务名称
2. 在 URL 中找到 **Service ID** 和 **Environment ID**:
   ```
   https://dash.zeabur.com/projects/{project_id}/services/{service_id}?environmentID={env_id}
   ```

3. 记录下来，稍后用于配置 Calendar Bot

---

### 阶段 2: 部署 Calendar Bot

> **重要提示**: 请确保 Singbox Updater 部署成功后再继续

#### Step 1: 创建 Zeabur 服务

1. 在同一个 Zeabur 项目中，点击 **"Add Service"** → **"Git"**

2. 选择同一个 GitHub 仓库

3. 配置服务：
   - **Service Name**: `calendar-bot`
   - **Root Directory**: `services/calendar_bot`
   - **Branch**: `main`

4. 点击 **"Deploy"**

#### Step 2: 配置环境变量

**⚠️ 关键步骤，请仔细核对！**

1. 进入 **"Variables"** 标签

2. 添加以下变量：

   **核心必需变量**:
   ```
   TELEGRAM_TOKEN
   值: [从 @BotFather 获取的 Token]
   ```
   ```
   ALLOWED_USER_IDS
   值: [你的Telegram用户ID，多个用逗号分隔，如: 123456789,987654321]
   ```

   **如何获取你的 Telegram 用户 ID**:
   - 方法 1: 发送消息给 @userinfobot
   - 方法 2: 发送消息给 @RawDataBot
   - 方法 3: 先不设置这个变量，部署后给 Bot 发消息，在日志中会看到你的 ID

   **AI 配置**:
   ```
   OPENROUTER_API_KEY
   值: [你的 OpenRouter API Key]
   ```

   **Google Calendar 配置**:
   ```
   GOOGLE_CREDENTIALS_JSON
   值: [完整的 Service Account JSON，注意是单行]
   ```

   **如何准备 GOOGLE_CREDENTIALS_JSON**:
   - 从 Google Cloud Console 下载 JSON 文件
   - 将多行 JSON 压缩成单行（去除所有换行符）
   - 确保是有效的 JSON 格式

   ```
   GOOGLE_CALENDAR_ID
   值: [你的主日历 ID，通常是你的 Gmail 地址]
   ```

   **家庭成员日历**（如果有）:
   ```
   GOOGLE_CALENDAR_ID_KIKI
   GOOGLE_CALENDAR_ID_JASON
   GOOGLE_CALENDAR_ID_JANET
   GOOGLE_CALENDAR_ID_FAMILY
   ```

   **Zeabur 远程控制**（如果要远程重启 Singbox Updater）:
   ```
   ZEABUR_API_TOKEN
   值: [你的 Zeabur Token]
   ```

   **如何获取 ZEABUR_API_TOKEN**:
   - 进入 Zeabur Account Settings
   - 找到 API Tokens
   - 创建新的 Token

   ```
   ZEABUR_TARGETS
   值: {"singbox":{"service_id":"[刚才记录的ID]","env_id":"[刚才记录的ID]","name":"Singbox Updater"}}
   ```

3. **保存后检查**: Zeabur 会自动重启服务

#### Step 3: 验证部署

1. 查看 **"Logs"** 标签:
   ```
   🤖 Calendar Bot v3.0 (Refactored) Starting...
   ✅ Database initialized: data/calendar_bot_v2.db
   ✅ Google Calendar service initialized
   ✅ Zeabur client initialized  # (如果配置了)
   ✅ Calendar Bot v3.0 Started Successfully!
   📊 Configured for 4 family members
   🔑 Authorized users: 2
   ```

2. **如果看到错误**:
   - 检查所有环境变量是否正确
   - 特别检查 `GOOGLE_CREDENTIALS_JSON` 格式
   - 查看详细错误信息

3. **测试 Bot**:
   - 打开 Telegram，找到你的 Bot
   - 发送 `/start`
   - 应该收到欢迎消息

4. **测试核心功能**:
   ```
   发送: /status
   应该看到: 系统状态信息

   发送: 明天下午3点开会
   应该看到: 创建事件成功的消息

   发送: /today
   应该看到: 今日日程列表
   ```

#### Step 4: 测试远程控制（可选）

如果配置了 Zeabur 远程控制：

```
发送: /restartsingboxupdater
应该看到: ✅ 服务重启指令已发送 (Zeabur)
```

然后查看 Singbox Updater 的日志，确认服务已重启。

---

## 🔍 部署后检查清单

### Calendar Bot
- [ ] `/start` 命令正常响应
- [ ] `/status` 显示正确状态
- [ ] 能够创建事件（测试文本消息）
- [ ] `/today` 显示日程
- [ ] 撤回按钮功能正常
- [ ] 图片识别功能正常（可选测试）
- [ ] `/restartsingboxupdater` 功能正常（可选）

### Singbox Updater
- [ ] 服务正常运行
- [ ] 日志显示初始化成功
- [ ] 订阅下载成功
- [ ] Telegram 通知发送成功（如配置）
- [ ] 定时任务已设置

---

## 🚨 故障排除

### 问题 1: Calendar Bot 无法启动

**症状**: 日志显示错误，服务不断重启

**可能原因**:
- 环境变量缺失或格式错误
- `GOOGLE_CREDENTIALS_JSON` 格式不正确

**解决方法**:
1. 检查日志中的具体错误信息
2. 逐个验证环境变量
3. 确保 `GOOGLE_CREDENTIALS_JSON` 是有效的单行 JSON
4. 确认 `ALLOWED_USER_IDS` 格式正确（逗号分隔，无空格）

### 问题 2: Bot 不响应消息

**症状**: 发送消息没有任何反应

**可能原因**:
- 你的用户 ID 不在 `ALLOWED_USER_IDS` 中
- `TELEGRAM_TOKEN` 错误

**解决方法**:
1. 查看日志，应该会看到 "未授权 ID: XXXXXX"
2. 将你的 ID 添加到 `ALLOWED_USER_IDS`
3. 保存环境变量后，服务会自动重启

### 问题 3: 无法创建日历事件

**症状**: Bot 响应正常，但创建事件失败

**可能原因**:
- Google Service Account 权限不足
- 日历 ID 错误

**解决方法**:
1. 确认 Service Account 有日历编辑权限
2. 在 Google Calendar 设置中，将 Service Account 邮箱添加为日历的编辑者
3. 检查 `GOOGLE_CALENDAR_ID` 是否正确

### 问题 4: Singbox Updater 订阅下载失败

**症状**: 日志显示 "Download failed"

**可能原因**:
- 订阅 URL 无效
- Zeabur 网络无法访问订阅地址
- 订阅需要特殊认证

**解决方法**:
1. 在浏览器中测试订阅 URL 是否可访问
2. 检查订阅 URL 格式是否正确
3. 如果订阅需要代理，可能需要其他解决方案

### 问题 5: Telegram 通知失败

**症状**: Singbox Updater 运行正常，但没收到 Telegram 消息

**可能原因**:
- Bot Token 或 Chat ID 错误
- `SINGBOX_ENABLE_TELEGRAM` 未设置为 true

**解决方法**:
1. 确认 `SINGBOX_ENABLE_TELEGRAM=true`
2. 验证 Bot Token 和 Chat ID
3. 查看日志中的详细错误信息

---

## 📊 部署成功标志

当你看到以下所有标志时，说明部署完全成功：

### Calendar Bot ✅
- [x] Zeabur 服务状态显示 "Running"
- [x] 日志无错误，显示 "Started Successfully"
- [x] Telegram Bot 响应 `/start` 命令
- [x] 成功创建测试事件
- [x] Google Calendar 中能看到创建的事件

### Singbox Updater ✅
- [x] Zeabur 服务状态显示 "Running"
- [x] 日志显示 "Update completed successfully"
- [x] 如配置 Telegram，收到更新通知
- [x] 定时任务正常运行（查看日志确认）

---

## 🎉 恭喜部署成功！

如果所有检查都通过，你现在已经成功部署了重构后的 v3.0.0 版本！

**下一步**:
1. 日常使用 Calendar Bot 创建事件
2. 监控 Singbox Updater 的自动更新
3. 如有问题，查看日志并参考故障排除
4. 定期检查 Zeabur 服务状态

**回滚方案**（如果需要）:
1. 在 Zeabur 中，进入服务设置
2. 找到 "Deployments" 历史
3. 选择之前的部署版本
4. 点击 "Redeploy" 回滚

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-17
