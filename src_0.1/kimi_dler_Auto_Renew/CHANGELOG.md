# 更新日志

## [1.1.0] - 2026-01-04

### 新增
- ✨ **Telegram Bot集成** - 自动推送更新通知和配置文件到Telegram
  - 自动发送更新通知消息（包含变更摘要）
  - 自动发送三个配置文件（Pro, Air V5.9, Air V7.8）
  - 每个文件都有详细说明
  - 启动时自动测试连接

- 🔧 **环境变量支持** - 支持通过环境变量配置（云部署最佳实践）
  - `SINGBOX_SUBSCRIPTION_URL` - 订阅URL
  - `SINGBOX_TELEGRAM_BOT_TOKEN` - Telegram Bot Token
  - `SINGBOX_TELEGRAM_CHAT_ID` - Telegram Chat ID
  - `SINGBOX_ENABLE_TELEGRAM` - 启用Telegram开关
  - `SINGBOX_CHECK_INTERVAL_HOURS` - 检查间隔
  - `SINGBOX_LOG_LEVEL` - 日志级别
  - 环境变量优先级高于配置文件
  
### 文档
- 📚 新增 `TELEGRAM_GUIDE.md` - Telegram配置完整指南
- 📚 新增 `TELEGRAM_EXAMPLE.md` - 使用示例和效果演示
- 📚 新增 `Telegram功能发布说明.md` - 功能详细介绍
- 📚 新增 `ZEABUR_ENV_GUIDE.md` - Zeabur环境变量配置指南
- 📚 新增 `ENV_QUICK_REF.md` - 环境变量快速参考
- 📚 新增 `.env.example` - 本地开发环境变量模板
- 📝 更新 `README.md` - 添加Telegram和环境变量说明
- 📝 更新 `CONFIG_GUIDE.md` - 添加Telegram配置参数
- 📝 更新 `DEPLOYMENT.md` - 添加环境变量配置步骤

### 技术改进
- 🔧 新增 `src/telegram_notifier.py` 模块（约300行）
- 🔧 更新 `main.py` - 集成Telegram通知和环境变量加载
- 🔧 更新 `config/settings.json` - 移除示例敏感信息
- 🔧 更新 `.gitignore` - 添加.env文件

### 安全改进
- 🔒 支持环境变量，避免敏感信息在代码中
- 🔒 配置来源日志记录
- 🔒 .env文件加入.gitignore

### 其他
- 📦 项目大小：19KB → 30KB（包含新增文档）

---

## [1.0.0] - 2026-01-04

### 初始发布
- ✅ 自动检测订阅更新（基于hash对比）
- ✅ 版本控制（保存所有历史订阅）
- ✅ 自动更新Pro配置（严格按照singbox-updater skill）
- ✅ 自动生成Air V5.9（个人简化版）
- ✅ 自动生成Air V7.8（朋友分享版）
- ✅ 定时任务调度（默认6小时检查一次）
- ✅ 完整的日志记录
- ✅ Docker支持
- ✅ Zeabur部署支持

### 文档
- 📚 `README.md` - 项目主文档
- 📚 `QUICKSTART.md` - 5分钟快速开始
- 📚 `CONFIG_GUIDE.md` - 配置详细说明
- 📚 `DEPLOYMENT.md` - Zeabur部署指南
- 📚 `PROJECT_OVERVIEW.md` - 项目架构概览

### 核心模块
- `src/subscription_checker.py` - 订阅检查器
- `src/updater.py` - Pro配置更新器（基于singbox-updater skill）
- `src/generator.py` - Air版本生成器（基于singbox-air-generator skill）
- `src/scheduler.py` - 定时任务调度器
- `main.py` - 主程序入口

### 配置
- `config/settings.json` - 应用配置
- `config/base_configs/` - 基础配置目录
- `Dockerfile` - Docker配置
- `requirements.txt` - Python依赖

---

## 版本规划

### v1.2.0 (计划中)
- [ ] 支持多个Telegram接收者
- [ ] Telegram交互式命令（/status, /check等）
- [ ] 多订阅源支持
- [ ] Web界面（配置查看、历史浏览）
- [ ] 自动上传到云存储（S3/OSS）

### v1.3.0 (计划中)
- [ ] 完整的Web管理平台
- [ ] API接口
- [ ] 用户账户系统
- [ ] 配置对比工具
- [ ] 统计分析dashboard

### v2.0.0 (远期)
- [ ] 多用户支持
- [ ] 订阅市场
- [ ] 智能服务器选择
- [ ] 性能优化建议
- [ ] 企业级功能

---

## 更新说明

### 版本号规则
- 主版本号：重大架构变更
- 次版本号：新功能添加
- 修订号：Bug修复和小改进

### 更新频率
- 功能更新：按需发布
- Bug修复：及时发布
- 安全更新：立即发布

### 兼容性
- v1.x.x 系列保持向后兼容
- 配置文件格式保持稳定
- 升级前建议备份配置

---

**最新版本**: v1.1.0  
**发布日期**: 2026-01-04  
**下载**: singbox-auto-updater.tar.gz
