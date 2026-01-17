# 🚀 快速开始指南

**版本**: v3.0.0 | **状态**: ✅ 就绪

---

## 第一步：上传到 GitHub ⬆️

### 方式：手动拖拽上传

**需要上传的内容**（按重要性排序）:

1️⃣ **services/** 文件夹（最重要！）
   - 包含两个服务的完整代码

2️⃣ **docs/** 文件夹
   - 包含部署指南等文档

3️⃣ **根目录文件**:
   - README.md
   - CLAUDE.md
   - .gitignore
   - GITHUB_UPLOAD_GUIDE.md
   - PROJECT_CHECKLIST.md

4️⃣ **src_0.1/** 文件夹（可选，作为备份）

**详细指南**: 参见 `GITHUB_UPLOAD_GUIDE.md` 或 `UPLOAD_CHECKLIST.txt`

---

## 第二步：部署到 Zeabur 🚀

### 顺序：先 Singbox Updater，后 Calendar Bot

#### 部署 Singbox Updater

**在 Zeabur**:
1. Add Service → Git → 选择你的仓库
2. Service Name: `singbox-updater`
3. Root Directory: `services/singbox_updater`
4. 配置环境变量:
   ```
   SINGBOX_SUBSCRIPTION_URL=你的订阅URL
   SINGBOX_ENABLE_TELEGRAM=true
   SINGBOX_TELEGRAM_BOT_TOKEN=你的Token
   SINGBOX_TELEGRAM_CHAT_ID=你的ChatID
   ```
5. Deploy

#### 部署 Calendar Bot

**在 Zeabur**:
1. Add Service → Git → 同一个仓库
2. Service Name: `calendar-bot`
3. Root Directory: `services/calendar_bot`
4. 配置环境变量（见下方）
5. Deploy

**Calendar Bot 环境变量**:
```
必需:
TELEGRAM_TOKEN=
ALLOWED_USER_IDS=
OPENROUTER_API_KEY=
GOOGLE_CREDENTIALS_JSON=
GOOGLE_CALENDAR_ID=

可选:
GOOGLE_CALENDAR_ID_KIKI=
GOOGLE_CALENDAR_ID_JASON=
GOOGLE_CALENDAR_ID_JANET=
GOOGLE_CALENDAR_ID_FAMILY=
ZEABUR_API_TOKEN=
ZEABUR_TARGETS=
```

**详细指南**: 参见 `docs/DEPLOYMENT_GUIDE.md`

---

## 第三步：验证部署 ✅

### Singbox Updater

**查看日志，应该看到**:
```
✅ Telegram notifier initialized
🚀 Running initial update check...
✅ Downloaded: XX servers
✅ Update completed successfully!
```

### Calendar Bot

**测试命令**:
```
发送: /start
应看到: 欢迎消息

发送: /status
应看到: 系统状态

发送: 明天下午3点开会
应看到: 创建事件成功
```

---

## 📚 重要文档

| 文档 | 用途 |
|------|------|
| `UPLOAD_CHECKLIST.txt` | 上传文件清单（简洁版） |
| `GITHUB_UPLOAD_GUIDE.md` | GitHub 上传详细指南 |
| `docs/DEPLOYMENT_GUIDE.md` | Zeabur 部署详细指南 ⭐ |
| `docs/CODE_AUDIT_REPORT.md` | 代码审计报告 |
| `README.md` | 项目总览 |

---

## 🆘 遇到问题？

1. **上传问题** → 查看 `GITHUB_UPLOAD_GUIDE.md`
2. **部署问题** → 查看 `docs/DEPLOYMENT_GUIDE.md` 故障排除章节
3. **环境变量** → 查看 `README.md` 配置说明章节
4. **其他问题** → 告诉 Claude，提供日志

---

## 📞 随时联系 Claude

在整个过程中，我会一步步引导你：
- ✅ 确认文件上传正确
- ✅ 指导 Zeabur 配置
- ✅ 帮助排查问题
- ✅ 验证部署成功

**现在，告诉我你准备好上传了，我会继续指导！** 🚀

---

**创建时间**: 2026-01-17 22:30
