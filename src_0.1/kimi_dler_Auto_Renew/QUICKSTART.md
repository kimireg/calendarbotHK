# 🚀 快速开始指南

## 5分钟部署到Zeabur

### 步骤1: 下载项目（30秒）

下载 `singbox-auto-updater.tar.gz` 并解压：

```bash
tar -xzf singbox-auto-updater.tar.gz
cd singbox-auto-updater
```

### 步骤2: 配置文件（2分钟）

#### 2.1 准备Pro基础配置

将你的Singbox Pro配置复制到：
```
config/base_configs/Singbox_Pro_V5_9.json
```

#### 2.2 配置订阅URL

编辑 `config/settings.json`，替换你的订阅URL：

```json
{
  "subscription_url": "https://your-subscription-url",
  "check_interval_hours": 6
}
```

### 步骤3: 本地测试（1分钟）

```bash
# 安装依赖
pip install -r requirements.txt

# 测试运行一次
python main.py --mode once
```

如果成功，会看到：
```
✅ 步骤1完成：Pro配置已更新
✅ 步骤2完成：Air版本已生成
```

检查 `outputs/` 目录应该有三个配置文件。

### 步骤4: 上传到GitHub（1分钟）

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 步骤5: 部署到Zeabur（1分钟）

1. 访问 [zeabur.com](https://zeabur.com)
2. 创建新项目
3. 添加服务 → 从GitHub导入
4. 选择你的仓库
5. 点击部署

**完成！** 🎉

---

## 验证部署

### 查看日志

在Zeabur控制台查看服务日志，应该看到：

```
🚀 Starting update check
📥 Downloading subscription from: https://...
✅ Downloaded: 36 servers
...
✅ Update completed successfully!
```

### 获取配置文件

#### 方式1: 通过Zeabur控制台

服务详情 → 文件浏览器 → `outputs/` → 下载文件

#### 方式2: 配置自动上传

修改 `main.py` 中的 `_send_notification` 方法，添加上传到云存储的逻辑。

---

## 常见问题

### Q: 订阅下载失败怎么办？

A: 检查订阅URL是否正确，以及网络是否可以访问。

### Q: 如何更改检查频率？

A: 修改 `config/settings.json` 中的 `check_interval_hours`。

### Q: 自定义服务器会丢失吗？

A: 不会。只要在基础配置中定义了，程序会自动保留。

### Q: 如何停止服务？

A: 在Zeabur控制台暂停或删除服务即可。

---

## 下一步

- [完整文档](README.md)
- [配置指南](CONFIG_GUIDE.md)
- [部署指南](DEPLOYMENT.md)

**需要帮助？** 查看项目GitHub Issues或README文档。
