《全能管家 Telegram Bot – 产品需求文档（v6.2 冻结版）》

0. 文档元信息

产品名称：全能管家 · Kimi Family Butler

版本：v6.2（Query Fix & Timezone Safe）

形态：Telegram Bot（自用家庭工具，不对外公开）

代码主文件：main.py（单文件结构）

最近主要改动：

支持显式命令 /note /event /query

Notion 查询走本地 Python 过滤（避免 Notion filter 的各种坑）

Google Calendar 时间处理更加保守，不再随意“修正”跨时区航班时间

文档目的：冻结当前版本的产品定义，便于未来在任何新对话中恢复项目、继续演进。

1. 产品背景 & 目标
1.1 背景

家庭中有大量零散的信息 & 事务：

生日、重要日期

家庭地址、WiFi、账号密码等静态信息

航班/行程、孩子的课表等动态日程

这些信息目前分散在：聊天记录、照片截图、大脑记忆、备忘录中。

目标：做一个 “家庭级知识与日程的 AI 管家”，让家人只要在 Telegram 里丢一句话 / 一张截图，就能完成：

记一条笔记到 Notion

建一个日程到 Google Calendar

查出之前记过的某条信息

或者单纯聊天

1.2 核心目标

极低心智负担：
用户只需要在 Telegram 发消息（自然语言或截图），不需要复杂操作。

信息归一化存储：

所有静态信息 → 进入 Notion Database（家庭知识库）

所有未来事件 → 写入 Google Calendar（多日历支持）

结构化理解：

通过 LLM 把自然语言转为结构化 JSON（EVENT / NOTE / QUERY / TEXT）。

强可控 / 可恢复：

Topic 标准化、显式命令、幂等处理，确保行为稳定可预期。

1.3 非目标（当前版本不做）

不做复杂 UI（只有 Telegram 文本界面）

不做多人并发协作场景的复杂权限体系（仅通过 ALLOWED_USER_IDS 白名单控制）

不做自然语言“多轮问答记忆”（避免长上下文幻觉）

不做自动从邮件/行程 App 抓取信息

2. 角色 & 使用场景
2.1 主要使用者（Persona）

Kimi（你自己）：Bot 管理者 & 高级用户

负责部署、维护、配置 Notion / GCal。

同时也是重度使用者，记大量家庭信息 / 日程。

Janet / Jason / Kiki：

轻度使用者

场景：发个“记一下某个账号密码”、查生日、查家庭地址等。

其他家庭成员（可扩展）：

通过增加 Telegram ID 到 ALLOWED_USER_IDS 即可接入。

2.2 核心使用场景

记录信息（NOTE）

/note Janet Apple ID 是 xxxx

/note 新家 Wifi：SSID xxx，密码 yyy

发一张账单/说明书截图，Bot 自动识别并存为笔记。

创建日程（EVENT）

/event 明天早上 9 点带 Jason 去看牙

发一张航班行程图，Bot 自动识别起飞/到达时间、地点，写入 Google Calendar。

查找信息（QUERY）

/query Janet Birthday

/query Home Address

/query Dahua Wifi

系统健康检查（STATUS）

/status 查看当前配置是否完整（Notion / GCal / Telegram 环境变量）。

普通聊天（TEXT）

发一些闲聊内容，Bot 以 LLM 的聊天回复你，不触发任何外部写入。

3. 功能范围（Scope）

当前 v6.2 版本包含：

输入通道

Telegram 文本消息

Telegram 图片消息（单张照片）

意图识别模式

自动模式：普通文本 / 图片 → 交给 LLM 决定是 EVENT / NOTE / QUERY / TEXT。

显式模式：

/note ... → 强制 NOTE 模式

/event ... → 强制 EVENT 模式

/query ... → 强制 QUERY 模式（直接查 Notion，不经过 LLM）

支持的类型

EVENT：未来日程

NOTE：静态知识

QUERY：查询已有知识

TEXT：普通对话

外部系统

Notion：一个 Database，字段包括（约定）：

Content（title）

Category（rich_text 或 select）

Topic（rich_text，标准化大写）

Date（date）

Google Calendar：

通过 Service Account 写入

支持按 Category 分配到不同日历（Kiki / Jason / Janet / Family / Kimi）

4. 详细功能需求
4.1 权限控制

使用环境变量 ALLOWED_USER_IDS 控制：

配置为逗号分隔的 Telegram 用户 ID 列表，例如：123456789,987654321

不在列表中的用户：

任何消息回复：⛔️ 未授权 ID: {user_id}

不做任何进一步处理

所有 Handler（文本 / 图片 / status）在第一行调用 check_auth，未通过则中断。

4.2 幂等处理

由于 Telegram 可能重复投递消息，v6.2 在 check_auth 中做幂等防护：

使用 (chat_id, message_id) 作为 Key。

维护 processed_ids（deque(maxlen=200)）。

如果检测到重复 Key，则直接忽略并打印日志 🔁 忽略重复消息。

4.3 NOTE 功能

输入方式：

自动模式：

用户直接发送一条消息，例如：

Janet 的 Apple ID 密码是 xxxx

LLM 根据 System Prompt 判断为 NOTE。

显式模式：

用户发送 /note ...：

例如 /note Kiki 的生日是 2007-10-10

框架会去掉 /note 前缀，只把剩下文本交给 LLM；同时设置 forced_type="NOTE"，保证 LLM 输出 NOTE JSON。

LLM 期望输出 JSON：

{
  "type": "NOTE",
  "category": "Kiki",
  "topic": "KIKI BIRTHDAY",
  "content": "Kiki's birthday is 2007-10-10."
}


业务规则：

topic：

必须为英文，格式建议为 "ENTITY ATTRIBUTE"，如：

"JANET BIRTHDAY"

"HOME ADDRESS"

"DAHUA WIFI"

代码会调用 normalize_topic 转为大写、去前后空格，用于：

写入 Notion 的 Topic 字段

查重

写入 Notion 逻辑：

若 NOTION_DATABASE_ID 未配置 → 返回失败提示，不写入。

若 topic 为空 → 拒绝写入，提示用户让其重新描述。

查重逻辑：

在 Notion 中按 Topic 属性 rich_text.equals 标准化后的大写 Topic 查找。

若找到 N 条旧记录：

将这些旧记录 archived=True（逻辑删除）。

写入新记录：

Content = 【{TOPIC}】 {content}

Category = note_data.category（默认 Family）

Topic = 标准化后的大写 Topic

Date = 当前时间

成功时：返回 "Success" 或 "已更新 (覆盖 N 条旧记录)"。

用户可见反馈：

成功示例：

📝 笔记已存入 Notion

🗂 分类: #Kiki
📌 主题: KIKI BIRTHDAY
📄 内容:
Kiki's birthday is 2007-10-10.

ℹ️ 状态: Success

🧠 LLM: DeepSeek V3


失败场景：

Notion 未配置 / Topic 缺失 / API 异常：

返回 ❌ Notion 写入失败: {错误信息}（不再使用 Markdown 格式）。

4.4 EVENT 功能

输入方式：

自动模式：

纯文本：

明天晚上七点和 Janet 去吃饭

图片：

例如带有航班信息的机票截图 / 行程单。

使用 Kimi Vision 模型。

显式模式：

/event 下周三下午三点带 Jason 看牙

前缀 /event 会被去掉，剩余文本交给 LLM；同时设置 forced_type="EVENT"。

LLM 期望输出 JSON：

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


业务规则：

category 决定使用哪个日历：

Kiki / Jason / Janet / Family / Kimi

通过环境变量：

GOOGLE_CALENDAR_ID（默认）

GOOGLE_CALENDAR_ID_KIKI

GOOGLE_CALENDAR_ID_JASON

等等

时间与时区：

start_time / end_time 格式：YYYY-MM-DD HH:MM:SS。

start_timezone 默认 Asia/Singapore，若 LLM 提供则按其值。

若缺失 end_time：

代码补一个：start_time + 1 小时。

若 end_time <= start_time：

v6.2 不再“自动修正”，只打印 warning，保留原值。

用于兼容跨时区机票这种复杂场景。

写入 Google Calendar：

使用 Service Account JSON（GOOGLE_CREDENTIALS_JSON）。

创建 Event 时写入：

summary

description（如有）

start.datetime + start.timeZone

end.datetime + end.timeZone

location（如有）

用户可见反馈：

成功示例：

✅ 日程已同步

👧 Kiki - Kiki Piano Lesson
📅 日期: 2025-02-18 (周二)
🕒 时间: 15:30 - 16:30 (Asia/Singapore)
📍 地点: XXX Music School
🔗 查看日历(链接)

🧠 LLM: DeepSeek V3


失败 & 降级逻辑：

若写入 GCal 失败：

尝试生成 .ics 文件发给用户。

文案中会包含错误信息：

⚠️ 同步失败，请手动添加

👧 Kiki - Kiki Piano Lesson
📅 2025-02-18 15:30 - 16:30
❌ 错误: {Google API 错误信息}

4.5 QUERY 功能

显式模式（推荐）：

用户输入：/query Janet Birthday

v6.2 行为：

直接绕过 LLM，将 "Janet Birthday" 作为关键字交给 query_notion。

model_name 标记为 "DirectQuery"。

自动模式（不常用）：

如果 LLM 在自动模式下返回 {"type": "QUERY", "keywords": "..."}，也会调用同一个 query_notion。

查询策略（当前实现）：

v6.2 第一版：在 Python 中对 Notion 返回的 Content + Topic 进行大小写不敏感匹配（已知存在 Birthday 查不到的问题）。

（你后面已经有了一个更鲁棒的方案，遍历所有 title / rich_text 字段，这个属于 v6.3 的改进，不写死在 v6.2 PRD 里，只在「后续迭代建议」中记录。）

返回格式：

🔍 找到相关笔记 (3条):

1. [Kiki] [KIKI BIRTHDAY] Kiki's birthday is 2007-10-10.
2. [Janet] [JANET BIRTHDAY] Janet's birthday is 1976-03-24.
3. [Family] [HOME ADDRESS] ...

🧠 LLM: DirectQuery


查不到时：

🤷‍♂️ 未找到关于 'Janet Birthday' 的记录。

🧠 LLM: DirectQuery

4.6 STATUS 功能

命令：/status

功能：检查系统配置是否完整，并给出人类可读的提示。

检查项：

Telegram Token 是否配置

Notion：

是否存在 NOTION_DATABASE_ID

是否存在 NOTION_TOKEN

分情况给出：

Missing ID & Token

Missing DB ID

Missing Token

Configured

Google Calendar：

是否存在 GOOGLE_CREDENTIALS_JSON

返回示例：

🩺 系统状态检查

✅ Telegram (ID: 123456789)
✅ Notion: Configured
❌ Google Calendar: Missing Credentials

当前 Category: Kiki, Jason, Janet, Family, Kimi
默认时区: Asia/Singapore
代码版本: v6.2 (Query Fix & Timezone Safe)

5. 交互与体验要求

所有系统消息风格：

尽量短小、结构化、带 Emoji。

保留中英文混排，便于家庭成员理解。

错误信息：

对用户：只展示必要的错误说明 + 是否需要管理员介入。

对日志：打印完整的异常栈，便于排查。

语言：

用户输入可以中英文混合。

系统回复主要中文，关键字段（Topic、Category 等）保留英文。

6. 性能 & 可靠性

预计并发量极低（自用家庭 bot）。

单机单进程足够，无需复杂扩缩容。

超时：

Kimi Vision：120 秒

DeepSeek：60 秒

避免长对话上下文：

每次调用 LLM 只带 System Prompt + 当前一轮用户消息，不做多轮对话记忆，从产品层面减轻幻觉。

7. 安全 & 隐私

所有敏感信息（账号密码、家庭地址、生日等）都存储在：

私有 Notion 工作区

私有 Google Calendar

代码层面：

所有外部密钥通过环境变量注入，不写入仓库。

Bot 本身通过 ALLOWED_USER_IDS 白名单控制访问。

不做开放式群组使用。

8. 已知问题 & 后续迭代建议

/query 搜索范围有限

当前版本对 Notion 结构有假设（Content/Topic），在部分 schema 下可能出现 “明明有 Birthday 却查不到”的情况。

建议在 v6.3 中采用“遍历所有 title/rich_text 字段”的鲁棒查询方案。

跨时区复杂机票

v6.2 不再强行调整 end_time，但完全依赖 LLM 输出的 start/end + timezone 组合。

实际航班场景仍可能出现：

起飞/落地时间正确，但 timezone 错误；

或者反之。

后续可以增加：

明确“出发地/目的地”到时区的映射校验；

或提供可视化确认步骤。

撤销（Undo）功能

产品层面已经有需求苗头：希望 /undo 能撤销最近一次 Notion/Calendar 操作。