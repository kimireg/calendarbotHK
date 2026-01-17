# GitHub 推送清单

> 确保安全推送到 GitHub，为 Zeabur 部署做好准备

**创建时间**: 2026-01-17
**项目版本**: 3.0.0

---

## 📋 推送前最终检查

### 1. 敏感信息检查
- [ ] ✅ 无 `.env` 文件被提交
- [ ] ✅ 无硬编码的 API Keys
- [ ] ✅ 无硬编码的 Tokens
- [ ] ✅ 无数据库凭证
- [ ] ✅ 无 Google Credentials JSON 文件
- [ ] ✅ `.gitignore` 已正确配置

**验证命令**:
```bash
# 检查是否有敏感文件
git status --ignored

# 确认 .gitignore 生效
git check-ignore -v data/*.db logs/*.log outputs/*
```

### 2. 代码质量检查
- [ ] ✅ 无 `print()` 调试语句（已替换为 `logging`）
- [ ] ✅ 无 `pdb` 断点
- [ ] ✅ 无 TODO/FIXME 未处理
- [ ] ✅ 代码审计报告已生成（`docs/PRE_DEPLOYMENT_AUDIT.md`）

### 3. 文档检查
- [ ] ✅ `README.md` 完整
- [ ] ✅ `CLAUDE.md` 存在
- [ ] ✅ `docs/DEPLOYMENT_GUIDE.md` 详细
- [ ] ✅ `docs/ENV_VARIABLES.md` 完整
- [ ] ✅ `docs/PRE_DEPLOYMENT_AUDIT.md` 已生成

### 4. 依赖文件检查
- [ ] ✅ `services/calendar_bot/requirements.txt` 存在
- [ ] ✅ `services/singbox_updater/requirements.txt` 存在
- [ ] ✅ 所有依赖版本已固定

### 5. Docker 配置检查
- [ ] ✅ `services/calendar_bot/Dockerfile` 正确
- [ ] ✅ `services/singbox_updater/Dockerfile` 正确
- [ ] ✅ 两个 Dockerfile 都使用 `python:3.12-slim`
- [ ] ✅ CMD 命令正确

### 6. 配置文件检查
- [ ] ✅ `services/singbox_updater/config/settings.json` 存在
- [ ] ✅ 配置文件不包含真实密钥（仅占位符）
- [ ] ✅ Base config 文件存在

---

## 🔒 安全扫描

### 快速扫描命令

```bash
# 1. 检查是否有敏感关键词
grep -r "password\|api_key\|token\|secret" services/ --include="*.py" | grep -v "Field\|config\|env"

# 2. 检查环境变量文件
find . -name ".env*" -o -name "*.key" -o -name "*credentials.json"

# 3. 确认 .gitignore 覆盖
git check-ignore -v \
  data/calendar_bot_v2.db \
  logs/app.log \
  outputs/config.json \
  .env \
  credentials.json
```

**预期结果**:
- 第1个命令：应该只返回配置读取相关代码，无硬编码值
- 第2个命令：不应返回任何文件（或仅返回已在 .gitignore 的文件）
- 第3个命令：所有文件都应被 .gitignore 忽略

---

## 📦 Git 操作步骤

### 步骤 1: 初始化 Git（如果还没有）

```bash
# 检查是否已初始化
git status

# 如果未初始化
git init
```

### 步骤 2: 添加远程仓库

**选择你的仓库名**，例如: `kimi-telegram-bot`

```bash
# 方法 1: HTTPS (推荐)
git remote add origin https://github.com/你的用户名/kimi-telegram-bot.git

# 方法 2: SSH
git remote add origin git@github.com:你的用户名/kimi-telegram-bot.git

# 验证远程仓库
git remote -v
```

### 步骤 3: 检查要提交的文件

```bash
# 查看将要提交的文件
git status

# 查看详细的变更
git diff
```

**重要**: 仔细检查列表，确认：
- ❌ 无 `.env` 文件
- ❌ 无 `credentials.json`
- ❌ 无数据库文件（`.db`）
- ❌ 无日志文件
- ✅ 只包含源代码和配置模板

### 步骤 4: 添加文件

```bash
# 添加所有文件
git add .

# 再次检查
git status
```

### 步骤 5: 创建首次提交

```bash
git commit -m "feat: v3.0.0 - Refactored architecture with modular design

- ✨ Complete code refactoring
- ✨ Modular architecture (Calendar Bot + Singbox Updater)
- ✨ SQLAlchemy ORM integration
- ✨ Pydantic settings management
- ✨ Comprehensive documentation
- ✨ Zeabur deployment ready
- 📚 Added deployment guides and env variable docs
"
```

### 步骤 6: 推送到 GitHub

```bash
# 首次推送（设置上游分支）
git push -u origin main

# 如果失败，可能需要先拉取
git pull origin main --rebase
git push -u origin main
```

---

## ⚠️ 常见问题

### 问题 1: GitHub 拒绝推送
**错误**: `! [rejected] main -> main (fetch first)`

**解决**:
```bash
# 方法 1: Rebase (推荐)
git pull origin main --rebase
git push -u origin main

# 方法 2: 强制推送（小心使用！）
git push -u origin main --force
```

### 问题 2: 认证失败
**错误**: `Authentication failed`

**解决**:
1. 检查 GitHub Personal Access Token
2. 确认仓库权限
3. 使用 SSH 密钥（如果配置了）

### 问题 3: 意外提交敏感文件
**如果已提交但未推送**:
```bash
# 从暂存区移除
git reset HEAD .env

# 从提交中移除
git rm --cached .env
git commit --amend
```

**如果已推送到 GitHub**:
```bash
# ⚠️ 警告：这会改变历史
git rm --cached .env
git commit -m "Remove sensitive file"
git push --force

# 然后立即更换泄露的密钥！
```

---

## 🎯 推送后验证

### 1. GitHub 仓库检查
- [ ] 访问 GitHub 仓库页面
- [ ] 确认文件结构正确
- [ ] 检查 README.md 显示正常
- [ ] 确认无敏感文件

### 2. 准备 Zeabur 部署
- [ ] 记录仓库 URL
- [ ] 确认分支名称（通常是 `main`）
- [ ] 准备好所有环境变量的值

---

## 📝 推送后待办

### 立即执行
- [ ] 前往 Zeabur Dashboard
- [ ] 创建 Singbox Updater 服务
- [ ] 创建 Calendar Bot 服务
- [ ] 配置环境变量
- [ ] 启动服务

### 部署验证
- [ ] 检查服务状态
- [ ] 查看日志
- [ ] 测试 Bot 功能
- [ ] 验证定时任务

---

## ✅ 推送清单总结

**在执行 `git push` 之前，确认**:
- [x] 代码审计完成（`docs/PRE_DEPLOYMENT_AUDIT.md`）
- [x] 无敏感信息
- [x] 文档完整
- [x] .gitignore 正确
- [x] Dockerfile 验证
- [x] 依赖文件完整

**准备好了吗？**

✅ **所有检查通过 → 可以安全推送！**

---

## 🚀 快速推送命令（已确认安全）

```bash
# 一键推送（仅在所有检查通过后执行）
git add . && \
git commit -m "feat: v3.0.0 - Refactored architecture" && \
git push -u origin main
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-17
