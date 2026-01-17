# ---

**📘 Calendar Bot v2.3 \- Project Handover & Context Restoration**

Status: Production (Stable)  
Last Updated: v2.3 (Robust & Feature-Rich Edition)  
Role: AI-Native Family Executive Assistant

## **1\. 项目核心哲学 (Core Philosophy)**

**⚠️ To Future AI: 此原则不可动摇**

1. **Prompt-First / AI-Native (提示优先)**：  
   * 我们**不**在 Python 代码中编写复杂的 if-else 业务逻辑（如关键词匹配、城市名转时区）。  
   * 我们将所有“理解”、“分类”、“推断”的任务全权交给 **System Prompt**，利用 LLM 的世界知识。  
   * Python 代码只负责：**Schema 校验、安全兜底、API 调用、状态管理**。  
2. **Robustness over Complexity (稳健至上)**：  
   * 这是为家庭高频使用的生产级工具。宁可拒绝一个模糊的请求，也不要创建一个错误的日程（如年份错误、时区错误）。  
   * 所有关键路径必须有 try-except 和 fallback 机制。  
3. **One-File Architecture (单文件架构)**：  
   * 保持 main.py 单文件结构，便于部署维护，不要过度工程化拆分模块，除非代码量失控。

## ---

**2\. 功能全景 (Capabilities Matrix v2.3)**

### **2.1 核心日程能力**

* **自然语言输入**：支持文本（DeepSeek V3）和图片（Kimi Vision）。  
* **双时区支持 (Dual Timezone)**：  
  * 完美处理跨时区航班（Start @ Tokyo, End @ London）。  
  * UI 直观显示两地时间及转换为“用户本地时间”。  
* **智能语义路由**：  
  * 基于 Prompt 自动判断家庭成员角色（Kimi/Trudy/Kids/Family）。  
  * 自动路由写入不同的 Google Calendar ID。  
* **冲突检测**：  
  * 写入前预检目标日历，发现冲突在回执中警告（非阻断）。

### **2.2 智能修正与防御 (The "Smart Fix" Layer)**

* **年份修正**：防止 LLM 输出“去年的日期”或“2023年”的幻觉，自动推演为当前或未来年份。  
* **跨天/跨年修正**：针对航班到达时间早于起飞时间的逻辑悖论，优先按 \+1 Day 处理。  
* **时区标准化**：LLM 负责将城市名转为 IANA 标准串（如 Asia/Tokyo），Python 负责校验有效性。  
* **Fallback 机制**：若 AI 时区识别失败，自动回退到用户当前时区，并给出透明提示。

### **2.3 交互体验**

* **后悔药 (Undo)**：通过 SQLite event\_history 表记录操作，提供 Inline Button 一键撤回。  
* **指令集**：  
  * /start: 新手引导。  
  * /status: 查看当前时区、Creds 状态、最近操作。  
  * /today: 拉取 Google Calendar 查看今日日程。  
  * /event \[内容\]: 强制事件模式（用于处理模糊文本）。  
  * /travel \[City\]: 切换用户当前时区上下文。

## ---

**3\. 技术架构 (Technical Stack)**

* **Runtime**: Python 3.9+  
* **Deployment**: Zeabur (Serverless / Docker)  
* **Persistence**: SQLite (/app/data/calendar\_bot\_v2.db)  
  * user\_state: 存储 user\_id \-\> current\_timezone  
  * event\_history: 存储 event\_id 用于撤回  
* **API Integrations**:  
  * **Telegram Bot API**: python-telegram-bot (Async)  
  * **LLM**: OpenAI SDK (Compatible) \-\> Moonshot (Vision) & DeepSeek (Logic)  
  * **Google Calendar**: Service Account (Server-to-Server Auth)

### **3.1 环境变量依赖 (Environment Variables)**

Bash

TELEGRAM\_TOKEN=...  
OPENAI\_API\_KEY=...       \# Moonshot  
DEEPSEEK\_API\_KEY=...     \# DeepSeek  
ALLOWED\_USER\_IDS=123,456 \# 白名单  
GOOGLE\_CREDENTIALS\_JSON= \# 完整 JSON 内容  
\# Calendar IDs  
GOOGLE\_CALENDAR\_ID=...          \# Primary (Kimi/Trudy)  
GOOGLE\_CALENDAR\_ID\_JUANJUAN=... \# Child A  
GOOGLE\_CALENDAR\_ID\_DONGDONG=... \# Child B  
GOOGLE\_CALENDAR\_ID\_FAMILY=...   \# Shared

## ---

**4\. 关键逻辑说明 (Logic for Future Devs)**

### **4.1 为什么没有“城市-\>时区”的字典？**

设计决策：我们移除了 Python 中硬编码的 {'Osaka': 'Asia/Tokyo'} 字典。  
原因：世界城市太多。我们依靠 System Prompt 指令 "Map cities to Canonical IANA Timezone" 让 LLM 完成此任务。Python 仅保留极少量的 resolve\_timezone 映射作为对 LLM 常见幻觉的修补。

### **4.2 为什么不支持单次多事件？**

现状：v2.3 遵循 One Message \= One Event。  
原因：为了保证 Schema 解析的绝对稳定性。  
未来扩展：若需支持，需修改 Prompt 输出 Schema 为 JSON Array 并重构 process\_message 进行循环处理（目前 backlog）。

### **4.3 为什么是 Service Account？**

**原因**：这是 Executive Bot，不需要通过 OAuth 登录别人的账号。它作为“秘书”账号，被邀请加入家庭成员的日历并获得 Make Changes 权限。

## ---

**5\. 已知限制与待办 (Roadmap)**

### **已知限制 (Known Limitations)**

1. **单图多事件**：目前的解析器只取第一个识别到的 JSON 对象。  
2. **复杂循环**：虽然支持 RRULE，但过于复杂的自然语言循环（“每月的倒数第二个工作日”）完全依赖 LLM 的转换能力，Python 端仅做透传。

### **未来可能的升级方向 (v2.4+)**

1. **Multi-Event Parsing**：支持一次性解析多个事件（如会议议程表）。  
2. **Agenda 增强**：/today 目前只查主日历，未来可扩展为查询全家日历聚合。  
3. **Voice Mode**：支持 Telegram 语音消息直接转文字并创建日程。

## ---

**6\. 如何恢复开发 (Restoration Guide)**

如果你是接手此项目的 AI，请执行以下步骤：

1. **读取代码**：请求用户提供最新的 main.py。  
2. **理解配置**：确认用户是 **"Standard/Kimi 版"** 还是 **"Trudy 定制版"**（区别在于 Category 集合和 Prompt 中的家庭成员定义，逻辑代码是一致的）。  
3. **遵循原则**：任何修改都不要破坏“Prompt-First”原则。不要把业务逻辑写死在 Python 里。  
4. **安全检查**：确保所有 Google API 调用都包裹在 asyncio.to\_thread 中，保持非阻塞。

## ---

**7\. 版本分支说明 (Version Branches)**
目前维护了两个平行的 main.py 版本，核心逻辑代码 100% 一致，仅配置不同：

### **Standard Edition (Kimi 版)：**
User: Kimi
Kids: Kiki, Jason
Prompt: 针对 Kimi 家庭结构优化。

### **Trudy Edition (Trudy 定制版)：**
User: Trudy
Kids: Juanjuan (卷卷), Dongdong (咚咚)
Prompt: 针对 Trudy 家庭结构优化，角色关键词调整。

---

*\[End of Document\]*