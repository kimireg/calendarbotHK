import os
import re
import base64
import logging
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta, time
from io import BytesIO
from collections import deque
from typing import Tuple, Dict, Any, Optional, List

from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from openai import AsyncOpenAI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz

# --- 1. 配置与初始化 (Configuration) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

VISION_MODEL = "moonshot-v1-8k-vision-preview"
TEXT_MODEL = "deepseek-chat"
DEFAULT_HOME_TZ = "Asia/Singapore"
DB_PATH = "data/calendar_bot_v2.db"

# 权限与幂等性
allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
processed_ids = deque(maxlen=200)

# 允许的 Category 集合 (P0-2)
VALID_CATEGORIES = {"Kimi", "Kiki", "Jason", "Janet", "Family"}

# --- 2. 数据库层 (Database Layer) ---
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY, current_timezone TEXT DEFAULT 'Asia/Singapore', updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, calendar_id TEXT, google_event_id TEXT, summary TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()

def get_user_timezone(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        res = c.execute('SELECT current_timezone FROM user_state WHERE user_id = ?', (user_id,)).fetchone()
        return res[0] if res else DEFAULT_HOME_TZ

def set_user_timezone(user_id: int, timezone: str):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO user_state (user_id, current_timezone) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET current_timezone=excluded.current_timezone', (user_id, timezone))
        conn.commit()

def save_event_history(user_id, calendar_id, event_id, summary):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO event_history (user_id, calendar_id, google_event_id, summary) VALUES (?, ?, ?, ?)', (user_id, calendar_id, event_id, summary))
        return c.lastrowid

def get_event_from_history(row_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        return c.execute('SELECT calendar_id, google_event_id, summary FROM event_history WHERE id = ?', (row_id,)).fetchone()

def get_last_event_summary(user_id):
    """P1-1: 获取最近一条成功事件"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        res = c.execute('SELECT summary, created_at FROM event_history WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,)).fetchone()
        return res if res else None

# --- 3. 鉴权助手 ---
async def check_auth(update: Update) -> bool:
    user_id = update.effective_user.id
    if user_id not in ALLOWED_IDS:
        await update.message.reply_text(f"⛔️ 未授权 ID: {user_id}")
        return False
    return True

# --- 4. 逻辑层：解析与校验 ---

def extract_json_from_text(text: str) -> Optional[dict]:
    try: return json.loads(text)
    except: pass
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match: return json.loads(match.group(0))
    except: pass
    return None

async def parse_llm_response(response) -> Tuple[str, Any]:
    content = response.choices[0].message.content
    clean_content = content.replace("```json", "").replace("```", "").strip()
    
    data = extract_json_from_text(clean_content)
    
    # 只要有 is_event=true 且是字典，就认为是 Event
    if data and isinstance(data, dict) and data.get('is_event'):
        return "EVENT", data
    
    return "TEXT", content

# [P0-2] 增强 Schema 校验
def validate_and_fix_payload(data: dict) -> Tuple[bool, str]:
    # 1. 基础字段
    if not data.get('summary'): return False, "缺少事件标题 (summary)"
    if not data.get('start_time'): return False, "缺少开始时间 (start_time)"
    
    # 2. Category 校验与回退
    cat = data.get('category')
    if cat not in VALID_CATEGORIES:
        logger.warning(f"⚠️ Unknown category '{cat}', fallback to 'Kimi'")
        data['category'] = 'Kimi' # 原地修正
        
    # 3. 时间格式校验
    try:
        datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        if data.get('end_time'):
            datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False, "时间格式错误，需为 YYYY-MM-DD HH:MM:SS"
        
    return True, "OK"

# [P1-2] 时区显示优化
def get_timezone_display_name(tz_str: str) -> str:
    mapping = {
        "Asia/Singapore": "新加坡",
        "Asia/Shanghai": "上海",
        "Asia/Tokyo": "东京",
        "Asia/Hong_Kong": "香港",
        "Europe/London": "伦敦",
        "America/New_York": "纽约",
        "America/Los_Angeles": "洛杉矶"
    }
    # 如果在映射表里，显示中文名；否则显示 IANA 原名
    return mapping.get(tz_str, tz_str)

def normalize_recurrence(recurrence_data):
    if not recurrence_data: return None
    lst = [recurrence_data] if isinstance(recurrence_data, str) else recurrence_data
    norm = []
    for r in lst:
        r = r.strip()
        if r: norm.append(r if r.upper().startswith("RRULE:") else "RRULE:" + r)
    return norm if norm else None

def resolve_timezone(tz_str: str, user_fallback_tz: str) -> Tuple[str, Any, bool]:
    """返回: (tz_str, tz_obj, is_fallback)"""
    if not tz_str or tz_str == "UserContext":
        return user_fallback_tz, pytz.timezone(user_fallback_tz), False 
    
    corrections = {
        'Asia/Beijing': 'Asia/Shanghai', 'Asia/Osaka': 'Asia/Tokyo', 'Asia/Kyoto': 'Asia/Tokyo',
        'America/Washington': 'America/New_York', 'America/San_Francisco': 'America/Los_Angeles',
        'US/Pacific': 'America/Los_Angeles', 'US/Eastern': 'America/New_York'
    }
    candidate_tz = corrections.get(tz_str, tz_str)
    
    try:
        return candidate_tz, pytz.timezone(candidate_tz), False
    except pytz.UnknownTimeZoneError:
        logger.warning(f"⚠️ Unrecognized timezone '{tz_str}'. Fallback to '{user_fallback_tz}'.")
        return user_fallback_tz, pytz.timezone(user_fallback_tz), True 

def smart_fix_year(dt_naive, tz_obj):
    """Start Time 年份修正 (保持不变)"""
    now = datetime.now(tz_obj)
    dt_aware = tz_obj.localize(dt_naive)
    while dt_aware < now - timedelta(days=90):
        try:
            dt_naive = dt_naive.replace(year=dt_naive.year + 1)
            dt_aware = tz_obj.localize(dt_naive)
            logger.info(f"StartYear Fix: {dt_naive.year}")
        except ValueError: break
    return dt_aware, dt_naive

# [P0-1] End Time 跨天修正逻辑 (新)
def smart_fix_end_time(dt_start_aware, dt_end_naive_raw, end_tz_obj):
    """
    1. 继承 Start Year
    2. 如果 End < Start，优先尝试 +1 Day，其次尝试 +1 Year (跨年)
    """
    # 1. 继承开始时间的年份
    current_year = dt_start_aware.year
    try:
        dt_end_naive = dt_end_naive_raw.replace(year=current_year)
    except ValueError: # 闰年保护
        dt_end_naive = dt_end_naive_raw.replace(year=current_year, day=28) 

    dt_end_aware = end_tz_obj.localize(dt_end_naive)

    # 2. 检查时间倒流 (跨天/跨年)
    if dt_end_aware < dt_start_aware:
        # 策略A: 尝试 +1 天 (绝大多数情况是跨天航班)
        dt_end_naive_plus_day = dt_end_naive + timedelta(days=1)
        dt_end_aware_plus_day = end_tz_obj.localize(dt_end_naive_plus_day)

        if dt_end_aware_plus_day >= dt_start_aware:
            return dt_end_aware_plus_day
        
        # 策略B: 如果 +1 天还不够 (比如 12-31 到 01-01 且跨时区), 尝试 +1 年
        # 注意：这里我们简单假设跨年就是 +1 年
        try:
            dt_end_naive_plus_year = dt_end_naive.replace(year=current_year + 1)
            dt_end_aware_plus_year = end_tz_obj.localize(dt_end_naive_plus_year)
            return dt_end_aware_plus_year
        except ValueError:
            pass
            
        # 兜底：如果都失败，直接用 +1 天的结果，避免逻辑太复杂
        return dt_end_aware_plus_day

    return dt_end_aware

# --- 5. Google API Services ---

def get_calendar_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json: return None
    try:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/calendar'])
        return build('calendar', 'v3', credentials=creds)
    except: return None

# 同步 Wrapper
def _sync_check_conflicts(service, cal_id, start_dt, end_dt):
    try:
        items = service.events().list(
            calendarId=cal_id, timeMin=start_dt.isoformat(), timeMax=end_dt.isoformat(), 
            singleEvents=True, orderBy='startTime'
        ).execute().get('items', [])
        return [f"• {e.get('summary', '未知')}" for e in items if 'dateTime' in e['start']]
    except: return []

def _sync_insert_event(service, cal_id, body):
    return service.events().insert(calendarId=cal_id, body=body).execute()

def _sync_delete_event(service, cal_id, eid):
    service.events().delete(calendarId=cal_id, eventId=eid).execute()

def _sync_list_events(service, cal_id, start_iso, end_iso):
    # P2-1: 列出日程
    return service.events().list(
        calendarId=cal_id, timeMin=start_iso, timeMax=end_iso, 
        singleEvents=True, orderBy='startTime'
    ).execute().get('items', [])

async def create_calendar_event(event_data, user_current_tz):
    """Returns: (Success, Link, Conflicts, Start_DT, End_DT, Calendar_ID, Event_ID, Fallback_Msg)"""
    
    # 1. P0-2 校验与修正
    is_valid, err_msg = validate_and_fix_payload(event_data)
    if not is_valid:
        return False, f"数据校验失败: {err_msg}", [], None, None, None, None, ""

    service = get_calendar_service()
    if not service: return False, "服务端配置错误 (No Creds)", [], None, None, None, None, ""

    # 路由
    cat = event_data.get('category', 'Kimi')
    tid = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    if cat == 'Kiki': tid = os.getenv("GOOGLE_CALENDAR_ID_KIKI") or tid
    elif cat == 'Jason': tid = os.getenv("GOOGLE_CALENDAR_ID_JASON") or tid
    elif cat == 'Janet': tid = os.getenv("GOOGLE_CALENDAR_ID_JANET") or tid
    elif cat == 'Family': tid = os.getenv("GOOGLE_CALENDAR_ID_FAMILY") or tid

    try:
        # 2. 时区处理
        raw_start_tz = event_data.get('start_timezone', event_data.get('event_timezone'))
        final_start_tz, start_tz_obj, fb_start = resolve_timezone(raw_start_tz, user_current_tz)
        
        raw_end_tz = event_data.get('end_timezone', raw_start_tz)
        final_end_tz, end_tz_obj, fb_end = resolve_timezone(raw_end_tz, user_current_tz)
        
        # P1-3: 人性化 Fallback 提示
        fb_msg = ""
        if fb_start or fb_end:
            fb_msg = f"\n⚠️ 我没完全看懂 AI 给的时区，已按照你当前所在时区 {user_current_tz} 安排。"

        # 3. Start Time 解析与修正
        dt_start_naive = datetime.strptime(event_data['start_time'], '%Y-%m-%d %H:%M:%S')
        dt_start_aware, dt_start_naive = smart_fix_year(dt_start_naive, start_tz_obj)

        # 4. End Time 解析与 P0-1 核心修复
        if event_data.get('end_time'):
            dt_end_naive_raw = datetime.strptime(event_data['end_time'], '%Y-%m-%d %H:%M:%S')
            dt_end_aware = smart_fix_end_time(dt_start_aware, dt_end_naive_raw, end_tz_obj)
        else:
            dt_end_aware = dt_start_aware + timedelta(hours=1)
            final_end_tz = final_start_tz

        # 5. API Calls
        confs = await asyncio.to_thread(_sync_check_conflicts, service, tid, dt_start_aware, dt_end_aware)
        
        body = {
            'summary': event_data.get('summary', 'New Event'),
            'description': f"{event_data.get('description', '')}\n\n[Created by FamilyBot]",
            'location': event_data.get('location', ''),
            'start': {'dateTime': dt_start_naive.isoformat(), 'timeZone': final_start_tz},
            'end': {'dateTime': dt_end_aware.strftime('%Y-%m-%dT%H:%M:%S'), 'timeZone': final_end_tz},
        }
        if (rec := normalize_recurrence(event_data.get('recurrence'))): body['recurrence'] = rec

        evt = await asyncio.to_thread(_sync_insert_event, service, tid, body)
        return True, evt.get('htmlLink'), confs, dt_start_aware, dt_end_aware, tid, evt['id'], fb_msg

    except Exception as e:
        logger.error(f"Create Error: {e}")
        return False, str(e), [], None, None, None, None, ""

async def delete_event_wrapper(calendar_id, event_id):
    service = get_calendar_service()
    if not service: return False, "No Creds"
    try:
        await asyncio.to_thread(_sync_delete_event, service, calendar_id, event_id)
        return True, "已删除"
    except Exception as e: return False, str(e)

# --- 6. Prompt Engineering (v2.3 Upgrade) ---

def get_system_prompt(user_tz, is_explicit_event_mode=False):
    now = datetime.now(pytz.timezone(user_tz)).strftime("%Y-%m-%d %H:%M:%S")
    
    # P1-4: 自然对话指示
    chat_instruction = ""
    if not is_explicit_event_mode:
        chat_instruction = "If the input is clearly NOT an event (e.g. casual chat, greetings), reply naturally in plain text. DO NOT output JSON."
    else:
        chat_instruction = "User explicitly requested an event (/event). You MUST try to parse it as an event, even if ambiguous. Return is_event=true."

    return f"""
    Current User Context: {now} (Timezone: {user_tz}).
    
    【Task】
    Parse request into Google Calendar Event JSON.
    {chat_instruction}
    
    【RULE 1: Family Categories】
    Classify based on WHO: Kimi (Default), Jason (Son), Kiki (Daughter), Janet (Wife), Family.

    【RULE 2: Timezone & Location】
    - Flights: Extract `start_timezone` (Departure) and `end_timezone` (Arrival).
    - Map cities to **Canonical IANA Timezone** (e.g. "Osaka"->"Asia/Tokyo").
    - Ambiguous? Use "UserContext".

    【RULE 3: Date Logic】
    - Missing year? Assume UPCOMING relative to Now ({now}).
    - Validate Weekday.

    【Output JSON】
    {{
        "is_event": true,
        "category": "Kimi" | "Kiki" | "Jason" | "Janet" | "Family",
        "summary": "Title",
        "start_time": "YYYY-MM-DD HH:MM:SS",
        "start_timezone": "IANA_TZ",
        "end_time": "YYYY-MM-DD HH:MM:SS",
        "end_timezone": "IANA_TZ",
        "location": "...",
        "description": "...",
        "recurrence": []
    }}
    """

# --- 7. Handlers ---

def get_chinese_weekday(dt): return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]

# [P2-1] /today Handler
async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    user_tz = get_user_timezone(update.effective_user.id)
    tz_obj = pytz.timezone(user_tz)
    
    # 计算今天 00:00 - 23:59
    now = datetime.now(tz_obj)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    
    service = get_calendar_service()
    if not service: return await update.message.reply_text("❌ Service unavailable.")

    status_msg = await update.message.reply_text("🔍 查询中...")
    
    # 暂时只查 primary，如果要查全家，需要循环查询所有 Calendar ID
    # 这里为了演示简单，只查当前用户的主日历 (Kimi)
    # 若要增强，可以将家庭日历ID都查一遍并合并
    tid = os.getenv("GOOGLE_CALENDAR_ID", "primary") 
    
    try:
        events = await asyncio.to_thread(_sync_list_events, service, tid, start_of_day.isoformat(), end_of_day.isoformat())
        
        if not events:
            return await status_msg.edit_text(f"📅 今天 ({now.strftime('%Y-%m-%d')}) 暂无日程。")
            
        text = f"📅 **今日日程** ({now.strftime('%Y-%m-%d')})\n"
        for i, e in enumerate(events, 1):
            start = e['start'].get('dateTime', e['start'].get('date'))
            summary = e.get('summary', '无标题')
            
            # 简单格式化时间 (截取 HH:MM)
            # 注意：这里收到的 start 可能是 UTC ISO，UI 显示最好转回 user_tz，略微复杂，这里做简化处理
            time_str = "全天"
            if 'T' in start:
                dt = datetime.fromisoformat(start)
                dt_local = dt.astimezone(tz_obj)
                time_str = dt_local.strftime('%H:%M')
            
            text += f"{i}. {time_str} {summary}\n"
            
        await status_msg.edit_text(text, parse_mode='Markdown')
        
    except Exception as e:
        await status_msg.edit_text(f"❌ 查询失败: {str(e)}")

# [P1-1] /start Handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    msg = (
        "🤖 **Calendar Bot v2.3 (Executive)**\n\n"
        "我是你的 AI 日程秘书。你可以：\n"
        "1. **说话**: \"明天晚上8点和 Jason 踢球\"\n"
        "2. **发图**: 发送机票或活动海报截图\n"
        "3. **指令**: `/event` 强制建日程, `/today` 看今天\n\n"
        "🌍 **时区**: `/travel London` / `/home`\n"
        "🛠 **状态**: `/status`"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# [P1-1] /status Handler
async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    user_id = update.effective_user.id
    tz_str = get_user_timezone(user_id)
    
    # Local time
    now = datetime.now(pytz.timezone(tz_str)).strftime('%Y-%m-%d %H:%M')
    
    # Creds status
    creds_ok = "✅ OK" if os.getenv("GOOGLE_CREDENTIALS_JSON") else "❌ Missing"
    
    # Last event
    last_evt = get_last_event_summary(user_id)
    last_info = f"{last_evt[0]} ({last_evt[1]})" if last_evt else "无"
    
    msg = (
        f"📊 **System Status**\n\n"
        f"🌍 时区: `{tz_str}`\n"
        f"🕰 时间: `{now}`\n"
        f"🔑 Creds: {creds_ok}\n"
        f"📝 最近: {last_info}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def travel_handler(update, context):
    if not await check_auth(update): return
    if not context.args: return await update.message.reply_text("❌ Usage: /travel London")
    tz = context.args[0]
    alias = {"London": "Europe/London", "Tokyo": "Asia/Tokyo", "HK": "Asia/Hong_Kong", "CN": "Asia/Shanghai", "SG": "Asia/Singapore"}
    final = alias.get(tz, tz)
    try: pytz.timezone(final); set_user_timezone(update.effective_user.id, final); await update.message.reply_text(f"✈️ Switched: `{final}`")
    except: await update.message.reply_text("❌ Invalid Timezone")

async def home_handler(update, context):
    if not await check_auth(update): return
    set_user_timezone(update.effective_user.id, DEFAULT_HOME_TZ)
    await update.message.reply_text(f"🏠 Home: `{DEFAULT_HOME_TZ}`")

async def button_handler(update, context):
    q = update.callback_query
    await q.answer()
    if not await check_auth(update): return
    if q.data.startswith("undo:"):
        try:
            rid = int(q.data.split(":")[1])
            info = get_event_from_history(rid)
            if not info: return await q.edit_message_text("❌ 记录已过期")
            succ, msg = await delete_event_wrapper(info[0], info[1])
            if succ: await q.edit_message_text(f"🗑️ **已撤回**\n~~{info[2]}~~", parse_mode='Markdown')
            else: await q.edit_message_text(f"❌ 失败: {msg}")
        except: await q.edit_message_text("❌ Error")

# 通用消息处理 (含 /event 逻辑)
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if update.update_id in processed_ids: return
    processed_ids.append(update.update_id)

    user_tz = get_user_timezone(update.effective_user.id)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    text_content = update.message.text
    
    # [P2-2] /event 显式命令处理
    is_explicit_event = False
    if text_content and text_content.startswith("/event"):
        is_explicit_event = True
        text_content = text_content.replace("/event", "", 1).strip()
        if not text_content:
            return await update.message.reply_text("❌ 请在 /event 后输入内容")

    sys_prompt = get_system_prompt(user_tz, is_explicit_event_mode=is_explicit_event)
    model_used = "DeepSeek V3"

    try:
        # LLM Call
        if update.message.photo:
            model_used = "Kimi Vision"
            f = await update.message.photo[-1].get_file()
            buf = BytesIO()
            await f.download_to_memory(out=buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            resp = await kimi_client.chat.completions.create(model=VISION_MODEL, messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": [{"type": "text", "text": "Analyze event."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}], max_tokens=1000)
        else:
            resp = await deepseek_client.chat.completions.create(model=TEXT_MODEL, messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": text_content}], temperature=0.3)

        msg_type, res = await parse_llm_response(resp)
        
        # [P1-4] 自然对话处理
        if msg_type == "TEXT": 
            # 如果是 /event 强制模式但 LLM 返回了 TEXT，说明真的解析不了，给个提示
            if is_explicit_event:
                return await update.message.reply_text(f"⚠️ 无法识别为日程：\n{res}\n🧠 {model_used}")
            return await update.message.reply_text(f"{res}\n\n🧠 {model_used}")

        tmp = await update.message.reply_text("🗓 处理中...")
        succ, link, confs, dts, dte, cid, eid, fb = await create_calendar_event(res, user_tz)

        if succ:
            # [P1-2] UI 优化
            stz_disp = get_timezone_display_name(str(dts.tzinfo))
            etz_disp = get_timezone_display_name(str(dte.tzinfo))
            
            if str(dts.tzinfo) == str(dte.tzinfo):
                tm_str = f"{dts.strftime('%H:%M')} - {dte.strftime('%H:%M')} ({stz_disp})"
            else:
                tm_str = f"{dts.strftime('%H:%M')} ({stz_disp}) - {dte.strftime('%H:%M')} ({etz_disp})"
            
            if str(dts.tzinfo) != user_tz or str(dte.tzinfo) != user_tz:
                loc_s = dts.astimezone(pytz.timezone(user_tz))
                loc_e = dte.astimezone(pytz.timezone(user_tz))
                tm_str += f"\n🕒 **我的时间**: {loc_s.strftime('%H:%M')} - {loc_e.strftime('%H:%M')}"

            rid = save_event_history(update.effective_user.id, cid, eid, res.get('summary'))
            icon = {'Kimi': '👱‍♂️', 'Janet': '👩‍🎨', 'Jason': '👦', 'Kiki': '👧', 'Family': '🏠'}.get(res.get('category'), '📅')
            warn = ("\n⚠️ **冲突**: " + "; ".join([c.replace("• ", "") for c in confs])) if confs else ""
            
            txt = (f"✅ 日程已同步\n\n{icon} **{res.get('summary')}**\n📅 {dts.strftime('%Y-%m-%d')} ({get_chinese_weekday(dts)})\n🕒 {tm_str}\n" + (f"📍 {res['location']}\n" if res.get('location') else "") + f"{warn}{fb}\n🔗 [查看日历]({link})\n\n🧠 {model_used}")
            await tmp.edit_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ 撤回", callback_data=f"undo:{rid}")]]))
        else: 
            await tmp.edit_text(f"⚠️ 失败: {link}\n🧠 {model_used}")

    except Exception as e:
        logger.error(f"Main Err: {e}")
        await update.message.reply_text("❌ Error")

if __name__ == '__main__':
    init_db()
    if tk := os.getenv("TELEGRAM_TOKEN"):
        app = ApplicationBuilder().token(tk).build()
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("status", status_handler))
        app.add_handler(CommandHandler("travel", travel_handler))
        app.add_handler(CommandHandler("home", home_handler))
        app.add_handler(CommandHandler("today", today_handler)) # P2-1
        app.add_handler(CommandHandler("event", process_message)) # P2-2 via MessageHandler logic
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_message))
        print("✅ Calendar Bot v2.3 (Robust) Started...")
        app.run_polling()