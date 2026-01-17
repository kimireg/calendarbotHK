# Kimi's Telegram Bot Services

> 统一代码仓库，包含两个独立部署的 Python 服务

**版本**: 3.0.0 (Refactored)
**部署平台**: Zeabur
**最后更新**: 2026-01-17

---

## 📋 项目概述

本项目包含两个相关联的 Telegram Bot 服务：

### 1. **Calendar Bot** - 智能日历助手
通过 AI 解析自然语言，自动创建 Google Calendar 事件。

**核心功能**:
- 🤖 自然语言解析（支持文本和图片）
- 📅 多家庭成员日历管理
- 🌍 智能时区处理
- ✅ 全天任务 vs 定时事件自动识别
- 🔄 远程控制 Singbox Updater

**技术栈**: python-telegram-bot, OpenAI SDK, Google Calendar API, SQLAlchemy, Pydantic

### 2. **Singbox Updater** - VPN配置自动更新
定时检查订阅更新，自动生成多版本配置文件。

**核心功能**:
- 📥 自动检测订阅更新
- 📦 版本控制和历史管理
- 🔄 智能配置更新（Pro/Air版本）
- 📱 Telegram 通知推送

**技术栈**: schedule, requests, custom parsers

---

## 🏗️ 项目结构

```
kimi-telegram-bot/
├── services/
│   ├── calendar_bot/           # 日历机器人服务
│   │   ├── src/
│   │   │   ├── config/         # 配置管理
│   │   │   ├── database/       # 数据库层 (SQLAlchemy)
│   │   │   ├── core/           # 核心业务逻辑
│   │   │   ├── integrations/   # 外部集成 (Google, Zeabur)
│   │   │   └── handlers/       # Telegram 处理器
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── singbox_updater/        # Singbox 更新服务
│       ├── src/
│       │   ├── subscription/   # 订阅检查
│       │   ├── config_manager/ # 配置管理
│       │   ├── notifier/       # 通知系统
│       │   └── scheduler/      # 定时任务
│       ├── config/
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── src_0.1/                    # 旧版本代码（备份）
├── docs/                       # 文档
├── .gitignore
├── CLAUDE.md                   # Claude 协作规范
└── README.md                   # 本文件
```

---

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Zeabur 账号
- Telegram Bot Token
- Google Service Account (Calendar Bot)
- 订阅 URL (Singbox Updater)

### 本地开发

#### Calendar Bot
```bash
cd services/calendar_bot
pip install -r requirements.txt
python main.py
```

#### Singbox Updater
```bash
cd services/singbox_updater
pip install -r requirements.txt
python main.py --mode once  # 单次运行测试
python main.py              # 定时运行
```

---

## 📦 Zeabur 部署

### 部署 Calendar Bot

1. **创建新服务**
   - 在 Zeabur 选择 GitHub 仓库
   - 服务名称: `calendar-bot`
   - Root Directory: `services/calendar_bot`

2. **配置环境变量**

必需环境变量：
```
TELEGRAM_TOKEN=你的Bot Token
ALLOWED_USER_IDS=123456789,987654321
OPENROUTER_API_KEY=你的OpenRouter Key
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_CALENDAR_ID=主日历ID
```

可选环境变量：
```
LLM_MODEL_NAME=google/gemini-3-flash-preview
GOOGLE_CALENDAR_ID_KIKI=Kiki的日历ID
GOOGLE_CALENDAR_ID_JASON=Jason的日历ID
GOOGLE_CALENDAR_ID_JANET=Janet的日历ID
GOOGLE_CALENDAR_ID_FAMILY=家庭日历ID
DEFAULT_HOME_TZ=Asia/Singapore
LOG_LEVEL=INFO
```

Zeabur 远程控制（可选）：
```
ZEABUR_API_TOKEN=你的Zeabur Token
ZEABUR_TARGETS={"singbox":{"service_id":"...","env_id":"...","name":"Singbox Updater"}}
```

3. **部署**
   - Zeabur 自动检测 Dockerfile
   - 点击部署

### 部署 Singbox Updater

1. **创建新服务**
   - 在 Zeabur 选择同一个 GitHub 仓库
   - 服务名称: `singbox-updater`
   - Root Directory: `services/singbox_updater`

2. **配置环境变量**

必需环境变量：
```
SINGBOX_SUBSCRIPTION_URL=你的订阅URL
```

Telegram 通知（可选但推荐）：
```
SINGBOX_ENABLE_TELEGRAM=true
SINGBOX_TELEGRAM_BOT_TOKEN=你的Bot Token
SINGBOX_TELEGRAM_CHAT_ID=你的Chat ID
```

其他配置：
```
SINGBOX_CHECK_INTERVAL_HOURS=6
SINGBOX_LOG_LEVEL=INFO
```

3. **上传基础配置**
   - 需要手动上传 `config/base_configs/Singbox_Pro_V5_9.json`
   - 或在首次运行后自动生成

---

## ⚙️ 配置说明

### Calendar Bot 环境变量

| 环境变量 | 说明 | 必需 | 默认值 |
|---------|------|------|--------|
| `TELEGRAM_TOKEN` | Telegram Bot Token | ✅ | - |
| `ALLOWED_USER_IDS` | 允许的用户ID（逗号分隔） | ✅ | - |
| `OPENROUTER_API_KEY` | OpenRouter API Key | ✅ | - |
| `GOOGLE_CREDENTIALS_JSON` | Google 服务账号 JSON | ✅ | - |
| `GOOGLE_CALENDAR_ID` | 主日历 ID | ✅ | - |
| `LLM_MODEL_NAME` | AI 模型名称 | ❌ | gemini-3-flash-preview |
| `DEFAULT_HOME_TZ` | 默认时区 | ❌ | Asia/Singapore |
| `LOG_LEVEL` | 日志级别 | ❌ | INFO |

### Singbox Updater 环境变量

| 环境变量 | 说明 | 必需 | 默认值 |
|---------|------|------|--------|
| `SINGBOX_SUBSCRIPTION_URL` | 订阅 URL | ✅ | - |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | Telegram Bot Token | ⚠️ | - |
| `SINGBOX_TELEGRAM_CHAT_ID` | Telegram Chat ID | ⚠️ | - |
| `SINGBOX_ENABLE_TELEGRAM` | 启用 Telegram 通知 | ❌ | false |
| `SINGBOX_CHECK_INTERVAL_HOURS` | 检查间隔（小时） | ❌ | 6 |
| `SINGBOX_LOG_LEVEL` | 日志级别 | ❌ | INFO |

---

## 📝 使用指南

### Calendar Bot 命令

- `/start` - 显示帮助信息
- `/status` - 查看系统状态
- `/today` - 查看今日日程
- `/travel <时区>` - 切换时区（如 /travel London）
- `/home` - 切换回默认时区
- `/event <描述>` - 强制解析为事件
- `/restartsingboxupdater` - 远程重启 Singbox Updater

### 自然语言示例

**定时事件**:
- "明天下午3点开会"
- "下周五晚上7点和朋友吃饭"
- "2月14日给Janet买礼物"

**全天任务**:
- "记得买牛奶"
- "Jason的足球比赛"
- "今天给妈妈打电话"

**图片识别**:
- 发送演唱会海报
- 发送机票截图
- 发送活动邀请函

---

## 🔍 监控与维护

### 查看日志

**Zeabur 控制台**:
- 进入对应服务
- 点击 "Logs" 标签
- 实时查看日志

### 健康检查

**Calendar Bot**:
```
发送 /status 命令
检查返回的系统状态
```

**Singbox Updater**:
```
查看 Zeabur 日志
确认定时任务正常执行
```

---

## 🛠️ 故障排除

### Calendar Bot

**问题**: Bot 无响应
- 检查 Zeabur 服务是否运行
- 检查 `TELEGRAM_TOKEN` 是否正确
- 检查用户 ID 是否在 `ALLOWED_USER_IDS` 中

**问题**: 无法创建事件
- 检查 `GOOGLE_CREDENTIALS_JSON` 格式
- 确认 Service Account 有日历权限
- 查看日志中的详细错误信息

### Singbox Updater

**问题**: 订阅下载失败
- 检查 `SINGBOX_SUBSCRIPTION_URL` 是否有效
- 确认 Zeabur 网络可以访问订阅地址
- 检查订阅 URL 是否需要代理

**问题**: Telegram 通知失败
- 检查 Bot Token 和 Chat ID
- 确认 `SINGBOX_ENABLE_TELEGRAM=true`
- 查看日志中的错误信息

---

## 📚 技术栈

### Calendar Bot
- **Framework**: python-telegram-bot 20.7
- **AI**: OpenAI SDK (OpenRouter)
- **Database**: SQLAlchemy 2.0 + SQLite
- **Config**: Pydantic Settings
- **API**: Google Calendar API v3

### Singbox Updater
- **Scheduler**: schedule 1.2
- **HTTP**: requests, urllib
- **Format**: JSON parsing
- **Notification**: Telegram Bot API

---

## 🤝 贡献与维护

本项目由 Claude (AI Assistant) 负责维护和重构。

**协作规范**: 参见 [CLAUDE.md](./CLAUDE.md)

---

## 📄 变更日志

### v3.0.0 (2026-01-17)
- ✨ 完整重构代码架构
- ✨ 引入 SQLAlchemy ORM
- ✨ 使用 Pydantic 配置管理
- ✨ 模块化代码结构
- ✨ 改进错误处理和日志
- ✨ 统一代码仓库，独立部署

### v2.8 (之前)
- 单文件实现
- 原生 SQL
- 字典配置
- 功能完整但代码耦合

---

## 📞 联系方式

**项目维护者**: Kimi
**AI 助手**: Claude (Anthropic)

---

**License**: MIT
