# Zeabur 部署指南

## 📋 准备工作

### 1. 准备配置文件

在 `config/base_configs/` 目录下准备你的基础配置：

```
config/base_configs/Singbox_Pro_V5_9.json
```

这个文件应该包含：
- 你的基础Singbox配置
- 自定义服务器（如 SGNowaHomePlus, SGoffice）
- DNS、路由等其他配置

### 2. 配置订阅URL

编辑 `config/settings.json`：

```json
{
  "subscription_url": "你的订阅URL",
  "check_interval_hours": 6
}
```

## 🚀 部署到Zeabur

### 步骤1：上传到GitHub

1. 创建新的GitHub仓库
2. 上传所有代码：

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

### 步骤2：在Zeabur创建服务

1. 登录 [Zeabur](https://zeabur.com)
2. 创建新项目
3. 添加服务 → 从GitHub导入
4. 选择你的仓库
5. Zeabur会自动检测Dockerfile并部署

### 步骤3：配置环境变量（重要）

**推荐方式**: 使用环境变量配置敏感信息

在Zeabur服务设置中添加环境变量：

#### 必需的环境变量

| Key | Value | 说明 |
|-----|-------|------|
| `SINGBOX_SUBSCRIPTION_URL` | 你的订阅URL | 必需 |
| `SINGBOX_ENABLE_TELEGRAM` | `true` | 如果使用Telegram |
| `SINGBOX_TELEGRAM_BOT_TOKEN` | 你的Bot Token | 如果使用Telegram |
| `SINGBOX_TELEGRAM_CHAT_ID` | 你的Chat ID | 如果使用Telegram |

#### 可选的环境变量

| Key | Value | 说明 |
|-----|-------|------|
| `SINGBOX_CHECK_INTERVAL_HOURS` | `6` | 检查间隔（小时） |
| `SINGBOX_LOG_LEVEL` | `INFO` | 日志级别 |

**详细配置指南**: 见 [ZEABUR_ENV_GUIDE.md](ZEABUR_ENV_GUIDE.md)  
**快速参考**: 见 [ENV_QUICK_REF.md](ENV_QUICK_REF.md)

---

### 步骤4：配置持久化存储（重要）

Zeabur默认不持久化数据，需要配置Volume：

在Zeabur服务设置中添加Volume挂载：
- `/app/subscription_history` → 订阅历史
- `/app/outputs` → 输出文件
- `/app/logs` → 日志文件

### 步骤4：配置环境变量（可选）

可以通过环境变量覆盖配置：

```
CHECK_INTERVAL_HOURS=6
LOG_LEVEL=INFO
```

## 📊 监控运行状态

### 查看日志

在Zeabur控制台的服务详情页可以查看实时日志：
- 启动日志
- 更新检查日志
- 错误日志

### 访问输出文件

通过Zeabur的文件浏览器或API访问 `/app/outputs` 目录获取生成的配置文件。

## 🔄 自动更新流程

部署后，服务会自动：

1. 每6小时（默认）检查订阅更新
2. 如发现变化，自动更新配置
3. 生成三个版本的配置文件
4. 记录详细日志

## 📥 下载配置文件

### 方式1：通过Zeabur控制台

在服务详情 → 文件浏览器 → `outputs/` 目录下载

### 方式2：配置Webhook（推荐）

在 `main.py` 的 `_send_notification` 方法中实现：
- 自动上传到对象存储（S3, OSS等）
- 发送到Webhook通知
- 推送到指定服务器

## ⚙️ 高级配置

### 更改检查频率

编辑 `config/settings.json`：
```json
{
  "check_interval_hours": 2  // 改为2小时检查一次
}
```

### 启用通知

```json
{
  "enable_notifications": true,
  "notification_webhook": "your-webhook-url"
}
```

然后在代码中实现通知逻辑。

## 🔧 故障排除

### 服务无法启动

1. 检查Dockerfile是否正确
2. 确认 `config/base_configs/Singbox_Pro_V5_9.json` 存在
3. 查看Zeabur日志中的错误信息

### 订阅下载失败

如果订阅URL需要特定网络环境：
1. 可以考虑使用代理服务
2. 或在本地运行，定期手动上传订阅文件

### 配置文件无法保存

确保在Zeabur中正确配置了Volume挂载。

## 💡 最佳实践

1. **定期备份**: 定期下载 `outputs/` 目录的配置文件
2. **版本控制**: `subscription_history/` 保留了所有历史版本
3. **监控日志**: 定期查看日志确保服务正常运行
4. **测试更新**: 在本地先运行 `--mode once` 测试

## 📞 支持

如有问题，请查看：
- 项目README
- Zeabur文档
- GitHub Issues

---

**部署时间**: 预计5-10分钟  
**运行环境**: Python 3.12  
**资源需求**: 最小配置即可（CPU: 0.5核, 内存: 512MB）
