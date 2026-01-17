import os
import logging
import json
import asyncio
import uuid
import re
import base64
from datetime import datetime, timedelta
from io import BytesIO
from collections import deque
from typing import Optional, Dict, Any, Tuple, List

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from openai import AsyncOpenAI
from icalendar import Calendar, Event, vText
import pytz
from notion_client import AsyncClient as NotionClient

# --- 1. 配置与常量 (Configuration) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# AI Clients
kimi_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
    timeout=120.0
)
deepseek_client = AsyncOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    timeout=60.0
)

# Notion Config
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID", "")
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))

# Constants
VISION_MODEL = "moonshot-v1-8k-vision-preview"
TEXT_MODEL = "deepseek-chat"
DEFAULT_TIMEZONE = "Asia/Singapore"

# Icon Mapping
CATEGORY_MAP = {
    'Kiki':   {'icon': '👧', 'cal': 'For Kiki'},
    'Jason':  {'icon': '👦', 'cal': 'For Jason'},
    'Janet':  {'icon': '👩‍🎨', 'cal': 'For Janet'},
    'Family': {'icon': '🏠', 'cal': 'For Family'},
    'Kimi':   {'icon': '👨‍💼', 'cal': 'For Kimi'}  # Default
}

# 中文星期映射
WEEKDAY_MAP = {
    0: "周一", 1: "周二", 2: "周三", 3: "周四",
    4: "周五", 5: "周六", 6: "周日"
}

allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]

if not ALLOWED_IDS:
    logging.warning("⚠️ ALLOWED_USER_IDS 为空，当前将拒绝所有用户。")

# 全局变量：使用 deque 自动维护最近 200 条消息 ID (FIFO)
processed_ids: deque[Tuple[int, int]] = deque(maxlen=200)

# --- 2. 核心工具函数 ---

async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id

    if user_id not in ALLOWED_IDS:
        await update.message.reply_text(f"⛔️ 未授权 ID: {user_id}")
        return False

    # 幂等 Key: (Chat ID, Message ID)
    key = (chat_id, msg_id)
    if key in processed_ids:
        logging.info(f"🔁 忽略重复消息: {key}")
        return False

    processed_ids.append(key)
    return True


async def safe_reply(update: Update, text: str, parse_mode: Optional[str] = 'Markdown'):
    """
    发消息带兜底：Markdown 失败自动降级为纯文本。
    """
    try:
        await update.message.reply_text(
            text,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Markdown 发送失败，降级纯文本: {e}")
        try:
            await update.message.reply_text(text, parse_mode=None)
        except Exception as e2:
            logging.error(f"纯文本发送也失败: {e2}")


async def keep_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    在长任务期间持续发送 'typing' 状态。
    """
    try:
        while True:
            await context.bot.send_chat_action(
                chat_id=chat_id,
                action=constants.ChatAction.TYPING
            )
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


def normalize_topic(raw: Optional[str]) -> str:
    """标准化 Topic：去空格，转大写，确保查重精准"""
    if not raw:
        return ""
    return raw.strip().upper()


def parse_json_from_llm(content: Any) -> Tuple[str, Any]:
    """
    从 LLM 返回内容中提取 JSON，兼容多模态返回格式。
    """
    try:
        # 1. 针对多模态/SDK 可能返回 List 的兼容处理
        if isinstance(content, list):
            try:
                text_parts: List[str] = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text_parts.append(c.get("text", ""))
                content = "\n".join(text_parts) if text_parts else str(content)
            except Exception:
                content = str(content)

        # 2. 确保是字符串
        if not isinstance(content, str):
            logging.warning(f"LLM 返回了非字符串 Content: {type(content)}")
            content = str(content)

        # 3. 提取 JSON
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            clean_content = match.group(0)
        else:
            clean_content = content.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean_content)

        if isinstance(data, dict):
            # 类型转大写，增加兼容性
            msg_type = str(data.get('type', '')).upper()

            if msg_type in ['EVENT', 'NOTE', 'QUERY']:
                return msg_type, data
            if msg_type == 'TEXT':
                return "TEXT", data.get('content', content)

        return "TEXT", content

    except (json.JSONDecodeError, AttributeError) as e:
        logging.warning(
            f"JSON 解析失败 (可能是 TEXT 或格式错误): {str(e)} | "
            f"Prefix: {str(content)[:80]}"
        )
        return "TEXT", content

# --- 3. Google Calendar 模块 ---

def _google_api_sync_call(event_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    同步调用 Google Calendar API。
    注意：不再强行“修正” end_time <= start_time，避免跨时区航班被错误调整。
    """
    try:
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not credentials_json:
            return False, "未设置 Credentials"

        category = event_data.get('category', 'Kimi')
        env_key = (
            f"GOOGLE_CALENDAR_ID_{category.upper()}"
            if category != 'Kimi'
            else "GOOGLE_CALENDAR_ID"
        )
        target_calendar_id = os.getenv(
            env_key,
            os.getenv("GOOGLE_CALENDAR_ID", "primary")
        )

        import json
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        service_account_info = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)

        start_tz = event_data.get('start_timezone', DEFAULT_TIMEZONE)
        end_tz = event_data.get('end_timezone', start_tz)

        fmt = '%Y-%m-%d %H:%M:%S'
        dt_start = datetime.strptime(event_data['start_time'], fmt)

        # 处理 end_time：缺失则补 +1 小时；存在则原样发送，只做 warning，不改值
        if event_data.get('end_time'):
            try:
                dt_end = datetime.strptime(event_data['end_time'], fmt)
                if dt_end <= dt_start:
                    logging.warning(
                        "⚠️ 发现 end_time <= start_time，仍按原值写入 "
                        "(可能是跨时区航班或特殊事件，请人工确认)："
                        f" start={event_data['start_time']} end={event_data['end_time']}"
                    )
            except Exception as e:
                logging.warning(
                    f"⚠️ end_time 解析失败，将使用 +1 小时兜底: {e}, raw={event_data.get('end_time')}"
                )
                dt_end = dt_start + timedelta(hours=1)
                event_data['end_time'] = dt_end.strftime(fmt)
        else:
            dt_end = dt_start + timedelta(hours=1)
            event_data['end_time'] = dt_end.strftime(fmt)

        event_body = {
            'summary': event_data.get('summary', '未命名日程'),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data['start_time'].replace(' ', 'T'),
                'timeZone': start_tz
            },
            'end': {
                'dateTime': event_data['end_time'].replace(' ', 'T'),
                'timeZone': end_tz
            },
        }
        if event_data.get('location'):
            event_body['location'] = event_data['location']

        created_event = service.events().insert(
            calendarId=target_calendar_id,
            body=event_body
        ).execute()
        return True, created_event.get('htmlLink', '')
    except Exception as e:
        err_msg = str(e)
        if "HttpError 404" in err_msg:
            return False, (
                f"API 错误: 找不到日历 ID ({target_calendar_id})，"
                f"请检查环境变量配置。"
            )
        return False, err_msg


async def add_to_google_calendar(event_data: Dict[str, Any]) -> Tuple[bool, str]:
    return await asyncio.to_thread(_google_api_sync_call, event_data)


def create_ics_file(event_data: Dict[str, Any]):
    try:
        cal = Calendar()
        cal.add('prodid', '-//Bot//CN')
        cal.add('version', '2.0')
        cal.add('method', 'PUBLISH')

        event = Event()
        event.add('uid', str(uuid.uuid4()) + '@bot')
        event.add('summary', event_data.get('summary', 'Event'))

        tz_start_str = event_data.get('start_timezone', DEFAULT_TIMEZONE)
        tz_end_str = event_data.get('end_timezone', tz_start_str)

        dt_start_naive = datetime.strptime(
            event_data['start_time'], '%Y-%m-%d %H:%M:%S'
        )
        tz_start = pytz.timezone(tz_start_str)
        event.add('dtstart', tz_start.localize(dt_start_naive))

        if event_data.get('end_time'):
            dt_end_naive = datetime.strptime(
                event_data['end_time'], '%Y-%m-%d %H:%M:%S'
            )
            tz_end = pytz.timezone(tz_end_str)
            event.add('dtend', tz_end.localize(dt_end_naive))
        else:
            dt_end = tz_start.localize(dt_start_naive + timedelta(hours=1))
            event.add('dtend', dt_end)

        event.add('dtstamp', datetime.now(pytz.utc))

        if event_data.get('location'):
            event.add('location', vText(event_data['location']))
        if event_data.get('description'):
            event.add('description', vText(event_data['description']))

        cal.add_component(event)

        io_buffer = BytesIO()
        io_buffer.write(cal.to_ical())
        io_buffer.seek(0)

        summary = event_data.get('summary', 'event')
        safe_summary = "".join(
            [c for c in summary if c.isalnum() or c in (' ', '-', '_')]
        ).strip()
        return io_buffer, f"{safe_summary}.ics"
    except Exception:
        return None, None

# --- 4. Notion 模块 ---


async def add_to_notion(note_data: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        if not NOTION_DB_ID:
            return False, "❌ 暂时无法保存笔记：Notion 数据库未配置（NOTION_DATABASE_ID）。"

        raw_topic = note_data.get('topic')
        if not raw_topic:
            return False, "⚠️ 拒绝写入：LLM 未提供 Topic (请尝试重新描述)"

        topic = normalize_topic(raw_topic)
        content_val = note_data.get('content', '无内容')
        final_content = f"【{topic}】 {content_val}"

        existing_pages: List[Dict[str, Any]] = []

        # 1. 查重（按标准化 Topic）
        filter_rule = {
            "property": "Topic",
            "rich_text": {"equals": topic}
        }
        logging.info(f"[Notion] 查重 (Standardized): {topic}")

        try:
            response = await notion.databases.query(
                database_id=NOTION_DB_ID,
                filter=filter_rule
            )
            existing_pages = response.get("results", [])
            logging.info(f"[Notion] 查重结果: 发现 {len(existing_pages)} 条旧记录")
        except Exception as search_err:
            logging.error(f"[Notion] 查重请求失败: {search_err}")
            existing_pages = []

        # 归档旧记录
        for page in existing_pages:
            try:
                await notion.pages.update(page_id=page["id"], archived=True)
            except Exception as archive_err:
                logging.error(f"[Notion] 归档失败: {archive_err}")

        # 2. 写入
        # 注意：这里假设 Notion 中的 Category 是 Rich Text 类型。
        properties = {
            "Content": {
                "title": [{"text": {"content": final_content}}]
            },
            "Category": {
                "rich_text": [{
                    "text": {"content": note_data.get('category', 'Family')}
                }]
            },
            "Topic": {
                "rich_text": [{"text": {"content": topic}}]
            },
            "Date": {
                "date": {"start": datetime.now().isoformat()}
            }
        }

        logging.info(f"[Notion] 写入新记录: {topic}")
        await notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=properties
        )

        status_msg = "Success"
        if existing_pages:
            status_msg = f"已更新 (覆盖 {len(existing_pages)} 条旧记录)"

        return True, status_msg

    except Exception as e:
        logging.error(f"[Notion] add_to_notion 异常: {e}")
        return False, str(e)


async def query_notion(keywords: str) -> List[str]:
    """
    v6.2：改为 Python 本地过滤版查询，避免 Notion filter 的各种坑。

    策略：
    1. 用 databases.query 拉最近 N 条记录（按 Date 降序）。
    2. 在 Python 里把 Topic + Content 拼起来做小写匹配。
    3. 所有 search_terms 都在文本里出现才算命中。
    """
    try:
        if not NOTION_DB_ID:
            return ["❌ Notion 未配置，无法查询。"]

        # 拆分关键词，去掉多余空格
        search_terms = [t.strip() for t in re.split(r"\s+", keywords) if t.strip()]
        if not search_terms:
            return []

        logging.info(f"[Notion] 执行查询 (Python 过滤): {search_terms}")

        try:
            response = await notion.databases.query(
                database_id=NOTION_DB_ID,
                page_size=200,  # 家用场景足够
                sorts=[{"property": "Date", "direction": "descending"}]
            )
        except Exception as e:
            logging.error(f"[Notion] 查询请求失败: {e}")
            return []

        results: List[str] = []

        for page in response.get("results", []):
            try:
                props = page["properties"]

                # Content
                content_list = props["Content"]["title"]
                content_text = "".join(
                    [t["text"]["content"] for t in content_list]
                )

                # Topic（不一定有）
                topic_text = ""
                if "Topic" in props:
                    topic_prop = props["Topic"]
                    if topic_prop["type"] == "rich_text" and topic_prop["rich_text"]:
                        topic_text = "".join(
                            [t["text"]["content"] for t in topic_prop["rich_text"]]
                        )

                # Category
                category = "未分类"
                if "Category" in props:
                    cat_prop = props["Category"]
                    if cat_prop["type"] == "rich_text" and cat_prop["rich_text"]:
                        category = "".join(
                            [t["text"]["content"] for t in cat_prop["rich_text"]]
                        )
                    elif cat_prop["type"] == "select" and cat_prop["select"]:
                        category = cat_prop["select"]["name"]

                haystack = f"{topic_text} {content_text}".lower()
                if all(term.lower() in haystack for term in search_terms):
                    results.append(f"[{category}] {content_text}")
            except Exception as e:
                logging.error(f"[Notion] 结果解析失败: {e}")
                continue

        return results

    except Exception as e:
        logging.error(f"Notion 查询逻辑错误: {e}")
        return []

# --- 5. 系统 Prompt (v6.2) ---

def get_system_prompt() -> str:
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
    return f"""
    Current Time: {current_time_str} ({DEFAULT_TIMEZONE}).

    【Task】Analyze input, classify intent, output JSON.
    1. EVENT: Future events (Calendar).
    2. NOTE: Static info (Notion).
    3. QUERY: Search stored info.
    4. TEXT: Casual chat.

    【Important】
    - If the user explicitly defines the type (e.g. via command), you MUST output that specific type.

    【Rules for NOTE】
    1. Topic Naming: "Entity + Attribute" (e.g. "JANET BIRTHDAY").
       ALWAYS English, ALWAYS Upper Case preferred.
    2. Content: Standardize dates to YYYY-MM-DD.

    【Rules for EVENT】
    - Provide "start_timezone" and "end_timezone".

    【JSON Schema】
    EVENT: {{
        "type": "EVENT",
        "category": "...",
        "summary": "...",
        "start_time": "YYYY-MM-DD HH:MM:SS",
        "start_timezone": "Area/City",
        "end_time": "YYYY-MM-DD HH:MM:SS",
        "end_timezone": "Area/City",
        "location": "..."
    }}
    NOTE: {{
        "type": "NOTE",
        "category": "...",
        "topic": "...",
        "content": "..."
    }}
    QUERY: {{
        "type": "QUERY",
        "keywords": "..."
    }}
    """

# --- 6. 统一回复处理 ---

async def reply_handler(
    update: Update,
    status_msg: Optional[Any],
    msg_type: str,
    result_data: Dict[str, Any],
    model_name: str
):
    footer = f"\n\n🧠 LLM: {model_name}"

    try:
        if msg_type == "EVENT":
            success, google_result = await add_to_google_calendar(result_data)
            category = result_data.get('category', 'Kimi')
            style = CATEGORY_MAP.get(category, CATEGORY_MAP['Kimi'])

            # 解析时间用于展示
            try:
                dt_start = datetime.strptime(
                    result_data.get('start_time'), '%Y-%m-%d %H:%M:%S'
                )
                weekday_cn = WEEKDAY_MAP.get(dt_start.weekday(), "")
                date_str = dt_start.strftime('%Y-%m-%d') + f" ({weekday_cn})"
                time_str = dt_start.strftime('%H:%M')

                if result_data.get('end_time'):
                    dt_end = datetime.strptime(
                        result_data.get('end_time'), '%Y-%m-%d %H:%M:%S'
                    )
                    time_str += f" - {dt_end.strftime('%H:%M')}"
                else:
                    time_str += " - 约1小时"

                tz_info = result_data.get('start_timezone', DEFAULT_TIMEZONE)
            except Exception:
                date_str = result_data.get('start_time')
                time_str = "Unknown"
                tz_info = ""

            summary = result_data.get('summary', '未命名日程')
            loc = result_data.get('location', '')
            loc_line = f"\n📍 地点: {loc}" if loc else ""

            if success:
                text = (
                    f"✅ **日程已同步**\n\n"
                    f"{style['icon']} **{category} - {summary}**\n"
                    f"📅 日期: {date_str}\n"
                    f"🕒 时间: {time_str} ({tz_info}){loc_line}\n"
                    f"🔗 [查看日历]({google_result}){footer}"
                )
                if status_msg:
                    await status_msg.delete()
                await safe_reply(update, text)
            else:
                # 失败降级处理
                ics_file, filename = create_ics_file(result_data)
                text = (
                    f"⚠️ **同步失败，请手动添加**\n\n"
                    f"{style['icon']} **{summary}**\n"
                    f"📅 {date_str} {time_str}\n"
                    f"❌ 错误: {google_result}\n"
                    f"{footer}"
                )

                if status_msg:
                    await status_msg.delete()
                if ics_file:
                    try:
                        await update.message.reply_document(
                            document=ics_file,
                            filename=filename,
                            caption=text,
                            parse_mode='Markdown'
                        )
                    except Exception:
                        await update.message.reply_document(
                            document=ics_file,
                            filename=filename,
                            caption=text,
                            parse_mode=None
                        )
                else:
                    await safe_reply(
                        update,
                        text + "\n\n❌ (无法生成 .ics 文件)"
                    )

        elif msg_type == "NOTE":
            success, msg = await add_to_notion(result_data)
            category = result_data.get('category', 'Family')

            if success:
                status_icon = "🔄" if "更新" in msg else "📝"
                safe_topic = normalize_topic(result_data.get('topic'))
                content_display = result_data.get('content', '').strip()

                text = (
                    f"{status_icon} **笔记已存入 Notion**\n\n"
                    f"🗂 分类: #{category}\n"
                    f"📌 主题: {safe_topic}\n"
                    f"📄 内容:\n{content_display}\n\n"
                    f"ℹ️ 状态: {msg}{footer}"
                )
                if status_msg:
                    await status_msg.delete()
                await safe_reply(update, text)
            else:
                text = f"❌ Notion 写入失败: {msg}{footer}"
                if status_msg:
                    await status_msg.delete()
                await safe_reply(update, text, parse_mode=None)

        elif msg_type == "QUERY":
            keywords = result_data.get('keywords', '')
            results = await query_notion(keywords)
            if results:
                text = f"🔍 **找到相关笔记 ({len(results)}条):**\n\n"
                for i, res in enumerate(results, 1):
                    text += f"{i}. {res}\n"
                text += footer
            else:
                text = (
                    f"🤷‍♂️ **未找到关于 '{keywords}' 的记录。**"
                    f"{footer}"
                )
            if status_msg:
                await status_msg.delete()
            await safe_reply(update, text)

    except Exception as e:
        if status_msg:
            await status_msg.delete()
        await safe_reply(
            update,
            f"Error in reply_handler: {str(e)}",
            parse_mode=None
        )


async def process_llm_result(
    update: Update,
    status_msg: Optional[Any],
    content: Any,
    model_name: str,
    forced_type: Optional[str] = None
):
    """
    公共逻辑：解析 JSON 并分发任务。
    包含强制模式下的防御性检查。
    """
    msg_type, result = parse_json_from_llm(content)

    # 显式模式下，强制覆盖类型
    if forced_type:
        if not isinstance(result, dict):
            logging.warning(
                f"⚠️ 强制模式({forced_type})下 LLM 未返回合法 JSON，自动退回 TEXT。"
            )
            text = (
                f"⚠️ **指令执行失败**\n"
                f"AI 未能生成有效的 {forced_type} 数据。\n\n"
                f"原始回复:\n{str(result)}\n\n"
                f"🧠 LLM: {model_name}"
            )
            if status_msg:
                await status_msg.delete()
            await safe_reply(update, text)
            return

        logging.info(f"强制模式: 将 {msg_type} 修正为 {forced_type}")
        msg_type = forced_type

    if msg_type in ["EVENT", "NOTE", "QUERY"]:
        if isinstance(result, dict):
            await reply_handler(update, status_msg, msg_type, result, model_name)
        else:
            if status_msg:
                await status_msg.delete()
            await safe_reply(
                update,
                str(result) + f"\n\n🧠 LLM: {model_name}"
            )
    else:
        if status_msg:
            await status_msg.delete()
        await safe_reply(update, result + f"\n\n🧠 LLM: {model_name}")

# --- 7. 主逻辑 & 命令处理 ---


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return

    # 检查环境变量 (更详细)
    tg_ok = "✅" if os.getenv("TELEGRAM_TOKEN") else "❌"

    notion_db = os.getenv("NOTION_DATABASE_ID")
    notion_token = os.getenv("NOTION_TOKEN")
    if notion_db and notion_token:
        notion_status = "✅ Configured"
    elif not notion_db and not notion_token:
        notion_status = "❌ Missing ID & Token"
    elif not notion_db:
        notion_status = "❌ Missing DB ID"
    else:
        notion_status = "❌ Missing Token"

    gcal_ok = (
        "✅ Configured"
        if os.getenv("GOOGLE_CREDENTIALS_JSON")
        else "❌ Missing Credentials"
    )

    user_id = update.effective_user.id

    msg = (
        f"🩺 **系统状态检查**\n\n"
        f"{tg_ok} Telegram (ID: {user_id})\n"
        f"{notion_status[0]} Notion: {notion_status}\n"
        f"{gcal_ok[0]} Google Calendar: {gcal_ok}\n\n"
        f"当前 Category: {', '.join(CATEGORY_MAP.keys())}\n"
        f"默认时区: {DEFAULT_TIMEZONE}\n"
        f"代码版本: v6.2 (Query Fix & Timezone Safe)"
    )
    await safe_reply(update, msg)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    typing_task = asyncio.create_task(
        keep_typing(context, update.effective_chat.id)
    )
    status_msg = await update.message.reply_text("👁️ Kimi 正在分析... ")

    try:
        photo_obj = update.message.photo[-1]
        photo_file = await photo_obj.get_file()
        file_stream = BytesIO()
        await photo_file.download_to_memory(out=file_stream)
        base64_image = base64.b64encode(file_stream.getvalue()).decode('utf-8')

        response = await kimi_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": get_system_prompt()},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=2000
        )

        typing_task.cancel()
        await process_llm_result(
            update,
            status_msg,
            response.choices[0].message.content,
            "Kimi Vision"
        )

    except Exception as e:
        typing_task.cancel()
        if status_msg:
            await status_msg.delete()
        await safe_reply(update, f"Error: {str(e)}", parse_mode=None)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return
    typing_task = asyncio.create_task(
        keep_typing(context, update.effective_chat.id)
    )

    raw_text = update.message.text.strip()
    forced_type: Optional[str] = None
    content_to_llm: str = raw_text

    # 显式命令解析
    if raw_text.lower().startswith("/note"):
        forced_type = "NOTE"
        content_to_llm = raw_text[5:].strip()
    elif raw_text.lower().startswith("/event"):
        forced_type = "EVENT"
        content_to_llm = raw_text[6:].strip()
    elif raw_text.lower().startswith("/query"):
        # v6.2：显式查询完全绕开 LLM，直接用用户输入做关键词
        forced_type = "QUERY"
        keywords = raw_text[6:].strip()

        if not keywords:
            typing_task.cancel()
            await safe_reply(
                update,
                "🤔 你想查什么？请在 /query 后面加上关键词，例如：`/query Janet Birthday`"
            )
            return

        typing_task.cancel()
        await reply_handler(
            update,
            None,
            "QUERY",
            {"type": "QUERY", "keywords": keywords},
            model_name="DirectQuery"
        )
        return

    # 其他情况仍然走 LLM
    system_prompt = get_system_prompt()
    if forced_type:
        system_prompt += (
            f"\n\n【IMPORTANT】User explicitly requested type: {forced_type}. "
            f"You MUST output JSON with type='{forced_type}'."
        )

    try:
        response = await deepseek_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_to_llm}
            ],
            temperature=0.3
        )
        typing_task.cancel()
        await process_llm_result(
            update,
            None,
            response.choices[0].message.content,
            "DeepSeek V3",
            forced_type=forced_type
        )

    except Exception as e:
        typing_task.cancel()
        await safe_reply(update, f"Error: {str(e)}", parse_mode=None)


if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("❌ 未设置 TELEGRAM_TOKEN")
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        # 注册 Command Handler
        app.add_handler(CommandHandler("status", handle_status))

        # 注册 Message Handler
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text)
        )

        # 显式命令入口：/note /event /query
        app.add_handler(
            CommandHandler(["note", "event", "query"], handle_text)
        )

        print("✅ 全能管家 v6.2 (Query Fix & Timezone Safe) 已启动...")
        app.run_polling()
