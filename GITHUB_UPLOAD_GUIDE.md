# GitHub 手动上传指南

**目标**: 将重构后的代码上传到 GitHub
**方式**: 手动上传文件（不使用 Git 命令）
**版本**: v3.0.0

---

## 📂 需要上传的文件和文件夹

### 方式一：完整上传（推荐）

**直接上传整个项目根目录，包含以下内容**:

```
整个项目文件夹/
├── services/                    ✅ 必需 - 两个服务的完整代码
│   ├── calendar_bot/
│   └── singbox_updater/
│
├── docs/                        ✅ 必需 - 所有文档
│   ├── CODE_AUDIT_REPORT.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── REFACTORING_SUMMARY.md
│
├── src_0.1/                     ⚠️  可选 - 旧版本备份（建议保留）
│
├── README.md                    ✅ 必需
├── CLAUDE.md                    ✅ 必需
├── .gitignore                   ✅ 必需
└── PROJECT_CHECKLIST.md         ✅ 必需
```

### 方式二：选择性上传（最小化）

如果你想减小仓库大小，可以只上传以下内容：

**必需文件夹**:
```
✅ services/                     # 完整服务代码
✅ docs/                         # 完整文档
```

**必需根目录文件**:
```
✅ README.md
✅ CLAUDE.md
✅ .gitignore
```

**可选但推荐**:
```
⚠️  src_0.1/                     # 旧版本备份（如果需要回滚）
⚠️  PROJECT_CHECKLIST.md        # 项目清单
```

---

## 🚫 不需要上传的文件/文件夹

以下文件和文件夹**不要上传**到 GitHub：

```
❌ __pycache__/                 # Python 缓存
❌ *.pyc                         # Python 编译文件
❌ .DS_Store                     # macOS 系统文件
❌ data/                         # 数据库文件（运行时生成）
❌ logs/                         # 日志文件（运行时生成）
❌ outputs/                      # 输出文件（运行时生成）
❌ subscription_history/         # 订阅历史（运行时生成）
❌ *.db                          # 数据库文件
❌ *.log                         # 日志文件
❌ .env                          # 环境变量文件（敏感信息）
❌ venv/                         # 虚拟环境
❌ env/                          # 虚拟环境
```

**好消息**: `.gitignore` 文件已经配置好了这些规则！

---

## 📋 手动上传步骤

### 步骤 1: 准备文件

1. 在你的电脑上，打开项目根目录：
   ```
   /Users/kimi/Library/Mobile Documents/com~apple~CloudDocs/Projects/for Claude Code/KImi's Telegram Bot
   ```

2. 确认以下文件夹存在：
   - ✅ `services/calendar_bot/`
   - ✅ `services/singbox_updater/`
   - ✅ `docs/`

3. 确认以下文件存在：
   - ✅ `README.md`
   - ✅ `CLAUDE.md`
   - ✅ `.gitignore`

### 步骤 2: 创建/打开 GitHub 仓库

**如果仓库已存在**:
1. 进入你的 GitHub 仓库页面
2. 准备清空旧文件（或创建新分支）

**如果需要创建新仓库**:
1. 登录 GitHub
2. 点击右上角 "+" → "New repository"
3. 填写仓库名称（如: `kimi-telegram-bot`）
4. 选择 Private（推荐）或 Public
5. **不要**勾选 "Initialize with README"（我们已有 README）
6. 点击 "Create repository"

### 步骤 3: 上传文件

#### 方法 A: 使用 GitHub 网页界面（简单）

1. 进入你的 GitHub 仓库页面

2. **如果是空仓库**:
   - 页面会显示 "Quick setup"
   - 点击 "uploading an existing file"

3. **如果仓库已有文件**:
   - 点击 "Add file" → "Upload files"

4. **上传文件**:
   - 将整个 `services` 文件夹拖拽到页面
   - 将整个 `docs` 文件夹拖拽到页面
   - 将 `README.md`, `CLAUDE.md`, `.gitignore` 拖拽到页面
   - （可选）将 `src_0.1` 文件夹拖拽到页面

5. **提交**:
   - 在页面底部的 "Commit changes" 区域
   - 填写提交消息: `Refactor to v3.0.0 - Modular architecture`
   - 点击 "Commit changes"

6. **等待上传完成**

#### 方法 B: 使用 GitHub Desktop（如果你有安装）

1. 打开 GitHub Desktop
2. File → Add Local Repository
3. 选择项目文件夹
4. Commit to main: `Refactor to v3.0.0`
5. Push origin

---

## ✅ 上传后验证

### 在 GitHub 仓库中检查：

**必需文件夹**:
- ✅ `services/calendar_bot/src/` - 应该包含多个子文件夹
- ✅ `services/calendar_bot/main.py`
- ✅ `services/calendar_bot/Dockerfile`
- ✅ `services/calendar_bot/requirements.txt`
- ✅ `services/singbox_updater/src/` - 应该包含多个 .py 文件
- ✅ `services/singbox_updater/main.py`
- ✅ `services/singbox_updater/Dockerfile`
- ✅ `services/singbox_updater/requirements.txt`
- ✅ `services/singbox_updater/config/base_configs/Singbox_Pro_V5_9.json`

**必需文档**:
- ✅ `docs/DEPLOYMENT_GUIDE.md`
- ✅ `docs/CODE_AUDIT_REPORT.md`
- ✅ `docs/REFACTORING_SUMMARY.md`

**根目录文件**:
- ✅ `README.md`
- ✅ `CLAUDE.md`
- ✅ `.gitignore`

### 检查文件结构

在 GitHub 仓库页面，你应该看到类似的结构：

```
你的仓库/
├── services/
│   ├── calendar_bot/
│   │   ├── src/
│   │   │   ├── config/
│   │   │   ├── core/
│   │   │   ├── database/
│   │   │   ├── handlers/
│   │   │   └── integrations/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── singbox_updater/
│       ├── config/
│       │   ├── base_configs/
│       │   │   └── Singbox_Pro_V5_9.json
│       │   └── settings.json
│       ├── src/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
├── docs/
│   ├── CODE_AUDIT_REPORT.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── REFACTORING_SUMMARY.md
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## 🎯 上传完成后的下一步

### 1. 确认上传成功

- [ ] 在 GitHub 仓库页面能看到所有文件
- [ ] 点击 `services/calendar_bot/src/` 能看到子文件夹
- [ ] 点击 `README.md` 能正常显示内容
- [ ] 点击 `services/singbox_updater/config/base_configs/` 能看到 JSON 文件

### 2. 准备 Zeabur 部署

现在你可以：
1. 登录 Zeabur Dashboard
2. 选择这个 GitHub 仓库
3. 开始部署 Singbox Updater（Root Directory: `services/singbox_updater`）
4. 然后部署 Calendar Bot（Root Directory: `services/calendar_bot`）

### 3. 参考部署指南

详细步骤请参考: `docs/DEPLOYMENT_GUIDE.md`

---

## 🚨 常见问题

### Q: 上传时文件夹是灰色的，无法选择？
**A**: 这是正常的。拖拽整个文件夹到浏览器窗口即可，不需要点击选择。

### Q: .gitignore 文件看不到？
**A**: 因为以 `.` 开头的文件在 macOS Finder 中默认隐藏。可以：
   - 按 `Cmd + Shift + .` 显示隐藏文件
   - 或在终端用 `ls -la` 查看

### Q: 上传很慢或失败？
**A**:
   - 确保网络连接稳定
   - 如果文件太大，可以先上传 `services` 文件夹，再分批上传其他
   - 或使用 GitHub Desktop

### Q: 是否需要上传 src_0.1 文件夹？
**A**:
   - **推荐保留**，作为备份，万一需要回滚
   - 如果想减小仓库大小，可以不上传
   - 你本地永远保留这个备份即可

---

## ✅ 上传检查清单

在告诉我"上传完成"之前，请确认：

- [ ] GitHub 仓库中能看到 `services/calendar_bot/` 文件夹
- [ ] GitHub 仓库中能看到 `services/singbox_updater/` 文件夹
- [ ] GitHub 仓库中能看到 `docs/` 文件夹
- [ ] 点击 `services/calendar_bot/src/config/settings.py` 能看到代码
- [ ] 点击 `services/singbox_updater/config/base_configs/Singbox_Pro_V5_9.json` 能看到 JSON
- [ ] `README.md` 正常显示
- [ ] `.gitignore` 文件存在

**全部确认后，你就可以告诉我准备开始部署了！** 🚀

---

**文档版本**: 1.0.0
**创建时间**: 2026-01-17
