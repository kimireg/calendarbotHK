# 环境变量清单

> 快速参考：所有服务的环境变量配置

**更新时间**: 2026-01-17

---

## 📋 Calendar Bot

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TELEGRAM_TOKEN` | Telegram Bot Token | `123456:ABC-DEF1234...` |
| `ALLOWED_USER_IDS` | 授权用户ID（逗号分隔） | `123456789,987654321` |
| `OPENROUTER_API_KEY` | OpenRouter API密钥 | `sk-or-v1-xxxxx` |
| `GOOGLE_CREDENTIALS_JSON` | Google Service Account JSON（单行） | `{"type":"service_account",...}` |
| `GOOGLE_CALENDAR_ID` | 主日历ID | `your@gmail.com` |

### 可选变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_MODEL_NAME` | `google/gemini-3-flash-preview` | LLM模型名称 |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API地址 |
| `DEFAULT_HOME_TZ` | `Asia/Singapore` | 默认时区 |
| `DB_PATH` | `data/calendar_bot_v2.db` | 数据库路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 家庭成员日历（可选）

| 变量名 | 说明 |
|--------|------|
| `GOOGLE_CALENDAR_ID_KIKI` | Kiki的日历ID |
| `GOOGLE_CALENDAR_ID_JASON` | Jason的日历ID |
| `GOOGLE_CALENDAR_ID_JANET` | Janet的日历ID |
| `GOOGLE_CALENDAR_ID_FAMILY` | 家庭共享日历ID |

### Zeabur远程控制（可选）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ZEABUR_API_TOKEN` | Zeabur API Token | `zbt_xxxxx` |
| `ZEABUR_TARGETS` | 远程服务配置（JSON） | 见下方示例 |

**ZEABUR_TARGETS 示例**:
```json
{
  "singbox": {
    "service_id": "xxx",
    "env_id": "yyy",
    "name": "Singbox Updater"
  }
}
```

---

## 📦 Singbox Updater

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SINGBOX_SUBSCRIPTION_URL` | 订阅地址 | `https://example.com/sub` |

### Telegram通知（强烈推荐）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SINGBOX_ENABLE_TELEGRAM` | 启用Telegram通知 | `true` |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | Bot Token | `123456:ABC-DEF...` |
| `SINGBOX_TELEGRAM_CHAT_ID` | Chat ID | `123456789` |

### 可选变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SINGBOX_CHECK_INTERVAL_HOURS` | `6` | 检查间隔（小时） |
| `SINGBOX_LOG_LEVEL` | `INFO` | 日志级别 |

---

## 🔍 如何获取这些值

### Telegram Bot Token
1. 在 Telegram 找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按提示操作，获取 Token

### Telegram User ID
方法 1: 发送消息给 [@userinfobot](https://t.me/userinfobot)
方法 2: 发送消息给 [@RawDataBot](https://t.me/RawDataBot)

### Telegram Chat ID
- 如果是个人聊天：Chat ID = User ID
- 如果是群组：使用 [@RawDataBot](https://t.me/RawDataBot) 在群组中获取

### Google Credentials JSON
1. 访问 [Google Cloud Console](https://console.cloud.google.com)
2. 创建服务账号（Service Account）
3. 下载 JSON 密钥文件
4. **重要**: 将多行 JSON 压缩成单行

**压缩方法**:
```bash
# Linux/Mac
cat credentials.json | jq -c

# 或者手动去除所有换行符
```

### Google Calendar ID
- **主日历**: 通常是你的 Gmail 地址（如 `your@gmail.com`）
- **其他日历**:
  1. 打开 Google Calendar
  2. 找到目标日历 → 设置
  3. 向下滚动找到 "日历 ID"

### Zeabur API Token
1. 登录 [Zeabur Dashboard](https://dash.zeabur.com)
2. 进入 Account Settings
3. 找到 "API Tokens"
4. 创建新 Token

### Zeabur Service ID & Environment ID
在 Zeabur 服务页面 URL 中：
```
https://dash.zeabur.com/projects/{project_id}/services/{service_id}?environmentID={env_id}
```

---

## ✅ 配置检查清单

### Calendar Bot 部署前
- [ ] 已获取 Telegram Bot Token
- [ ] 已获取你的 Telegram User ID
- [ ] 已创建 Google Service Account
- [ ] 已下载并压缩 Google Credentials JSON
- [ ] 已将 Service Account 添加到 Google Calendar
- [ ] 已获取 Google Calendar ID
- [ ] 已配置 OpenRouter API Key

### Singbox Updater 部署前
- [ ] 已获取订阅 URL
- [ ] 已决定是否启用 Telegram 通知
- [ ] 如启用通知，已准备 Bot Token 和 Chat ID

---

## 🚨 常见错误

### 错误 1: `GOOGLE_CREDENTIALS_JSON` 格式错误
**错误信息**: `JSON parsing error`

**原因**: JSON 包含换行符或格式不正确

**解决**:
1. 确保 JSON 是单行
2. 去除所有 `\n` 换行符
3. 验证 JSON 格式：使用 [JSONLint](https://jsonlint.com/)

### 错误 2: `ALLOWED_USER_IDS` 解析失败
**错误信息**: `invalid literal for int()`

**原因**: 格式不正确（有空格、非数字字符等）

**正确格式**: `123456789,987654321` （逗号分隔，无空格）
**错误格式**: `123456789, 987654321` （逗号后有空格❌）

### 错误 3: Google Calendar 权限不足
**错误信息**: `403 Forbidden`

**原因**: Service Account 没有日历编辑权限

**解决**:
1. 打开 Google Calendar
2. 找到目标日历 → 设置与共享
3. 添加 Service Account 邮箱（在 JSON 中的 `client_email`）
4. 权限设置为 "进行更改和管理共享设置"

---

**最后更新**: 2026-01-17
**文档版本**: 1.0.0
