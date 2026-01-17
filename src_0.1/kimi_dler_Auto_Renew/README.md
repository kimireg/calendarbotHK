# Singbox Auto Updater

自动化Singbox配置更新工具，支持定期检测订阅更新并自动生成Pro和Air版本配置。

## 📋 功能特性

- ✅ **自动检测订阅更新**: 定期检查订阅URL，自动识别配置变化
- ✅ **版本控制**: 保存所有历史订阅版本，支持回滚
- ✅ **智能更新**: 严格按照skills定义更新配置，保留自定义服务器
- ✅ **自动生成**: 同时生成Pro、Air V5.9和Air V7.8三个版本
- ✅ **Telegram推送**: 更新时自动发送通知和配置文件到Telegram 🆕
- ✅ **日志记录**: 完整的更新日志和变更追踪
- ✅ **Docker部署**: 支持Zeabur等平台一键部署

## 🏗️ 项目结构

```
singbox-auto-updater/
├── config/
│   ├── base_configs/              # 基础配置文件
│   │   ├── Singbox_Pro_V5_9.json # Pro基础配置
│   │   └── initial_subscription.json # 初始订阅（可选）
│   └── settings.json              # 应用配置
├── subscription_history/          # 订阅历史版本
├── outputs/                       # 生成的配置文件
├── logs/                          # 日志文件
├── src/
│   ├── subscription_checker.py   # 订阅检查器
│   ├── updater.py                # Pro配置更新器
│   ├── generator.py              # Air版本生成器
│   └── scheduler.py              # 定时任务调度
├── main.py                        # 主程序
├── requirements.txt               # Python依赖
├── Dockerfile                     # Docker配置
└── README.md                      # 本文档
```

## 🚀 快速开始

### 方式1：本地运行

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **准备配置文件**

将你的基础Pro配置放在：
```
config/base_configs/Singbox_Pro_V5_9.json
```

3. **配置settings.json**

编辑 `config/settings.json`，设置你的订阅URL等参数。

4. **运行**

定时运行（默认每6小时检查一次）：
```bash
python main.py --mode schedule
```

单次运行（测试用）：
```bash
python main.py --mode once
```

### 方式2：Docker运行

1. **构建镜像**
```bash
docker build -t singbox-auto-updater .
```

2. **运行容器**
```bash
docker run -d \
  --name singbox-updater \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/subscription_history:/app/subscription_history \
  singbox-auto-updater
```

### 方式3：Zeabur部署

1. **准备代码仓库**

将整个项目上传到GitHub

2. **在Zeabur创建服务**

- 选择你的GitHub仓库
- Zeabur会自动检测Dockerfile
- 自动构建和部署

3. **配置环境变量**（可选）

在Zeabur中可以设置环境变量来覆盖默认配置。

## ⚙️ 配置说明

### 配置方式

**方式1: 配置文件** (本地开发)

编辑 `config/settings.json`:
```json
{
  "subscription_url": "订阅URL",
  "enable_telegram_notification": true,
  "telegram_bot_token": "你的Bot Token",
  "telegram_chat_id": "你的Chat ID"
}
```

**方式2: 环境变量** (云部署推荐) ✨

通过环境变量配置（优先级高于配置文件）：

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `SINGBOX_SUBSCRIPTION_URL` | 订阅URL | ✅ |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | Bot Token | ⚠️ 使用Telegram时 |
| `SINGBOX_TELEGRAM_CHAT_ID` | Chat ID | ⚠️ 使用Telegram时 |
| `SINGBOX_ENABLE_TELEGRAM` | 启用Telegram | 可选 |
| `SINGBOX_CHECK_INTERVAL_HOURS` | 检查间隔(小时) | 可选(默认6) |
| `SINGBOX_LOG_LEVEL` | 日志级别 | 可选(默认INFO) |

**环境变量配置**: 详见 [ZEABUR_ENV_GUIDE.md](ZEABUR_ENV_GUIDE.md)  
**快速参考**: [ENV_QUICK_REF.md](ENV_QUICK_REF.md)

### 配置优先级

```
环境变量 > 配置文件
```

这意味着：
- 可以在配置文件设置默认值
- 在Zeabur等平台通过环境变量覆盖敏感信息
- 同一份代码可用于不同环境

### 参数说明

- `subscription_url`: 你的Singbox订阅URL
- `base_config_path`: Pro基础配置文件路径
- `check_interval_hours`: 检查间隔（小时），默认6小时
- `log_level`: 日志级别（DEBUG, INFO, WARNING, ERROR）
- `enable_telegram_notification`: 是否启用Telegram通知 🆕
- `telegram_bot_token`: Telegram Bot Token 🆕
- `telegram_chat_id`: 接收消息的Chat ID 🆕

**Telegram配置**: 详见 [TELEGRAM_GUIDE.md](TELEGRAM_GUIDE.md)

## 📝 配置文件要求

### 基础Pro配置 (Singbox_Pro_V5_9.json)

需要包含以下自定义服务器（如果有）：
- SGNowaHomePlus
- SGoffice

配置格式应符合Singbox标准格式，包含：
- `outbounds`: 服务器列表
- `route`: 路由规则
- `dns`: DNS配置

### 文件命名规范

- Pro配置: `Singbox_Pro_V{version}.json`
- 订阅历史: `subscription_{timestamp}.json`
- 输出文件: 自动生成带时间戳的文件名

## 🔄 工作流程

```
1. 定时检查订阅URL
   ↓
2. 下载并解析最新订阅
   ↓
3. 与历史版本对比hash
   ↓
4. 如有变化 → 保存新版本
   ↓
5. 执行更新流程：
   - 步骤1: 更新Pro配置 (singbox-updater)
   - 步骤2: 生成Air版本 (singbox-air-generator)
   ↓
6. 生成三个配置文件：
   - Singbox_Pro_V5_9_Updated_{timestamp}.json
   - Singbox_Air_V5_9_Generated.json
   - Singbox_Air_V7_8_Generated.json
   ↓
7. 记录日志
```

## 📊 生成的配置说明

### Pro版本
- 完整功能配置
- 包含所有订阅服务器
- 保留自定义服务器
- 完整路由规则

### Air V5.9（个人简化版）
- 移除应用路由组（YouTube, Netflix, Apple等）
- **保留AllServer组**（可手动选择所有服务器）
- 保留自定义服务器
- 简化路由规则
- 适合日常使用

### Air V7.8（朋友试用版）
- 保留所有功能组
- **移除自定义服务器**
- 完整路由规则
- 可安全分享

## 🔍 监控和维护

### 查看日志

日志文件位于 `logs/` 目录：
```bash
tail -f logs/updater_20260104.log
```

### 查看订阅历史

所有历史订阅版本保存在 `subscription_history/`：
```bash
ls -lh subscription_history/
```

### 查看输出文件

生成的配置文件在 `outputs/`：
```bash
ls -lh outputs/
```

## 🛠️ 故障排除

### 订阅下载失败

**问题**: 403 Forbidden 错误

**解决方法**: 订阅URL可能需要代理访问。在Zeabur等平台部署时，确保网络可以访问订阅URL。

### 配置更新失败

**问题**: 自定义服务器丢失

**解决方法**: 检查基础配置文件中是否包含自定义服务器定义。

### Docker容器无法启动

**问题**: 文件权限问题

**解决方法**: 确保挂载的目录有正确的读写权限。

## 📈 扩展功能

### Telegram通知（已实现）✅

配置后每次更新会自动：
1. 发送更新通知（包含变更摘要）
2. 发送三个配置文件到Telegram

**配置教程**: [TELEGRAM_GUIDE.md](TELEGRAM_GUIDE.md)

### 添加其他通知方式

可以在 `src/telegram_notifier.py` 的基础上实现：
- 邮件通知
- 企业微信通知
- 钉钉通知
- Webhook通知

### 自定义检查间隔

修改 `config/settings.json` 中的 `check_interval_hours`。

### 添加更多Air版本

在 `src/generator.py` 中添加新的生成方法。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

## 🙏 致谢

基于以下skills开发：
- singbox-updater
- singbox-air-generator

---

**作者**: Kimi  
**版本**: 1.0.0  
**最后更新**: 2026-01-04
