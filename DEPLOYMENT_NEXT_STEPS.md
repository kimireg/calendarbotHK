# 🚀 部署下一步

> GitHub 推送成功！现在可以部署到 Zeabur

**GitHub 仓库**: https://github.com/kimireg/calendarbotHK
**部署平台**: Zeabur
**推送时间**: 2026-01-17

---

## ✅ 已完成的工作

- [x] ✅ 代码重构完成（v3.0.0）
- [x] ✅ 代码审计通过（无安全问题）
- [x] ✅ 文档完整（部署指南、环境变量、故障排除）
- [x] ✅ 推送到 GitHub 成功

---

## 📋 部署前准备清单

### 需要准备的环境变量值

在开始部署前，请确保您已经准备好以下值：

#### Calendar Bot (必需)
- [ ] `TELEGRAM_TOKEN` - Telegram Bot Token
- [ ] `ALLOWED_USER_IDS` - 您的 Telegram 用户 ID
- [ ] `OPENROUTER_API_KEY` - OpenRouter API Key
- [ ] `GOOGLE_CREDENTIALS_JSON` - Google Service Account JSON（单行）
- [ ] `GOOGLE_CALENDAR_ID` - 主日历 ID

#### Calendar Bot (可选)
- [ ] `GOOGLE_CALENDAR_ID_KIKI` - Kiki 的日历 ID
- [ ] `GOOGLE_CALENDAR_ID_JASON` - Jason 的日历 ID
- [ ] `GOOGLE_CALENDAR_ID_JANET` - Janet 的日历 ID
- [ ] `GOOGLE_CALENDAR_ID_FAMILY` - 家庭日历 ID
- [ ] `ZEABUR_API_TOKEN` - Zeabur API Token（用于远程控制）

#### Singbox Updater (必需)
- [ ] `SINGBOX_SUBSCRIPTION_URL` - 订阅 URL

#### Singbox Updater (推荐)
- [ ] `SINGBOX_TELEGRAM_BOT_TOKEN` - Telegram Bot Token
- [ ] `SINGBOX_TELEGRAM_CHAT_ID` - Telegram Chat ID

**如何获取这些值**：参见 `docs/ENV_VARIABLES.md`

---

## 🎯 部署步骤（按建议顺序）

### 阶段 1: 部署 Singbox Updater

> **为什么先部署这个？**
> - 影响较小，独立运行
> - 可以验证 Zeabur 配置流程
> - 为 Calendar Bot 部署积累经验

#### Step 1: 登录 Zeabur
访问：https://dash.zeabur.com

#### Step 2: 创建服务
1. 进入您的项目（Project）
2. 点击 **"Add Service"** → 选择 **"Git"**
3. 选择仓库：`kimireg/calendarbotHK`
4. 配置服务：
   - **Service Name**: `singbox-updater`
   - **Root Directory**: `services/singbox_updater`
   - **Branch**: `main`
5. 点击 **"Deploy"**

#### Step 3: 配置环境变量
在服务页面，点击 **"Variables"** 标签，添加：

**必需变量**:
```
SINGBOX_SUBSCRIPTION_URL = [您的订阅URL]
```

**Telegram 通知变量**（推荐）:
```
SINGBOX_ENABLE_TELEGRAM = true
SINGBOX_TELEGRAM_BOT_TOKEN = [您的Bot Token]
SINGBOX_TELEGRAM_CHAT_ID = [您的Chat ID]
```

**可选变量**:
```
SINGBOX_CHECK_INTERVAL_HOURS = 6
SINGBOX_LOG_LEVEL = INFO
```

#### Step 4: 验证部署
1. 点击 **"Logs"** 标签
2. 查看日志，确认服务启动成功
3. 应该看到：
   ```
   ✅ Telegram notifier initialized
   🚀 Running initial update check...
   ✅ Update completed successfully!
   ```

#### Step 5: 记录服务信息
记录以下信息，用于 Calendar Bot 的远程控制：
- **Service ID**: 在 URL 中找到
- **Environment ID**: 在 URL 中找到

URL 格式：`https://dash.zeabur.com/projects/{project_id}/services/{service_id}?environmentID={env_id}`

---

### 阶段 2: 部署 Calendar Bot

> **确保 Singbox Updater 部署成功后再继续**

#### Step 1: 创建服务
1. 在同一个 Zeabur 项目中，点击 **"Add Service"** → **"Git"**
2. 选择仓库：`kimireg/calendarbotHK`
3. 配置服务：
   - **Service Name**: `calendar-bot`
   - **Root Directory**: `services/calendar_bot`
   - **Branch**: `main`
4. 点击 **"Deploy"**

#### Step 2: 配置环境变量

**核心必需变量**:
```
TELEGRAM_TOKEN = [您的Bot Token]
ALLOWED_USER_IDS = [您的用户ID，多个用逗号分隔]
OPENROUTER_API_KEY = [您的OpenRouter Key]
GOOGLE_CREDENTIALS_JSON = [完整的JSON，单行]
GOOGLE_CALENDAR_ID = [主日历ID]
```

**家庭成员日历**（可选）:
```
GOOGLE_CALENDAR_ID_KIKI = [Kiki的日历ID]
GOOGLE_CALENDAR_ID_JASON = [Jason的日历ID]
GOOGLE_CALENDAR_ID_JANET = [Janet的日历ID]
GOOGLE_CALENDAR_ID_FAMILY = [家庭日历ID]
```

**Zeabur 远程控制**（可选）:
```
ZEABUR_API_TOKEN = [您的Zeabur Token]
ZEABUR_TARGETS = {"singbox":{"service_id":"[刚才记录的ID]","env_id":"[刚才记录的ID]","name":"Singbox Updater"}}
```

#### Step 3: 验证部署
1. 查看日志，确认启动成功
2. 应该看到：
   ```
   🤖 Calendar Bot v3.0 (Refactored) Starting...
   ✅ Calendar Bot v3.0 Started Successfully!
   ```

#### Step 4: 测试功能
1. 打开 Telegram，找到您的 Bot
2. 发送 `/start`
3. 测试创建事件：发送 "明天下午3点开会"
4. 验证 Google Calendar 中是否创建成功

---

## 📚 详细文档参考

部署过程中如有疑问，请参考：

- **完整部署指南**: `docs/DEPLOYMENT_GUIDE.md`
- **环境变量参考**: `docs/ENV_VARIABLES.md`
- **故障排除**: `docs/DEPLOYMENT_GUIDE.md` 的故障排除章节
- **代码审计报告**: `docs/PRE_DEPLOYMENT_AUDIT.md`

---

## 🔍 部署验证清单

### Singbox Updater
- [ ] Zeabur 服务状态显示 "Running"
- [ ] 日志无错误，显示 "Update completed successfully"
- [ ] 如配置 Telegram，收到更新通知
- [ ] 定时任务正常运行

### Calendar Bot
- [ ] Zeabur 服务状态显示 "Running"
- [ ] 日志无错误，显示 "Started Successfully"
- [ ] Telegram Bot 响应 `/start` 命令
- [ ] 成功创建测试事件
- [ ] Google Calendar 中能看到创建的事件

---

## 🚨 如果遇到问题

### 常见问题
1. **服务无法启动** → 检查环境变量是否正确配置
2. **Bot 不响应** → 检查 `ALLOWED_USER_IDS` 是否包含您的 ID
3. **无法创建事件** → 检查 Google Service Account 权限
4. **订阅下载失败** → 检查订阅 URL 是否有效

详细的故障排除步骤请参考 `docs/DEPLOYMENT_GUIDE.md`

---

## 🎉 部署成功后

恭喜！您现在拥有：
- ✅ 智能日历助手（AI 驱动）
- ✅ VPN 配置自动更新服务
- ✅ 自动化的通知系统
- ✅ 远程控制能力

---

## 📝 后续维护

### 日常监控
- 定期查看 Zeabur 日志
- 监控 Telegram 通知
- 验证日历事件创建

### 更新代码
当需要更新代码时：
```bash
git add .
git commit -m "feat: 描述您的更新"
git push
```
Zeabur 会自动重新部署。

---

**准备好了吗？现在就开始部署吧！** 🚀

访问：https://dash.zeabur.com
