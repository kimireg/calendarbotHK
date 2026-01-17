# 配置文件说明

## 📁 必需的配置文件

### 1. Singbox_Pro_V5_9.json

**位置**: `config/base_configs/Singbox_Pro_V5_9.json`

**作用**: 这是你的基础Pro配置，会被用作更新的模板。

**要求**:
- 包含完整的Singbox配置结构
- 如果有自定义服务器，必须在此定义
- 包含DNS、路由等完整配置

**示例结构**:
```json
{
  "log": { ... },
  "dns": { ... },
  "inbounds": [ ... ],
  "outbounds": [
    // 自定义服务器（如果有）
    {
      "type": "shadowsocks",
      "tag": "SGNowaHomePlus",
      "server": "your-server",
      ...
    },
    {
      "type": "shadowsocks",
      "tag": "SGoffice",
      "server": "your-server",
      ...
    },
    // 服务器组
    {
      "type": "selector",
      "tag": "Proxy",
      "outbounds": [...]
    },
    {
      "type": "urltest",
      "tag": "HKonly",
      "outbounds": [...]
    },
    ...
  ],
  "route": { ... }
}
```

### 2. settings.json

**位置**: `config/settings.json`

**作用**: 应用程序配置

**完整示例**:
```json
{
  "subscription_url": "https://dler.cloud/api/v3/download.getFile/YOUR_TOKEN?protocols=smart&provider=singbox&lv=2%7C3%7C4%7C5%7C6%7C8.zip",
  "base_config_path": "config/base_configs/Singbox_Pro_V5_9.json",
  "subscription_history_dir": "subscription_history",
  "output_dir": "outputs",
  "log_dir": "logs",
  "check_interval_hours": 6,
  "log_level": "INFO",
  "enable_notifications": false,
  "notification_webhook": ""
}
```

**参数说明**:

- `subscription_url`: 
  - **必填**
  - 你的Singbox订阅URL
  - 示例: `https://your-provider.com/api/download?token=xxx`

- `base_config_path`:
  - **必填**
  - Pro基础配置文件路径
  - 默认: `config/base_configs/Singbox_Pro_V5_9.json`

- `check_interval_hours`:
  - **可选**
  - 检查订阅更新的间隔（小时）
  - 默认: `6`（每6小时检查一次）
  - 建议: 2-12小时之间

- `log_level`:
  - **可选**
  - 日志级别
  - 选项: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - 默认: `INFO`

- `enable_notifications`:
  - **可选**
  - 是否启用更新通知
  - 默认: `false`

- `notification_webhook`:
  - **可选**
  - Webhook URL（需要先实现通知逻辑）
  - 默认: `""`

## 📝 自定义服务器说明

### 默认自定义服务器

程序默认会保留以下自定义服务器：
- `SGNowaHomePlus`
- `SGoffice`

### 如何修改

如果你有不同的自定义服务器名称，需要修改源代码：

**修改文件**: `src/updater.py` 和 `src/generator.py`

```python
# 找到这一行
self.custom_servers = ['SGNowaHomePlus', 'SGoffice']

# 改为你的服务器名称
self.custom_servers = ['YourCustomServer1', 'YourCustomServer2']
```

## 🔄 更新逻辑说明

### Pro配置更新

程序会：
1. 从订阅下载最新服务器列表
2. 按地区分类（HK/SG/US/JP）
3. 更新以下服务器组：
   - `HKonly`: 香港+台湾
   - `SGonly`: 新加坡
   - `USonly`: 美国
   - `AllServer`: 所有服务器
4. **保留自定义服务器**
5. 保留DNS、路由等其他配置不变

### Air版本生成

#### Air V5.9（个人版）
- 移除: AIDefault, YouTube, Netflix, Apple, USonly
- **保留: AllServer组**（重要！）
- 保留: 自定义服务器
- 简化路由规则

#### Air V7.8（分享版）
- 保留: 所有功能组
- **移除: 所有自定义服务器**
- 保留完整路由规则

## 🎯 使用场景

### 场景1：只更新订阅服务器

如果你只想更新订阅服务器，保持其他配置不变：
- 确保基础配置文件正确
- 运行程序即可

### 场景2：同时使用自定义服务器

如果你有自定义服务器（家庭服务器、办公室服务器等）：
1. 在基础配置中定义自定义服务器
2. 将它们添加到相应的服务器组中
3. 程序会自动保留它们

### 场景3：分享给朋友

生成的Air V7.8版本：
- 自动移除所有自定义服务器
- 保留完整功能
- 可以安全分享

## ⚠️ 注意事项

1. **基础配置备份**
   - 首次使用前备份你的原始配置
   - 程序不会修改基础配置文件

2. **订阅URL安全**
   - 订阅URL包含认证信息
   - 不要将包含URL的配置文件公开

3. **自定义服务器隐私**
   - Air V5.9包含自定义服务器，不要分享
   - Air V7.8已移除自定义服务器，可以分享

4. **定期检查**
   - 建议定期查看日志
   - 确认更新是否正常执行

## 🔧 配置模板

### 最小配置

如果你不需要自定义服务器：

```json
{
  "subscription_url": "YOUR_SUBSCRIPTION_URL",
  "base_config_path": "config/base_configs/Singbox_Pro_V5_9.json",
  "check_interval_hours": 6
}
```

### 完整配置

```json
{
  "subscription_url": "YOUR_SUBSCRIPTION_URL",
  "base_config_path": "config/base_configs/Singbox_Pro_V5_9.json",
  "subscription_history_dir": "subscription_history",
  "output_dir": "outputs",
  "log_dir": "logs",
  "check_interval_hours": 6,
  "log_level": "INFO",
  "enable_notifications": true,
  "notification_webhook": "https://your-webhook-url.com/notify"
}
```

---

**提示**: 
- 首次运行建议使用 `--mode once` 测试
- 确认配置正确后再使用 `--mode schedule` 定时运行
