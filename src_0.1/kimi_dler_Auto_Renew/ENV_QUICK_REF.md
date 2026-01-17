# 🔑 环境变量快速参考卡

> 打印或保存此页面，在Zeabur配置时查阅

---

## 📋 环境变量映射表

| 环境变量 Key | 对应配置项 | 类型 | 必需 |
|-------------|-----------|------|------|
| `SINGBOX_SUBSCRIPTION_URL` | subscription_url | 字符串 | ✅ 必需 |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | telegram_bot_token | 字符串 | ⚠️  使用Telegram时必需 |
| `SINGBOX_TELEGRAM_CHAT_ID` | telegram_chat_id | 字符串 | ⚠️  使用Telegram时必需 |
| `SINGBOX_ENABLE_TELEGRAM` | enable_telegram_notification | 布尔 | 可选 (默认false) |
| `SINGBOX_CHECK_INTERVAL_HOURS` | check_interval_hours | 整数 | 可选 (默认6) |
| `SINGBOX_LOG_LEVEL` | log_level | 字符串 | 可选 (默认INFO) |

---

## ✅ 最小配置（不使用Telegram）

```
SINGBOX_SUBSCRIPTION_URL = 你的订阅URL
```

**就一个变量！**

---

## ✅ 推荐配置（使用Telegram）

```
SINGBOX_SUBSCRIPTION_URL = 你的订阅URL
SINGBOX_ENABLE_TELEGRAM = true
SINGBOX_TELEGRAM_BOT_TOKEN = 你的Bot Token
SINGBOX_TELEGRAM_CHAT_ID = 你的Chat ID
```

**4个变量，完整功能！**

---

## 📝 变量详细说明

### 1️⃣ SINGBOX_SUBSCRIPTION_URL

**示例值**:
```
https://dler.cloud/api/v3/download.getFile/YOUR_TOKEN?protocols=smart&provider=singbox&lv=2%7C3%7C4%7C5%7C6%7C8.zip
```

**获取方式**: 订阅服务商提供  
**注意**: 包含认证信息，勿公开

---

### 2️⃣ SINGBOX_TELEGRAM_BOT_TOKEN

**示例值**:
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**获取方式**: 
1. Telegram搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示创建Bot
4. 复制Token

**格式**: `数字:字母数字`（约45字符）

---

### 3️⃣ SINGBOX_TELEGRAM_CHAT_ID

**示例值**:
```
123456789
```

**获取方式**:
1. Telegram搜索 `@userinfobot`
2. 发送 `/start`
3. 复制显示的ID

**格式**: 
- 个人: 纯数字（正数）
- 群组: 负数（如 `-100123456789`）

---

### 4️⃣ SINGBOX_ENABLE_TELEGRAM

**可选值**: `true`, `false`, `1`, `0`, `yes`, `no`

**推荐值**: `true`

**说明**: 
- 设为 `true` 时必须同时配置Token和ChatID
- 不设置则从配置文件读取

---

### 5️⃣ SINGBOX_CHECK_INTERVAL_HOURS

**可选值**: 任意正整数

**推荐值**: `6`（6小时）

**范围建议**: `2-12`

**说明**:
- 太频繁: 对服务器压力大
- 太长: 可能错过更新
- 默认6小时是平衡点

---

### 6️⃣ SINGBOX_LOG_LEVEL

**可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**推荐值**: `INFO`

**说明**:
- `DEBUG`: 详细日志（调试用）
- `INFO`: 正常信息（推荐）
- `WARNING`: 仅警告
- `ERROR`: 仅错误

---

## 🎯 配置优先级

```
环境变量 > 配置文件

即: 环境变量会覆盖config/settings.json中的值
```

**优势**: 
- ✅ 代码中可以有默认值
- ✅ Zeabur中覆盖敏感信息
- ✅ 同一代码多环境部署

---

## 🚀 Zeabur配置步骤

### 1. 进入服务

Zeabur控制台 → 选择服务 → Variables标签

### 2. 添加变量

点击 "Add Variable" 或 "+"

### 3. 填写Key和Value

参考上面的映射表填写

### 4. 保存

点击 "Save" → 服务自动重启

---

## ✅ 配置检查清单

部署前检查：

- [ ] `SINGBOX_SUBSCRIPTION_URL` 已填写
- [ ] 如果使用Telegram:
  - [ ] `SINGBOX_ENABLE_TELEGRAM` 设为 `true`
  - [ ] `SINGBOX_TELEGRAM_BOT_TOKEN` 已填写
  - [ ] `SINGBOX_TELEGRAM_CHAT_ID` 已填写
- [ ] 可选配置已根据需要设置
- [ ] 所有Key名称完全匹配（区分大小写）

---

## 🔍 验证配置

### 查看Zeabur日志

部署后应该看到：

```
📋 Configuration loaded:
   From environment variables: subscription_url, telegram_bot_token, telegram_chat_id, enable_telegram_notification
✅ Connected to Telegram Bot: @your_bot_name
✅ Telegram notifier initialized
```

### Telegram测试

- 收到连接测试消息
- 或等待下次更新时收到通知

---

## ⚠️ 常见错误

### 错误1: Token格式错误

**症状**: `Telegram connection test failed`

**检查**:
- Token是否完整（包括冒号）
- 是否复制时有多余空格
- 格式: `数字:字母数字`

---

### 错误2: Chat ID错误

**症状**: 消息发送失败

**检查**:
- ID是否正确
- 是否给Bot发送过消息（激活对话）
- 个人是正数，群组是负数

---

### 错误3: URL编码问题

**症状**: 订阅下载失败

**解决**:
- 直接粘贴原始URL
- Zeabur会自动处理编码
- 不需要手动转义

---

### 错误4: 环境变量未生效

**症状**: 日志显示 "From config file only"

**原因**: Key名称不正确

**解决**:
- 检查拼写（区分大小写）
- 确保格式: `SINGBOX_SUBSCRIPTION_URL`（全大写）
- 保存后重启服务

---

## 💡 快速测试

### 本地测试环境变量

**Linux/Mac**:
```bash
export SINGBOX_SUBSCRIPTION_URL="https://your-url"
export SINGBOX_ENABLE_TELEGRAM="true"
export SINGBOX_TELEGRAM_BOT_TOKEN="your-token"
export SINGBOX_TELEGRAM_CHAT_ID="your-chat-id"

python main.py --mode once
```

**Windows**:
```cmd
set SINGBOX_SUBSCRIPTION_URL=https://your-url
set SINGBOX_ENABLE_TELEGRAM=true
set SINGBOX_TELEGRAM_BOT_TOKEN=your-token
set SINGBOX_TELEGRAM_CHAT_ID=your-chat-id

python main.py --mode once
```

---

## 📸 Zeabur配置示例

在Variables页面应该是这样：

```
┌──────────────────────────────┬──────────────────────────┐
│ Key                          │ Value                    │
├──────────────────────────────┼──────────────────────────┤
│ SINGBOX_SUBSCRIPTION_URL     │ https://dler.cloud/...   │
│ SINGBOX_ENABLE_TELEGRAM      │ true                     │
│ SINGBOX_TELEGRAM_BOT_TOKEN   │ 1234567890:ABCdef...     │
│ SINGBOX_TELEGRAM_CHAT_ID     │ 123456789                │
│ SINGBOX_CHECK_INTERVAL_HOURS │ 6                        │
│ SINGBOX_LOG_LEVEL            │ INFO                     │
└──────────────────────────────┴──────────────────────────┘
```

---

## 🔒 安全提醒

### ✅ 应该做

1. 所有敏感信息用环境变量
2. 使用私有GitHub仓库
3. 定期更换Bot Token

### ❌ 不应该做

1. 不要在代码中硬编码Token
2. 不要提交包含敏感信息的配置文件
3. 不要在公开场合分享环境变量截图

---

## 📞 需要帮助？

1. 查看完整指南: `ZEABUR_ENV_GUIDE.md`
2. 查看Zeabur日志的详细错误
3. 参考常见错误解决方案

---

## 📋 复制清单

```
# === 必需配置 ===
SINGBOX_SUBSCRIPTION_URL=
SINGBOX_ENABLE_TELEGRAM=true
SINGBOX_TELEGRAM_BOT_TOKEN=
SINGBOX_TELEGRAM_CHAT_ID=

# === 可选配置 ===
SINGBOX_CHECK_INTERVAL_HOURS=6
SINGBOX_LOG_LEVEL=INFO
```

**填写你的值后，逐条添加到Zeabur！**

---

**保存此卡片备用！** 📌

---

**版本**: v1.1.0  
**支持平台**: Zeabur, Railway, Render等  
**更新日期**: 2026-01-04
