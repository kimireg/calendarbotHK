我明白你的意思，而且我觉得这个做法非常对：
把代码、PRD、系统设计三件东西“打包冻结”，以后任何一个新对话，把这三份东西丢进来，就能无损恢复现在的工程语境。

除了你要的 **PRD + 系统设计** 之外，我会在文档里顺带留一小节 *Changelog & TODO*，帮助你以后继续往 v6.3+ 推进。

下面我直接给你两份“可以当文件保存”的内容，你可以分别存成：

* `kimi_butler_v6.2_PRD.md`
* `kimi_butler_v6.2_System_Design.md`

---

## 文件一：`kimi_butler_v6.2_PRD.md`

**《全能管家 Telegram Bot – 产品需求文档（v6.2 冻结版）》**

### 0. 文档元信息

* 产品名称：**全能管家 · Kimi Family Butler**
* 版本：v6.2（Query Fix & Timezone Safe）
* 形态：Telegram Bot（自用家庭工具，不对外公开）
* 代码主文件：`main.py`（单文件结构）
* 最近主要改动：

  * 支持显式命令 `/note` `/event` `/query`
  * Notion 查询走本地 Python 过滤（避免 Notion filter 的各种坑）
  * Google Calendar 时间处理更加保守，不再随意“修正”跨时区航班时间
* 文档目的：冻结当前版本的产品定义，便于未来在任何新对话中恢复项目、继续演进。

---

### 1. 产品背景 & 目标

#### 1.1 背景

* 家庭中有大量零散的信息 & 事务：

  * 生日、重要日期
  * 家庭地址、WiFi、账号密码等静态信息
  * 航班/行程、孩子的课表等动态日程
* 这些信息目前分散在：聊天记录、照片截图、大脑记忆、备忘录中。
* 目标：做一个 **“家庭级知识与日程的 AI 管家”**，让家人只要在 Telegram 里丢一句话 / 一张截图，就能完成：

  * 记一条笔记到 Notion
  * 建一个日程到 Google Calendar
  * 查出之前记过的某条信息
  * 或者单纯聊天

#### 1.2 核心目标

1. **极低心智负担**：
   用户只需要在 Telegram 发消息（自然语言或截图），不需要复杂操作。
2. **信息归一化存储**：

   * 所有静态信息 → 进入 Notion Database（家庭知识库）
   * 所有未来事件 → 写入 Google Calendar（多日历支持）
3. **结构化理解**：

   * 通过 LLM 把自然语言转为结构化 JSON（EVENT / NOTE / QUERY / TEXT）。
4. **强可控 / 可恢复**：

   * Topic 标准化、显式命令、幂等处理，确保行为稳定可预期。

#### 1.3 非目标（当前版本不做）

* 不做复杂 UI（只有 Telegram 文本界面）
* 不做多人并发协作场景的复杂权限体系（仅通过 `ALLOWED_USER_IDS` 白名单控制）
* 不做自然语言“多轮问答记忆”（避免长上下文幻觉）
* 不做自动从邮件/行程 App 抓取信息

---

### 2. 角色 & 使用场景

#### 2.1 主要使用者（Persona）

* **Kimi**（你自己）：Bot 管理者 & 高级用户

  * 负责部署、维护、配置 Notion / GCal。
  * 同时也是重度使用者，记大量家庭信息 / 日程。
* **Janet / Jason / Kiki**：

  * 轻度使用者
  * 场景：发个“记一下某个账号密码”、查生日、查家庭地址等。
* **其他家庭成员（可扩展）**：

  * 通过增加 Telegram ID 到 `ALLOWED_USER_IDS` 即可接入。

#### 2.2 核心使用场景

1. **记录信息（NOTE）**

   * `/note Janet Apple ID 是 xxxx`
   * `/note 新家 Wifi：SSID xxx，密码 yyy`
   * 发一张账单/说明书截图，Bot 自动识别并存为笔记。

2. **创建日程（EVENT）**

   * `/event 明天早上 9 点带 Jason 去看牙`
   * 发一张航班行程图，Bot 自动识别起飞/到达时间、地点，写入 Google Calendar。

3. **查找信息（QUERY）**

   * `/query Janet Birthday`
   * `/query Home Address`
   * `/query Dahua Wifi`

4. **系统健康检查（STATUS）**

   * `/status` 查看当前配置是否完整（Notion / GCal / Telegram 环境变量）。

5. **普通聊天（TEXT）**

   * 发一些闲聊内容，Bot 以 LLM 的聊天回复你，不触发任何外部写入。

---

### 3. 功能范围（Scope）

当前 v6.2 版本包含：

1. **输入通道**

   * Telegram 文本消息
   * Telegram 图片消息（单张照片）

2. **意图识别模式**

   * 自动模式：普通文本 / 图片 → 交给 LLM 决定是 EVENT / NOTE / QUERY / TEXT。
   * 显式模式：

     * `/note ...` → 强制 NOTE 模式
     * `/event ...` → 强制 EVENT 模式
     * `/query ...` → 强制 QUERY 模式（直接查 Notion，不经过 LLM）

3. **支持的类型**

   * `EVENT`：未来日程
   * `NOTE`：静态知识
   * `QUERY`：查询已有知识
   * `TEXT`：普通对话

4. **外部系统**

   * **Notion**：一个 Database，字段包括（约定）：

     * `Content`（title）
     * `Category`（rich_text 或 select）
     * `Topic`（rich_text，标准化大写）
     * `Date`（date）
   * **Google Calendar**：

     * 通过 Service Account 写入
     * 支持按 Category 分配到不同日历（Kiki / Jason / Janet / Family / Kimi）

---

### 4. 详细功能需求

#### 4.1 权限控制

* 使用环境变量 `ALLOWED_USER_IDS` 控制：

  * 配置为逗号分隔的 Telegram 用户 ID 列表，例如：`123456789,987654321`
  * 不在列表中的用户：

    * 任何消息回复：`⛔️ 未授权 ID: {user_id}`
    * 不做任何进一步处理
* 所有 Handler（文本 / 图片 / status）在第一行调用 `check_auth`，未通过则中断。

#### 4.2 幂等处理

* 由于 Telegram 可能重复投递消息，v6.2 在 `check_auth` 中做幂等防护：

  * 使用 `(chat_id, message_id)` 作为 Key。
  * 维护 `processed_ids`（`deque(maxlen=200)`）。
  * 如果检测到重复 Key，则直接忽略并打印日志 `🔁 忽略重复消息`。

---

#### 4.3 NOTE 功能

**输入方式：**

1. 自动模式：

   * 用户直接发送一条消息，例如：

     > Janet 的 Apple ID 密码是 xxxx
   * LLM 根据 System Prompt 判断为 NOTE。

2. 显式模式：

   * 用户发送 `/note ...`：

     * 例如 `/note Kiki 的生日是 2007-10-10`
     * 框架会去掉 `/note` 前缀，只把剩下文本交给 LLM；同时设置 `forced_type="NOTE"`，保证 LLM 输出 NOTE JSON。

**LLM 期望输出 JSON：**

```json
{
  "type": "NOTE",
  "category": "Kiki",
  "topic": "KIKI BIRTHDAY",
  "content": "Kiki's birthday is 2007-10-10."
}
```

**业务规则：**

* `topic`：

  * 必须为英文，格式建议为 `"ENTITY ATTRIBUTE"`，如：

    * `"JANET BIRTHDAY"`
    * `"HOME ADDRESS"`
    * `"DAHUA WIFI"`
  * 代码会调用 `normalize_topic` 转为大写、去前后空格，用于：

    * 写入 Notion 的 Topic 字段
    * 查重

* 写入 Notion 逻辑：

  1. 若 `NOTION_DATABASE_ID` 未配置 → 返回失败提示，不写入。
  2. 若 `topic` 为空 → 拒绝写入，提示用户让其重新描述。
  3. 查重逻辑：

     * 在 Notion 中按 `Topic` 属性 `rich_text.equals` 标准化后的大写 Topic 查找。
     * 若找到 N 条旧记录：

       * 将这些旧记录 `archived=True`（逻辑删除）。
  4. 写入新记录：

     * `Content` = `【{TOPIC}】 {content}`
     * `Category` = `note_data.category`（默认 `Family`）
     * `Topic` = 标准化后的大写 Topic
     * `Date` = 当前时间
  5. 成功时：返回 `"Success"` 或 `"已更新 (覆盖 N 条旧记录)"`。

**用户可见反馈：**

* 成功示例：

```text
📝 笔记已存入 Notion

🗂 分类: #Kiki
📌 主题: KIKI BIRTHDAY
📄 内容:
Kiki's birthday is 2007-10-10.

ℹ️ 状态: Success

🧠 LLM: DeepSeek V3
```

* 失败场景：

  * Notion 未配置 / Topic 缺失 / API 异常：

    * 返回 `❌ Notion 写入失败: {错误信息}`（不再使用 Markdown 格式）。

---

#### 4.4 EVENT 功能

**输入方式：**

1. 自动模式：

   * 纯文本：

     > 明天晚上七点和 Janet 去吃饭
   * 图片：

     * 例如带有航班信息的机票截图 / 行程单。
     * 使用 Kimi Vision 模型。

2. 显式模式：

   * `/event 下周三下午三点带 Jason 看牙`
   * 前缀 `/event` 会被去掉，剩余文本交给 LLM；同时设置 `forced_type="EVENT"`。

**LLM 期望输出 JSON：**

```json
{
  "type": "EVENT",
  "category": "Kiki",
  "summary": "Kiki Piano Lesson",
  "start_time": "2025-02-18 15:30:00",
  "start_timezone": "Asia/Singapore",
  "end_time": "2025-02-18 16:30:00",
  "end_timezone": "Asia/Singapore",
  "location": "XXX Music School"
}
```

**业务规则：**

* `category` 决定使用哪个日历：

  * `Kiki` / `Jason` / `Janet` / `Family` / `Kimi`
  * 通过环境变量：

    * `GOOGLE_CALENDAR_ID`（默认）
    * `GOOGLE_CALENDAR_ID_KIKI`
    * `GOOGLE_CALENDAR_ID_JASON`
    * 等等

* 时间与时区：

  * `start_time` / `end_time` 格式：`YYYY-MM-DD HH:MM:SS`。
  * `start_timezone` 默认 `Asia/Singapore`，若 LLM 提供则按其值。
  * 若缺失 `end_time`：

    * 代码补一个：`start_time + 1 小时`。
  * 若 `end_time <= start_time`：

    * v6.2 不再“自动修正”，只打印 warning，保留原值。
    * 用于兼容跨时区机票这种复杂场景。

* 写入 Google Calendar：

  * 使用 Service Account JSON（`GOOGLE_CREDENTIALS_JSON`）。
  * 创建 Event 时写入：

    * `summary`
    * `description`（如有）
    * `start.datetime` + `start.timeZone`
    * `end.datetime` + `end.timeZone`
    * `location`（如有）

**用户可见反馈：**

* 成功示例：

```text
✅ 日程已同步

👧 Kiki - Kiki Piano Lesson
📅 日期: 2025-02-18 (周二)
🕒 时间: 15:30 - 16:30 (Asia/Singapore)
📍 地点: XXX Music School
🔗 查看日历(链接)

🧠 LLM: DeepSeek V3
```

* 失败 & 降级逻辑：

  * 若写入 GCal 失败：

    * 尝试生成 `.ics` 文件发给用户。
    * 文案中会包含错误信息：

      ```text
      ⚠️ 同步失败，请手动添加

      👧 Kiki - Kiki Piano Lesson
      📅 2025-02-18 15:30 - 16:30
      ❌ 错误: {Google API 错误信息}
      ```

---

#### 4.5 QUERY 功能

**显式模式（推荐）：**

* 用户输入：`/query Janet Birthday`
* v6.2 行为：

  * 直接绕过 LLM，将 `"Janet Birthday"` 作为关键字交给 `query_notion`。
  * `model_name` 标记为 `"DirectQuery"`。

**自动模式（不常用）：**

* 如果 LLM 在自动模式下返回 `{"type": "QUERY", "keywords": "..."}`，也会调用同一个 `query_notion`。

**查询策略（当前实现）：**

> v6.2 第一版：在 Python 中对 Notion 返回的 `Content` + `Topic` 进行大小写不敏感匹配（**已知存在 Birthday 查不到的问题**）。

（你后面已经有了一个更鲁棒的方案，遍历所有 title / rich_text 字段，这个属于 v6.3 的改进，不写死在 v6.2 PRD 里，只在「后续迭代建议」中记录。）

**返回格式：**

```text
🔍 找到相关笔记 (3条):

1. [Kiki] [KIKI BIRTHDAY] Kiki's birthday is 2007-10-10.
2. [Janet] [JANET BIRTHDAY] Janet's birthday is 1976-03-24.
3. [Family] [HOME ADDRESS] ...

🧠 LLM: DirectQuery
```

查不到时：

```text
🤷‍♂️ 未找到关于 'Janet Birthday' 的记录。

🧠 LLM: DirectQuery
```

---

#### 4.6 STATUS 功能

* 命令：`/status`
* 功能：检查系统配置是否完整，并给出人类可读的提示。
* 检查项：

  * Telegram Token 是否配置
  * Notion：

    * 是否存在 `NOTION_DATABASE_ID`
    * 是否存在 `NOTION_TOKEN`
    * 分情况给出：

      * Missing ID & Token
      * Missing DB ID
      * Missing Token
      * Configured
  * Google Calendar：

    * 是否存在 `GOOGLE_CREDENTIALS_JSON`

**返回示例：**

```text
🩺 系统状态检查

✅ Telegram (ID: 123456789)
✅ Notion: Configured
❌ Google Calendar: Missing Credentials

当前 Category: Kiki, Jason, Janet, Family, Kimi
默认时区: Asia/Singapore
代码版本: v6.2 (Query Fix & Timezone Safe)
```

---

### 5. 交互与体验要求

1. **所有系统消息风格**：

   * 尽量短小、结构化、带 Emoji。
   * 保留中英文混排，便于家庭成员理解。

2. **错误信息**：

   * 对用户：只展示必要的错误说明 + 是否需要管理员介入。
   * 对日志：打印完整的异常栈，便于排查。

3. **语言**：

   * 用户输入可以中英文混合。
   * 系统回复主要中文，关键字段（Topic、Category 等）保留英文。

---

### 6. 性能 & 可靠性

* 预计并发量极低（自用家庭 bot）。
* 单机单进程足够，无需复杂扩缩容。
* 超时：

  * Kimi Vision：120 秒
  * DeepSeek：60 秒
* 避免长对话上下文：

  * 每次调用 LLM 只带 System Prompt + 当前一轮用户消息，不做多轮对话记忆，从产品层面减轻幻觉。

---

### 7. 安全 & 隐私

* 所有敏感信息（账号密码、家庭地址、生日等）都存储在：

  * 私有 Notion 工作区
  * 私有 Google Calendar
* 代码层面：

  * 所有外部密钥通过环境变量注入，不写入仓库。
* Bot 本身通过 `ALLOWED_USER_IDS` 白名单控制访问。
* 不做开放式群组使用。

---

### 8. 已知问题 & 后续迭代建议

1. **/query 搜索范围有限**

   * 当前版本对 Notion 结构有假设（Content/Topic），在部分 schema 下可能出现 “明明有 Birthday 却查不到”的情况。
   * 建议在 v6.3 中采用“遍历所有 title/rich_text 字段”的鲁棒查询方案。

2. **跨时区复杂机票**

   * v6.2 不再强行调整 end_time，但完全依赖 LLM 输出的 start/end + timezone 组合。
   * 实际航班场景仍可能出现：

     * 起飞/落地时间正确，但 timezone 错误；
     * 或者反之。
   * 后续可以增加：

     * 明确“出发地/目的地”到时区的映射校验；
     * 或提供可视化确认步骤。

3. **撤销（Undo）功能**

   * 产品层面已经有需求苗头：希望 `/undo` 能撤销最近一次 Notion/Calendar 操作。
   * v6.2 尚未实现，仅在 System Design 里预留思路。

---

## 文件二：`kimi_butler_v6.2_System_Design.md`

**《全能管家 Telegram Bot – 系统设计说明（v6.2 冻结版）》**

### 0. 文档元信息

* 目标版本：v6.2（与当前部署 main.py 一致）
* 范围：单文件 `main.py` 的架构、模块职责、数据流、依赖配置。
* 受众：

  * 未来的“你”（重启这个项目时）
  * 其他 AI（例如 Gemini / 未来的 ChatGPT），用于快速建立技术上下文。

---

### 1. 整体架构概览

#### 1.1 高层组件

* **Telegram Bot Server（Zeabur 上的 Python 容器）**

  * 使用 `python-telegram-bot` 的 `Application.run_polling()` 模式。
  * 负责接收用户消息、调用 LLM、调用 Notion / Google Calendar。

* **LLM 提供方**

  * **Kimi Vision**（Moonshot API）

    * 模型：`moonshot-v1-8k-vision-preview`
    * 用于图片 + 文本混合理解。
  * **DeepSeek Chat**

    * 模型：`deepseek-chat`
    * 用于纯文本理解 & 聊天。

* **存储层**

  * **Notion Database**

    * 存储家庭知识（NOTE）。
  * **Google Calendar**

    * 存储家庭时间轴（EVENT）。

#### 1.2 调用关系（文字版时序图）

以 `/note ...` 为例：

1. 用户在 Telegram 输入 `/note Janet 的生日是 1976-03-24`。
2. Telegram → Bot（Webhook/long polling）。
3. Bot：

   * `handle_text`：

     * `check_auth` 验证用户，幂等。
     * 解析命令，设置 `forced_type="NOTE"`，去掉前缀得到 `content_to_llm`。
   * 构造 `system_prompt`（带当前时间 / 规则），附加“必须输出 NOTE JSON”的说明。
   * 调用 DeepSeek Chat。
4. DeepSeek 返回 JSON 文本。
5. `process_llm_result`：

   * `parse_json_from_llm` → 得到 `msg_type="NOTE"` + `note_data`。
   * `forced_type` 再次覆盖，确保类型仍为 NOTE。
   * 调用 `reply_handler(..., msg_type="NOTE", result_data=note_data)`。
6. `reply_handler`：

   * 调用 `add_to_notion(note_data)`。
   * 根据成功 / 失败构造文本消息，回复给 Telegram 用户。

其他类型（EVENT / QUERY / TEXT）类似。

---

### 2. 技术栈 & 依赖

* Python 3.x
* 主要库：

  * `python-telegram-bot` v20+
  * `openai`（用于 Moonshot / DeepSeek）
  * `notion_client`
  * `google-api-python-client` + `google-auth`
  * `icalendar`
  * `pytz`
* 部署环境：Zeabur 容器（长时间运行的进程即可，不需要额外服务）。

---

### 3. 模块划分（按 main.py 中的逻辑章节）

1. **配置与常量（Configuration）**

   * 日志配置
   * LLM 客户端初始化
   * Notion 客户端初始化
   * 常量定义（模型名 / 默认时区 / Category Map / 中文星期）
   * 环境变量解析（`ALLOWED_USER_IDS`）

2. **核心工具函数**

   * `check_auth`
   * `safe_reply`
   * `keep_typing`
   * `normalize_topic`
   * `parse_json_from_llm`

3. **Google Calendar 模块**

   * `_google_api_sync_call`
   * `add_to_google_calendar`
   * `create_ics_file`

4. **Notion 模块**

   * `add_to_notion`
   * `query_notion`（当前版本：Content+Topic 简化版；你有一个更鲁棒的升级方案）

5. **系统 Prompt**

   * `get_system_prompt`：封装对 LLM 的 System 指令。

6. **统一回复处理**

   * `reply_handler`
   * `process_llm_result`

7. **主逻辑 & 命令处理**

   * `handle_status`
   * `handle_photo`
   * `handle_text`
   * 程序入口：`if __name__ == '__main__': ... run_polling()`

---

### 4. 关键模块设计细节

#### 4.1 check_auth & 幂等

```python
async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id

    if user_id not in ALLOWED_IDS: ...
    key = (chat_id, msg_id)
    if key in processed_ids: ...
    processed_ids.append(key)
```

* `processed_ids` 使用 `deque(maxlen=200)`：

  * 内存有上限，不会无限膨胀。
  * 对家庭场景足够。

#### 4.2 LLM 解析 & JSON 抽取

* 所有来自 LLM 的回复都先经过 `parse_json_from_llm`：

  * 如果 Content 是 list（多模态），抽取其中 `{"type": "text"}` 的部分。
  * 使用正则 `re.search(r'\{[\s\S]*\}', content)` 尝试找到 JSON 块。
  * `json.loads` 后，如果是 dict：

    * 读取 `type` 字段（转大写）。
    * 返回 `(msg_type, data)`。
  * 出错则回退为 TEXT。

* `process_llm_result` 是统一入口：

  * 在此处理 `forced_type`（显式命令）。
  * 在 NOTE / EVENT / QUERY 三类时调用 `reply_handler`。

#### 4.3 Prompt 设计

* System Prompt 包含：

  * 当前时间 + 时区；
  * 类型定义（EVENT / NOTE / QUERY / TEXT）；
  * NOTE 规则：

    * Topic = 英文 + 大写；
    * 内容中的日期标准化为 `YYYY-MM-DD`。
  * EVENT 规则：

    * 要给出 `start_timezone` / `end_timezone`；
    * 给出 `location`。
  * JSON Schema 示例。

* 显式命令时，在 System Prompt 后追加：

  ```text
  【IMPORTANT】User explicitly requested type: {forced_type}. 
  You MUST output JSON with type='{forced_type}'.
  ```

  确保 LLM 不“自作主张”改类型。

#### 4.4 Notion 写入 & 去重

* Topic 标准化：

  * `normalize_topic(raw)` → 去空格 + 大写。
* 去重：

  * 调用 `notion.databases.query`，按 `Topic.rich_text.equals(topic)` 查找。
  * 对所有旧记录 `pages.update(..., archived=True)`.
* 新记录属性：

  * `Content.title` → `【TOPIC】 {content}`
  * `Category.rich_text` → 短文本，如 `Kiki`、`PERSONAL`
  * `Topic.rich_text` → 标准化 Topic
  * `Date.date.start` → `datetime.now().isoformat()`

#### 4.5 Notion 查询（query_notion）

* 当前 v6.2 版本逻辑（简略）：

  * 拆分关键词为多个 term。
  * 单个 term：OR 查询：

    * `Content.title.contains(term)` OR `Topic.rich_text.equals(term.upper())`
  * 多个 term：AND 查询：

    * 所有 term 都在 `Content.title` 中 `contains`。
  * 返回前，将结果组装为 `"[{category}] {content_text}"` 形式。

* 已知问题：

  * 当关键词只出现在 Topic 或 Content 中的一部分时，在某些 schema 下可能无法命中（特别是 Birthday 案例）。
  * 你已经有了一个“扫描所有文本字段”的改进版，这个属于后续版本。

#### 4.6 Google Calendar 写入

* `_google_api_sync_call` 内部：

  * 从环境变量读 Service Account JSON。
  * 根据 `category` 选择日历 ID：

    * `GOOGLE_CALENDAR_ID_KIKI` 等。
  * 时间处理：

    * 解析 `start_time`，格式错误会抛异常。
    * `end_time`：

      * 缺失 → `start + 1h`。
      * 存在且解析成功但 `<= start` → 打 warning，但不改变（保留原值）。
      * 解析失败 → fallback 到 `start + 1h`。
  * 调用 Google API 创建事件：

    * 失败时，返回错误字符串 → 上层用于生成提示。

* `create_ics_file`：

  * 用 `icalendar` 库生成 `.ics`，时间带时区。

---

### 5. 环境变量 & 配置

在 Zeabur / 本地运行时，需要配置以下环境变量：

1. Telegram

   * `TELEGRAM_TOKEN`

2. LLM

   * `OPENAI_API_KEY`（Kimi / Moonshot）
   * `DEEPSEEK_API_KEY`

3. Notion

   * `NOTION_DATABASE_ID`
   * `NOTION_TOKEN`

4. Google Calendar

   * `GOOGLE_CREDENTIALS_JSON`（Service Account JSON 文本）
   * `GOOGLE_CALENDAR_ID`（默认日历）
   * `GOOGLE_CALENDAR_ID_KIKI`
   * `GOOGLE_CALENDAR_ID_JASON`
   * `GOOGLE_CALENDAR_ID_JANET`
   * `GOOGLE_CALENDAR_ID_FAMILY`
   * `GOOGLE_CALENDAR_ID_KIMI`
   * （后四/五个按需要配置）

5. 权限

   * `ALLOWED_USER_IDS`：逗号分隔的 Telegram user id 列表。

---

### 6. 部署 & 运维要点（简版）

1. **依赖安装**：使用当前 `requirements.txt`。
2. **Zeabur 容器命令**：

   * 形如：`python main.py`
3. **日志查看**：

   * 依赖 `logging` 输出到 stdout，由 Zeabur 收集。
4. **故障排查建议**：

   * 查询失败 → 看 Notion 查询日志（filter 结构、结果条数）。
   * EVENT 创建失败 → 关注 Google API 返回的错误字符串。
   * LLM 异常 → 查看 `JSON 解析失败` / `Error: ...` 的日志。

---

### 7. 演进与扩展建议（给未来的 v6.3+）

> 这部分不是当前代码行为，而是“系统设计层”的建议，方便以后继续做。

1. **更鲁棒的 `query_notion`**

   * 改为遍历所有 `title` + `rich_text` 属性，拼成一个 `haystack` 做本地匹配。
   * 不再依赖固定的 `Content` / `Topic` 列名。

2. **Undo 能力**

   * 在 `reply_handler` 中记录最近一次写入的：

     * Notion page_id
     * Calendar event_id
   * `/undo` 命令：

     * 默认撤销当前用户最近一次成功的 NOTE 或 EVENT。

3. **Config 自检 & 可视化**

   * `/status` 增强为：

     * 显示当前 Notion DB 的列名 / 类型快照；
     * 显示当前可用的 Google Calendar 列表。

4. **复杂航班场景优化**

   * 在 EVENT JSON 中约定字段：

     * `origin_airport`, `destination_airport`
   * 通过机场代码推断时区辅助校验。

---

## 最后小结：还有没有更好的“冻结方案”？

你现在这套做法已经挺专业了：

1. 冻结代码：`main.py`
2. 冻结产品定义：PRD
3. 冻结技术语境：System Design

如果再想更保险一点，可以考虑再加两样东西（可选）：

* **A. `CHANGELOG.md`**：简单列一下从 v1.x 到 v6.2 的关键变化点，方便以后回忆“为什么当时这么设计”。
* **B. 一个最小的 `.env.sample`**：列出所有需要的环境变量名，方便未来在新环境下快速恢复部署。

但就恢复项目的可行性来说，现在这三件（`main.py + PRD + System Design`）已经完全够用。你以后在任何新对话里，只要把这三份东西贴上来，谁接这个项目（包括未来版本的我 / Gemini），都能几乎无损地继续往 v6.3+ 开发下去。
