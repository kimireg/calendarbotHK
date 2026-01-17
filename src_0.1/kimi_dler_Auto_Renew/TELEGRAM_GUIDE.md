# Telegram Bot 配置指南

## 🤖 功能说明

配置Telegram Bot后，每次检测到订阅更新时，程序会自动：
1. 发送更新通知消息（包含变更摘要）
2. 发送三个配置文件：
   - Pro V5.9 Updated（完整版）
   - Air V5.9（个人简化版）
   - Air V7.8（朋友分享版）

这样你就能在手机上立即收到通知并下载最新配置！📱

---

## 🚀 快速配置（5分钟）

### 步骤1: 创建Telegram Bot（2分钟）

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示设置Bot名称和用户名
4. 获得Bot Token（类似：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

**保存这个Token！** ⚠️

### 步骤2: 获取Chat ID（2分钟）

#### 方法1: 使用 @userinfobot（推荐）

1. 在Telegram中搜索 `@userinfobot`
2. 点击Start或发送 `/start`
3. Bot会返回你的信息，找到 `Id:` 后面的数字
4. 这就是你的Chat ID（类似：`123456789`）

#### 方法2: 使用 @RawDataBot

1. 在Telegram中搜索 `@RawDataBot`
2. 发送任意消息
3. 在返回的JSON中找到 `"id": 123456789`

#### 方法3: 通过API

1. 给你的Bot发送一条消息（任意内容）
2. 在浏览器访问：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. 在返回的JSON中找到 `"chat":{"id": 123456789}`

### 步骤3: 配置程序（1分钟）

编辑 `config/settings.json`：

```json
{
  "enable_telegram_notification": true,
  "telegram_bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "telegram_chat_id": "123456789"
}
```

**注意**:
- `telegram_chat_id` 是数字，但要用引号包起来作为字符串
- 如果是私人群组，Chat ID可能是负数（如 `"-100123456789"`）

### 步骤4: 测试（30秒）

运行测试：
```bash
python main.py --mode once
```

如果配置正确，你会：
1. 在终端看到 `✅ Connected to Telegram Bot: @your_bot_name`
2. 如果有更新，会收到Telegram消息和文件

---

## 📋 完整配置示例

```json
{
  "subscription_url": "https://your-subscription-url",
  "base_config_path": "config/base_configs/Singbox_Pro_V5_9.json",
  "check_interval_hours": 6,
  "enable_telegram_notification": true,
  "telegram_bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "telegram_chat_id": "123456789"
}
```

---

## 📱 接收通知示例

当有更新时，你会在Telegram收到：

### 消息内容
```
🔄 Singbox配置更新通知

📦 版本: subscription_20260104_103045
⏰ 时间: 2026-01-04 10:30:45

📊 变更摘要:
• 新增服务器: 2 个
• 移除服务器: 0 个
• 配置更新: 5 个
• 服务器总数: 36 → 38

📁 生成的配置文件:
1️⃣ Pro V5.9 Updated (完整版)
2️⃣ Air V5.9 (个人简化版)
3️⃣ Air V7.8 (朋友分享版)

⬇️ 正在发送配置文件...
```

### 文件说明

紧接着会收到3个JSON文件，每个文件都有说明：

**文件1**: Singbox_Pro_V5_9_Updated_20260104_103045.json
```
📋 Pro V5.9 Updated
完整功能版，包含所有订阅服务器和自定义服务器
```

**文件2**: Singbox_Air_V5_9_Generated.json
```
📱 Air V5.9
个人简化版，保留AllServer组和自定义服务器
```

**文件3**: Singbox_Air_V7_8_Generated.json
```
👥 Air V7.8
朋友分享版，已移除自定义服务器，可安全分享
```

---

## 🔧 高级配置

### 发送到群组

如果要发送到Telegram群组：

1. 将Bot添加到群组
2. 给Bot管理员权限（或至少允许发送消息）
3. 获取群组Chat ID（通常是负数，如 `-100123456789`）
4. 在配置中使用群组的Chat ID

### 发送到频道

1. 将Bot添加为频道管理员
2. 获取频道Chat ID（格式：`@channel_username` 或 `-100123456789`）
3. 在配置中使用频道ID

### 多个接收者

如果要发送给多个人：
1. 创建一个群组
2. 将所有需要接收的人加入群组
3. 使用群组的Chat ID

---

## 🔍 故障排除

### Bot Token无效

**症状**: `Telegram connection test failed`

**解决**:
1. 检查Token是否正确复制（包括冒号前后）
2. 确认Bot未被删除
3. Token格式：`数字:字母数字组合`

### Chat ID无效

**症状**: 消息未收到

**解决**:
1. 确认Chat ID正确
2. 先给Bot发送一条消息（激活对话）
3. 如果是群组，确认Bot在群组中

### 文件发送失败

**症状**: 收到通知但没有文件

**解决**:
1. 检查文件大小（Telegram限制单文件50MB）
2. 确认Bot有发送文件权限
3. 检查网络连接

### 连接超时

**症状**: `Failed to connect to Telegram`

**解决**:
1. 检查网络连接
2. 确认可以访问 `api.telegram.org`
3. 如在国内，可能需要代理

---

## 🔒 安全建议

### 保护Bot Token

⚠️ **Bot Token相当于密码，务必保密！**

- ❌ 不要提交到公开的GitHub仓库
- ✅ 使用环境变量或私有配置文件
- ✅ 定期更换Token（通过 @BotFather）

### 保护Chat ID

- Chat ID相对安全，但建议不要公开
- 只给可信任的人使用你的Bot

### 建议设置

在 @BotFather 中设置：
- `/setprivacy` - 设置为ENABLED（仅响应直接消息）
- `/setjoingroups` - 设置为DISABLED（禁止被添加到群组）

---

## 💡 使用技巧

### 静音通知

如果不想被打扰：
1. 右键点击Bot对话
2. 选择"静音通知"
3. 仍会收到消息，但不会有声音提醒

### 自动下载

在Telegram设置中：
- 设置 → 数据和存储 → 自动下载媒体
- 可以选择自动下载文件

### 快速访问

将Bot对话置顶：
1. 右键点击对话
2. 选择"置顶对话"

---

## 🧪 测试通知

### 方法1: 测试连接

```bash
python -c "
from src.telegram_notifier import TelegramNotifier
notifier = TelegramNotifier('YOUR_BOT_TOKEN', 'YOUR_CHAT_ID')
if notifier.test_connection():
    notifier.send_message('🎉 测试成功！Telegram通知已配置完成。')
"
```

### 方法2: 强制触发更新

修改订阅历史文件，让程序检测到"变化"：
```bash
rm -rf subscription_history/*
python main.py --mode once
```

---

## 📊 通知内容自定义

如需自定义通知内容，可以编辑：
```
src/telegram_notifier.py
```

修改 `_format_update_message` 方法来改变消息格式。

---

## ❓ 常见问题

**Q: 可以发送到多个Chat ID吗？**
A: 当前版本支持一个Chat ID。如需多个接收者，建议创建群组。

**Q: 文件会占用Telegram存储空间吗？**
A: 是的，但可以随时删除。建议定期清理旧文件。

**Q: 可以不发送文件，只发送通知吗？**
A: 可以，修改 `main.py` 中的 `send_update_notification` 调用即可。

**Q: 可以修改文件说明文字吗？**
A: 可以，编辑 `src/telegram_notifier.py` 的 `_get_file_caption` 方法。

**Q: 发送失败会重试吗？**
A: 当前版本不会重试，但会记录到日志。可自行添加重试逻辑。

---

## 🎓 进阶功能

### 添加按钮

可以在消息中添加内联按钮，例如：
- "查看详细变更"
- "下载历史版本"
- "停止更新"

需要修改 `send_message` 方法，添加 `reply_markup` 参数。

### 命令交互

可以让Bot响应命令，例如：
- `/status` - 查看当前状态
- `/check` - 立即检查更新
- `/history` - 查看历史版本

需要添加命令处理逻辑。

### Webhook模式

当前使用的是主动发送，也可以改用Webhook模式：
- Bot响应用户命令
- 用户主动请求配置文件
- 更复杂的交互

---

## 📞 获取帮助

如有问题：
1. 查看日志文件 `logs/updater_*.log`
2. 检查Telegram Bot API文档
3. 测试Bot连接 `test_connection()`

**Telegram Bot API文档**: https://core.telegram.org/bots/api

---

**配置完成！** 🎉

现在每次订阅更新时，你都会在Telegram收到通知和最新配置文件。
