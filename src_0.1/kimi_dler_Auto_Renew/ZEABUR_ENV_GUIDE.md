# Zeabur 环境变量配置指南

## 📋 概述

在Zeabur部署时，**所有敏感信息都应通过环境变量配置**，而不是直接写在配置文件中。这是云部署的最佳实践。

---

## 🔑 必需的环境变量

以下是部署到Zeabur时**必须配置**的环境变量：

### 1. SINGBOX_SUBSCRIPTION_URL

**说明**: Singbox订阅URL  
**类型**: 字符串  
**是否必需**: ✅ 必需  
**示例**: 
```
https://dler.cloud/api/v3/download.getFile/YOUR_TOKEN?protocols=smart&provider=singbox&lv=2%7C3%7C4%7C5%7C6%7C8.zip
```

**注意**:
- 这是你的订阅服务商提供的URL
- 包含你的认证信息，请勿公开
- URL中可能包含特殊字符，Zeabur会自动处理

---

### 2. SINGBOX_TELEGRAM_BOT_TOKEN

**说明**: Telegram Bot Token  
**类型**: 字符串  
**是否必需**: ⚠️  如果启用Telegram通知则必需  
**获取方式**: 通过 @BotFather 创建Bot后获得  
**格式**: `数字:字母数字混合`  
**示例**: 
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**注意**:
- Token相当于密码，必须保密
- 包含冒号(:)，是正常的
- 长度约45个字符

---

### 3. SINGBOX_TELEGRAM_CHAT_ID

**说明**: Telegram接收消息的Chat ID  
**类型**: 字符串（虽然是数字，但作为字符串传入）  
**是否必需**: ⚠️  如果启用Telegram通知则必需  
**获取方式**: 通过 @userinfobot 获得  
**格式**: 纯数字或负数（群组）  
**示例**: 
```
123456789
```
或（如果是群组）：
```
-100123456789
```

**注意**:
- 个人Chat ID通常是正数
- 群组Chat ID是负数
- 不要加引号（Zeabur会自动处理）

---

## ⚙️ 可选的环境变量

以下环境变量是可选的，有默认值：

### 4. SINGBOX_ENABLE_TELEGRAM

**说明**: 是否启用Telegram通知  
**类型**: 布尔值  
**默认值**: `false`（从配置文件读取）  
**可选值**: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`  
**示例**: 
```
true
```

**注意**:
- 设置为 `true` 时，必须同时配置 `SINGBOX_TELEGRAM_BOT_TOKEN` 和 `SINGBOX_TELEGRAM_CHAT_ID`
- 不区分大小写

---

### 5. SINGBOX_CHECK_INTERVAL_HOURS

**说明**: 检查订阅更新的间隔（小时）  
**类型**: 整数  
**默认值**: `6`  
**建议范围**: `2-12`  
**示例**: 
```
6
```

**注意**:
- 设置太频繁可能对订阅服务器造成压力
- 设置太长可能错过紧急更新
- 建议保持默认值6小时

---

### 6. SINGBOX_LOG_LEVEL

**说明**: 日志级别  
**类型**: 字符串  
**默认值**: `INFO`  
**可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`  
**示例**: 
```
INFO
```

**注意**:
- `DEBUG`: 详细调试信息（开发时使用）
- `INFO`: 正常运行信息（推荐）
- `WARNING`: 仅警告和错误
- `ERROR`: 仅错误信息

---

## 📊 环境变量优先级

**优先级规则**: 环境变量 > 配置文件

即：
1. 程序首先从 `config/settings.json` 读取配置
2. 然后检查环境变量
3. 如果环境变量存在，覆盖配置文件中的值

这意味着：
- ✅ 可以在配置文件中设置默认值
- ✅ 在Zeabur中通过环境变量覆盖敏感信息
- ✅ 同一份代码可以在不同环境使用不同配置

---

## 🚀 Zeabur配置步骤

### 步骤1: 部署服务

1. 在Zeabur创建新项目
2. 从GitHub导入仓库
3. Zeabur自动检测Dockerfile并构建

### 步骤2: 配置环境变量

在Zeabur控制台：

1. 进入服务详情页
2. 点击"Variables"（变量）标签
3. 添加环境变量

### 步骤3: 添加必需变量

**最小配置**（如果不使用Telegram）：

| Key | Value | 说明 |
|-----|-------|------|
| `SINGBOX_SUBSCRIPTION_URL` | `你的订阅URL` | 必需 |

**完整配置**（使用Telegram）：

| Key | Value | 说明 |
|-----|-------|------|
| `SINGBOX_SUBSCRIPTION_URL` | `你的订阅URL` | 必需 |
| `SINGBOX_ENABLE_TELEGRAM` | `true` | 启用Telegram |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | `你的Bot Token` | 必需 |
| `SINGBOX_TELEGRAM_CHAT_ID` | `你的Chat ID` | 必需 |

### 步骤4: 可选调整

| Key | Value | 说明 |
|-----|-------|------|
| `SINGBOX_CHECK_INTERVAL_HOURS` | `6` | 可选 |
| `SINGBOX_LOG_LEVEL` | `INFO` | 可选 |

### 步骤5: 保存并重启

1. 点击"Save"保存环境变量
2. 服务会自动重启
3. 查看日志确认配置生效

---

## 📸 配置示例截图说明

在Zeabur的Variables页面，应该是这样的：

```
┌─────────────────────────────────────────────────────────────┐
│ Environment Variables                                       │
├────────────────────────────┬────────────────────────────────┤
│ Key                        │ Value                          │
├────────────────────────────┼────────────────────────────────┤
│ SINGBOX_SUBSCRIPTION_URL   │ https://your-subscription...   │
│ SINGBOX_ENABLE_TELEGRAM    │ true                           │
│ SINGBOX_TELEGRAM_BOT_TOKEN │ 1234567890:ABCdefGHIjk...     │
│ SINGBOX_TELEGRAM_CHAT_ID   │ 123456789                      │
│ SINGBOX_CHECK_INTERVAL_HOURS│ 6                             │
│ SINGBOX_LOG_LEVEL          │ INFO                           │
└────────────────────────────┴────────────────────────────────┘
```

---

## ✅ 验证配置

### 方法1: 查看日志

部署后，在Zeabur的日志中应该看到：

```
📋 Configuration loaded:
   From environment variables: subscription_url, telegram_bot_token, telegram_chat_id, enable_telegram_notification
✅ Connected to Telegram Bot: @your_bot_name
✅ Telegram notifier initialized
🚀 Starting update check
```

### 方法2: 测试Telegram

如果配置正确：
- 首次运行会发送测试通知
- 或等待下次检测到更新时收到通知

### 方法3: 检查配置来源

程序会在日志中显示哪些配置来自环境变量：
```
📋 Configuration loaded:
   From environment variables: subscription_url, telegram_bot_token, telegram_chat_id
```

---

## 🔒 安全最佳实践

### ✅ 应该做的

1. **所有敏感信息都用环境变量**
   - ✅ SUBSCRIPTION_URL
   - ✅ TELEGRAM_BOT_TOKEN
   - ✅ TELEGRAM_CHAT_ID

2. **定期更换Token**
   - 定期通过 @BotFather 重新生成Bot Token
   - 在Zeabur更新环境变量

3. **使用私有仓库**
   - GitHub仓库设置为Private
   - 避免配置文件泄露

### ❌ 不应该做的

1. **不要在代码中硬编码**
   ```json
   // ❌ 错误做法
   {
     "telegram_bot_token": "1234567890:ABCdefGHI..."
   }
   ```

2. **不要提交敏感信息到Git**
   - 检查 `.gitignore` 确保 `config/settings.json` 被忽略
   - 或确保settings.json中只有默认值

3. **不要在日志中输出完整Token**
   - 程序已经做了处理
   - 日志中只显示配置来源，不显示值

---

## 🔧 故障排除

### 问题1: 订阅下载失败

**错误**: `Failed to download subscription`

**检查**:
1. `SINGBOX_SUBSCRIPTION_URL` 是否正确
2. URL是否可以访问
3. 查看Zeabur日志的详细错误

**解决**: 
- 复制URL在浏览器测试
- 确认URL格式正确
- 检查订阅是否过期

---

### 问题2: Telegram连接失败

**错误**: `Telegram connection test failed`

**检查**:
1. `SINGBOX_TELEGRAM_BOT_TOKEN` 是否正确
2. `SINGBOX_TELEGRAM_CHAT_ID` 是否正确
3. `SINGBOX_ENABLE_TELEGRAM` 是否为 `true`

**解决**:
- 确认Token完整（包括冒号）
- 先给Bot发送一条消息
- 检查Chat ID是否正确

---

### 问题3: 环境变量未生效

**症状**: 日志显示 "From config file only"

**原因**: 环境变量名称不正确或未设置

**解决**:
1. 检查环境变量Key是否完全匹配（区分大小写）
2. 正确的格式：`SINGBOX_SUBSCRIPTION_URL`（全大写，下划线分隔）
3. 保存后重启服务

---

### 问题4: 值中包含特殊字符

**症状**: URL或Token解析错误

**解决**: 
- Zeabur会自动处理URL编码
- 直接粘贴原始值即可
- 不需要手动转义

---

## 📋 环境变量清单

### 快速复制清单

复制以下内容，填入你的值：

```
# 必需配置
SINGBOX_SUBSCRIPTION_URL=
SINGBOX_TELEGRAM_BOT_TOKEN=
SINGBOX_TELEGRAM_CHAT_ID=

# Telegram开关（必需，如果要使用Telegram）
SINGBOX_ENABLE_TELEGRAM=true

# 可选配置
SINGBOX_CHECK_INTERVAL_HOURS=6
SINGBOX_LOG_LEVEL=INFO
```

---

## 🎯 不同部署场景

### 场景1: 仅自动更新，不使用Telegram

**环境变量**:
```
SINGBOX_SUBSCRIPTION_URL=你的订阅URL
```

**结果**: 
- 自动更新配置
- 文件保存在 `outputs/` 目录
- 需要手动下载

---

### 场景2: 完整功能，使用Telegram

**环境变量**:
```
SINGBOX_SUBSCRIPTION_URL=你的订阅URL
SINGBOX_ENABLE_TELEGRAM=true
SINGBOX_TELEGRAM_BOT_TOKEN=你的Token
SINGBOX_TELEGRAM_CHAT_ID=你的ChatID
```

**结果**:
- 自动更新配置
- 自动推送到Telegram
- 手机直接下载

---

### 场景3: 开发调试

**环境变量**:
```
SINGBOX_SUBSCRIPTION_URL=你的订阅URL
SINGBOX_LOG_LEVEL=DEBUG
SINGBOX_CHECK_INTERVAL_HOURS=1
```

**结果**:
- 详细的调试日志
- 每小时检查一次
- 便于测试

---

## 💡 高级技巧

### 技巧1: 本地测试环境变量

在本地测试前设置环境变量：

**Linux/Mac**:
```bash
export SINGBOX_SUBSCRIPTION_URL="https://your-url"
export SINGBOX_TELEGRAM_BOT_TOKEN="your-token"
export SINGBOX_TELEGRAM_CHAT_ID="your-chat-id"
export SINGBOX_ENABLE_TELEGRAM="true"

python main.py --mode once
```

**Windows PowerShell**:
```powershell
$env:SINGBOX_SUBSCRIPTION_URL="https://your-url"
$env:SINGBOX_TELEGRAM_BOT_TOKEN="your-token"
$env:SINGBOX_TELEGRAM_CHAT_ID="your-chat-id"
$env:SINGBOX_ENABLE_TELEGRAM="true"

python main.py --mode once
```

**Windows CMD**:
```cmd
set SINGBOX_SUBSCRIPTION_URL=https://your-url
set SINGBOX_TELEGRAM_BOT_TOKEN=your-token
set SINGBOX_TELEGRAM_CHAT_ID=your-chat-id
set SINGBOX_ENABLE_TELEGRAM=true

python main.py --mode once
```

---

### 技巧2: 使用 .env 文件（本地开发）

创建 `.env` 文件（不要提交到Git）：
```
SINGBOX_SUBSCRIPTION_URL=https://your-url
SINGBOX_TELEGRAM_BOT_TOKEN=your-token
SINGBOX_TELEGRAM_CHAT_ID=your-chat-id
SINGBOX_ENABLE_TELEGRAM=true
```

然后：
```bash
# Linux/Mac
source .env
python main.py --mode once

# 或使用 python-dotenv（需要安装）
pip install python-dotenv
```

---

### 技巧3: 多环境配置

**开发环境** (Zeabur项目A):
```
SINGBOX_CHECK_INTERVAL_HOURS=1
SINGBOX_LOG_LEVEL=DEBUG
```

**生产环境** (Zeabur项目B):
```
SINGBOX_CHECK_INTERVAL_HOURS=6
SINGBOX_LOG_LEVEL=INFO
```

同一份代码，不同配置！

---

## 📞 获取帮助

### 检查配置是否正确

1. 部署后查看Zeabur日志
2. 看到 "Configuration loaded" 和配置来源
3. 确认环境变量是否生效

### 常见错误代码

| 错误 | 原因 | 解决 |
|------|------|------|
| `KeyError: 'subscription_url'` | 环境变量未设置 | 添加 `SINGBOX_SUBSCRIPTION_URL` |
| `Telegram connection test failed` | Token或ChatID错误 | 检查Token和ChatID |
| `Failed to download subscription` | URL错误或网络问题 | 检查URL，查看详细日志 |

---

## 🎉 总结

### 环境变量的优势

✅ **安全**: 敏感信息不在代码中  
✅ **灵活**: 不同环境不同配置  
✅ **简单**: Zeabur界面直接配置  
✅ **可维护**: 修改配置不需要改代码

### 最小配置（3个变量）

对于使用Telegram的完整功能：
1. `SINGBOX_SUBSCRIPTION_URL`
2. `SINGBOX_TELEGRAM_BOT_TOKEN`
3. `SINGBOX_TELEGRAM_CHAT_ID`

**就这么简单！** 🚀

---

**版本**: v1.1.0  
**更新日期**: 2026-01-04  
**支持平台**: Zeabur, Railway, Render, 任何支持环境变量的云平台
