《全能管家 Telegram Bot – 系统设计说明（v6.2 冻结版）》

0. 文档元信息

目标版本：v6.2（与当前部署 main.py 一致）

范围：单文件 main.py 的架构、模块职责、数据流、依赖配置。

受众：

未来的“你”（重启这个项目时）

其他 AI（例如 Gemini / 未来的 ChatGPT），用于快速建立技术上下文。

1. 整体架构概览
1.1 高层组件

Telegram Bot Server（Zeabur 上的 Python 容器）

使用 python-telegram-bot 的 Application.run_polling() 模式。

负责接收用户消息、调用 LLM、调用 Notion / Google Calendar。

LLM 提供方

Kimi Vision（Moonshot API）

模型：moonshot-v1-8k-vision-preview

用于图片 + 文本混合理解。

DeepSeek Chat

模型：deepseek-chat

用于纯文本理解 & 聊天。

存储层

Notion Database

存储家庭知识（NOTE）。

Google Calendar

存储家庭时间轴（EVENT）。

1.2 调用关系（文字版时序图）

以 /note ... 为例：

用户在 Telegram 输入 /note Janet 的生日是 1976-03-24。

Telegram → Bot（Webhook/long polling）。

Bot：

handle_text：

check_auth 验证用户，幂等。

解析命令，设置 forced_type="NOTE"，去掉前缀得到 content_to_llm。

构造 system_prompt（带当前时间 / 规则），附加“必须输出 NOTE JSON”的说明。

调用 DeepSeek Chat。

DeepSeek 返回 JSON 文本。

process_llm_result：

parse_json_from_llm → 得到 msg_type="NOTE" + note_data。

forced_type 再次覆盖，确保类型仍为 NOTE。

调用 reply_handler(..., msg_type="NOTE", result_data=note_data)。

reply_handler：

调用 add_to_notion(note_data)。

根据成功 / 失败构造文本消息，回复给 Telegram 用户。

其他类型（EVENT / QUERY / TEXT）类似。

2. 技术栈 & 依赖

Python 3.x

主要库：

python-telegram-bot v20+

openai（用于 Moonshot / DeepSeek）

notion_client

google-api-python-client + google-auth

icalendar

pytz

部署环境：Zeabur 容器（长时间运行的进程即可，不需要额外服务）。

3. 模块划分（按 main.py 中的逻辑章节）

配置与常量（Configuration）

日志配置

LLM 客户端初始化

Notion 客户端初始化

常量定义（模型名 / 默认时区 / Category Map / 中文星期）

环境变量解析（ALLOWED_USER_IDS）

核心工具函数

check_auth

safe_reply

keep_typing

normalize_topic

parse_json_from_llm

Google Calendar 模块

_google_api_sync_call

add_to_google_calendar

create_ics_file

Notion 模块

add_to_notion

query_notion（当前版本：Content+Topic 简化版；你有一个更鲁棒的升级方案）

系统 Prompt

get_system_prompt：封装对 LLM 的 System 指令。

统一回复处理

reply_handler

process_llm_result

主逻辑 & 命令处理

handle_status

handle_photo

handle_text

程序入口：if __name__ == '__main__': ... run_polling()

4. 关键模块设计细节
4.1 check_auth & 幂等
async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id

    if user_id not in ALLOWED_IDS: ...
    key = (chat_id, msg_id)
    if key in processed_ids: ...
    processed_ids.append(key)


processed_ids 使用 deque(maxlen=200)：

内存有上限，不会无限膨胀。

对家庭场景足够。

4.2 LLM 解析 & JSON 抽取

所有来自 LLM 的回复都先经过 parse_json_from_llm：

如果 Content 是 list（多模态），抽取其中 {"type": "text"} 的部分。

使用正则 re.search(r'\{[\s\S]*\}', content) 尝试找到 JSON 块。

json.loads 后，如果是 dict：

读取 type 字段（转大写）。

返回 (msg_type, data)。

出错则回退为 TEXT。

process_llm_result 是统一入口：

在此处理 forced_type（显式命令）。

在 NOTE / EVENT / QUERY 三类时调用 reply_handler。

4.3 Prompt 设计

System Prompt 包含：

当前时间 + 时区；

类型定义（EVENT / NOTE / QUERY / TEXT）；

NOTE 规则：

Topic = 英文 + 大写；

内容中的日期标准化为 YYYY-MM-DD。

EVENT 规则：

要给出 start_timezone / end_timezone；

给出 location。

JSON Schema 示例。

显式命令时，在 System Prompt 后追加：

【IMPORTANT】User explicitly requested type: {forced_type}. 
You MUST output JSON with type='{forced_type}'.


确保 LLM 不“自作主张”改类型。

4.4 Notion 写入 & 去重

Topic 标准化：

normalize_topic(raw) → 去空格 + 大写。

去重：

调用 notion.databases.query，按 Topic.rich_text.equals(topic) 查找。

对所有旧记录 pages.update(..., archived=True).

新记录属性：

Content.title → 【TOPIC】 {content}

Category.rich_text → 短文本，如 Kiki、PERSONAL

Topic.rich_text → 标准化 Topic

Date.date.start → datetime.now().isoformat()

4.5 Notion 查询（query_notion）

当前 v6.2 版本逻辑（简略）：

拆分关键词为多个 term。

单个 term：OR 查询：

Content.title.contains(term) OR Topic.rich_text.equals(term.upper())

多个 term：AND 查询：

所有 term 都在 Content.title 中 contains。

返回前，将结果组装为 "[{category}] {content_text}" 形式。

已知问题：

当关键词只出现在 Topic 或 Content 中的一部分时，在某些 schema 下可能无法命中（特别是 Birthday 案例）。

你已经有了一个“扫描所有文本字段”的改进版，这个属于后续版本。

4.6 Google Calendar 写入

_google_api_sync_call 内部：

从环境变量读 Service Account JSON。

根据 category 选择日历 ID：

GOOGLE_CALENDAR_ID_KIKI 等。

时间处理：

解析 start_time，格式错误会抛异常。

end_time：

缺失 → start + 1h。

存在且解析成功但 <= start → 打 warning，但不改变（保留原值）。

解析失败 → fallback 到 start + 1h。

调用 Google API 创建事件：

失败时，返回错误字符串 → 上层用于生成提示。

create_ics_file：

用 icalendar 库生成 .ics，时间带时区。

5. 环境变量 & 配置

在 Zeabur / 本地运行时，需要配置以下环境变量：

Telegram

TELEGRAM_TOKEN

LLM

OPENAI_API_KEY（Kimi / Moonshot）

DEEPSEEK_API_KEY

Notion

NOTION_DATABASE_ID

NOTION_TOKEN

Google Calendar

GOOGLE_CREDENTIALS_JSON（Service Account JSON 文本）

GOOGLE_CALENDAR_ID（默认日历）

GOOGLE_CALENDAR_ID_KIKI

GOOGLE_CALENDAR_ID_JASON

GOOGLE_CALENDAR_ID_JANET

GOOGLE_CALENDAR_ID_FAMILY

GOOGLE_CALENDAR_ID_KIMI

（后四/五个按需要配置）

权限

ALLOWED_USER_IDS：逗号分隔的 Telegram user id 列表。

6. 部署 & 运维要点（简版）

依赖安装：使用当前 requirements.txt。

Zeabur 容器命令：

形如：python main.py

日志查看：

依赖 logging 输出到 stdout，由 Zeabur 收集。

故障排查建议：

查询失败 → 看 Notion 查询日志（filter 结构、结果条数）。

EVENT 创建失败 → 关注 Google API 返回的错误字符串。

LLM 异常 → 查看 JSON 解析失败 / Error: ... 的日志。

7. 演进与扩展建议（给未来的 v6.3+）

这部分不是当前代码行为，而是“系统设计层”的建议，方便以后继续做。

更鲁棒的 query_notion

改为遍历所有 title + rich_text 属性，拼成一个 haystack 做本地匹配。

不再依赖固定的 Content / Topic 列名。

Undo 能力

在 reply_handler 中记录最近一次写入的：

Notion page_id

Calendar event_id

/undo 命令：

默认撤销当前用户最近一次成功的 NOTE 或 EVENT。

Config 自检 & 可视化

/status 增强为：

显示当前 Notion DB 的列名 / 类型快照；

显示当前可用的 Google Calendar 列表。

复杂航班场景优化

在 EVENT JSON 中约定字段：

origin_airport, destination_airport

通过机场代码推断时区辅助校验。