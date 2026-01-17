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

# --- [新增] Zeabur 远程控制模块 ---
import zeabur_remote

# --- 1. 配置与初始化 (Configuration) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- AI Client (OpenRouter Unified) ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

if not OPENROUTER_API_KEY:
    logger.error("❌ Missing OPENROUTER_API_KEY")

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    timeout=60.0,
)

MODEL_NAME = "google/gemini-3-flash-preview"
DEFAULT_HOME_TZ = "Asia/Singapore"
DB_PATH = "data/calendar_bot_v2.db"

# 权限与幂等性
allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
processed_ids = deque(maxlen=200)

VALID_CATEGORIES = {"Kimi", "Kiki", "Jason", "Janet", "Family"}

# --- 2. 数据库层 (保持不变) ---
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
    
    if data and isinstance(data, dict) and data.get('is_event'):
        return "EVENT", data
    return "TEXT", content

# v2.6 更新: 支持全天事件的日期格式校验
def validate_and_fix_payload(data: dict) -> Tuple[bool, str]:
    if not data.get('summary'): return False, "缺少事件标题 (summary)"
    if not data.get('start_time'): return False, "缺少开始时间 (start_time)"
    
    cat = data.get('category')
    if cat not in VALID_CATEGORIES:
        logger.warning(f"⚠️ Unknown category '{cat}', fallback to 'Kimi'")
        data['category'] = 'Kimi' 
    
    is_all_day = data.get('is_all_day', False)

    try:
        if is_all_day:
            # 全天事件只校验 YYYY-MM-DD
            datetime.strptime(data['start_time'], '%Y-%m-%d')
            # 全天事件通常不需要 end_time，如果有也只校验日期
            if data.get('end_time'):
                datetime.strptime(data['end_time'], '%Y-%m-%d')
        else:
            # 普通事件校验完整时间
            datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
            if data.get('end_time'):
                datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        fmt = "YYYY-MM-DD" if is_all_day else "YYYY-MM-DD HH:MM:SS"
        return False, f"时间格式错误，需为 {fmt}"
        
    return True, "OK"

def get_timezone_display_name(tz_str: str) -> str:
    mapping = {
        "Asia/Singapore": "新加坡", "Asia/Shanghai": "上海", "Asia/Tokyo": "东京", "Asia/Hong_Kong": "香港",
        "Europe/London": "伦敦", "America/New_York": "纽约", "America/Los_Angeles": "洛杉矶"
    }
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
    now = datetime.now(tz_obj)
    dt_aware = tz_obj.localize(dt_naive)
    while dt_aware < now - timedelta(days=90):
        try:
            dt_naive = dt_naive.replace(year=dt_naive.year + 1)
            dt_aware = tz_obj.localize(dt_naive)
            logger.info(f"StartYear Fix: {dt_naive.year}")
        except ValueError: break
    return dt_aware, dt_naive

def smart_fix_end_time(dt_start_aware, dt_end_naive_raw, end_tz_obj):
    current_year = dt_start_aware.year
    try: dt_end_naive = dt_end_naive_raw.replace(year=current_year)
    except ValueError: dt_end_naive = dt_end_naive_raw.replace(year=current_year, day=28) 
    dt_end_aware = end_tz_obj.localize(dt_end_naive)
    if dt_end_aware < dt_start_aware:
        dt_end_naive_plus_day = dt_end_naive + timedelta(days=1)
        dt_end_aware_plus_day = end_tz_obj.localize(dt_end_naive_plus_day)
        if dt_end_aware_plus_day >= dt_start_aware: return dt_end_aware_plus_day
        try:
            dt_end_naive_plus_year = dt_end_naive.replace(year=current_year + 1)
            return end_tz_obj.localize(dt_end_naive_plus_year)
        except: return dt_end_aware_plus_day
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

def _sync_check_conflicts(service, cal_id, start_dt, end_dt):
    # 全天事件暂不检测具体冲突，或者简化检测
    try:
        # 如果是 datetime 对象，转 isoformat
        t_min = start_dt.isoformat()
        t_max = end_dt.isoformat()
        items = service.events().list(
            calendarId=cal_id, timeMin=t_min, timeMax=t_max, 
            singleEvents=True, orderBy='startTime'
        ).execute().get('items', [])
        return [f"• {e.get('summary', '未知')}" for e in items if 'dateTime' in e['start']]
    except: return []

def _sync_insert_event(service, cal_id, body):
    return service.events().insert(calendarId=cal_id, body=body).execute()

def _sync_delete_event(service, cal_id, eid):
    service.events().delete(calendarId=cal_id, eventId=eid).execute()

def _sync_list_events(service, cal_id, start_iso, end_iso):
    return service.events().list(
        calendarId=cal_id, timeMin=start_iso, timeMax=end_iso, 
        singleEvents=True, orderBy='startTime'
    ).execute().get('items', [])

async def create_calendar_event(event_data, user_current_tz):
    is_valid, err_msg = validate_and_fix_payload(event_data)
    if not is_valid: return False, f"数据校验失败: {err_msg}", [], None, None, None, None, ""

    service = get_calendar_service()
    if not service: return False, "服务端配置错误 (No Creds)", [], None, None, None, None, ""

    cat = event_data.get('category', 'Kimi')
    tid = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    if cat == 'Kiki': tid = os.getenv("GOOGLE_CALENDAR_ID_KIKI") or tid
    elif cat == 'Jason': tid = os.getenv("GOOGLE_CALENDAR_ID_JASON") or tid
    elif cat == 'Janet': tid = os.getenv("GOOGLE_CALENDAR_ID_JANET") or tid
    elif cat == 'Family': tid = os.getenv("GOOGLE_CALENDAR_ID_FAMILY") or tid

    try:
        # v2.6 新增: 全天事件/任务 处理逻辑
        is_all_day = event_data.get('is_all_day', False)
        
        body = {
            'summary': event_data.get('summary', 'New Event'),
            'description': f"{event_data.get('description', '')}\n\n[Created by CalendarBot]",
            'location': event_data.get('location', ''),
        }

        # 变量初始化，用于 UI 显示
        dt_start_display = None 
        dt_end_display = None
        fb_msg = ""
        confs = []

        if is_all_day:
            # --- 任务/全天事件模式 ---
            # 格式: YYYY-MM-DD
            start_date_str = event_data['start_time']
            # Google 全天事件结束时间必须是 start + 1 day (exclusive)
            dt_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            dt_end_date = dt_start_date + timedelta(days=1)
            end_date_str = dt_end_date.strftime('%Y-%m-%d')
            
            body['start'] = {'date': start_date_str}
            body['end'] = {'date': end_date_str}
            body['colorId'] = '11' # 🔴 红色，标识为 Task/Important

            dt_start_display = dt_start_date # 用于 UI 显示
            dt_end_display = dt_end_date
            
            # 全天事件不进行严格冲突检测，或不做提示
            
        else:
            # --- 普通日程模式 (v2.5 逻辑) ---
            raw_start_tz = event_data.get('start_timezone', event_data.get('event_timezone'))
            final_start_tz, start_tz_obj, fb_start = resolve_timezone(raw_start_tz, user_current_tz)
            raw_end_tz = event_data.get('end_timezone', raw_start_tz)
            final_end_tz, end_tz_obj, fb_end = resolve_timezone(raw_end_tz, user_current_tz)
            
            if fb_start or fb_end: fb_msg = f"\n⚠️ AI未识别时区，已按 {user_current_tz} 安排。"

            dt_start_naive = datetime.strptime(event_data['start_time'], '%Y-%m-%d %H:%M:%S')
            dt_start_aware, dt_start_naive = smart_fix_year(dt_start_naive, start_tz_obj)

            if event_data.get('end_time'):
                dt_end_naive_raw = datetime.strptime(event_data['end_time'], '%Y-%m-%d %H:%M:%S')
                dt_end_aware = smart_fix_end_time(dt_start_aware, dt_end_naive_raw, end_tz_obj)
            else:
                dt_end_aware = dt_start_aware + timedelta(hours=1)
                final_end_tz = final_start_tz
            
            confs = await asyncio.to_thread(_sync_check_conflicts, service, tid, dt_start_aware, dt_end_aware)

            body['start'] = {'dateTime': dt_start_naive.isoformat(), 'timeZone': final_start_tz}
            body['end'] = {'dateTime': dt_end_aware.strftime('%Y-%m-%dT%H:%M:%S'), 'timeZone': final_end_tz}
            
            dt_start_display = dt_start_aware
            dt_end_display = dt_end_aware

        if (rec := normalize_recurrence(event_data.get('recurrence'))): body['recurrence'] = rec

        evt = await asyncio.to_thread(_sync_insert_event, service, tid, body)
        return True, evt.get('htmlLink'), confs, dt_start_display, dt_end_display, tid, evt['id'], fb_msg, is_all_day

    except Exception as e:
        logger.error(f"Create Error: {e}")
        return False, str(e), [], None, None, None, None, "", False

async def delete_event_wrapper(calendar_id, event_id):
    service = get_calendar_service()
    if not service: return False, "No Creds"
    try:
        await asyncio.to_thread(_sync_delete_event, service, calendar_id, event_id)
        return True, "已删除"
    except Exception as e: return False, str(e)

# --- 6. Prompt Engineering (v2.6 Updated) ---
def get_system_prompt(user_tz, is_explicit_event_mode=False):
    now = datetime.now(pytz.timezone(user_tz)).strftime("%Y-%m-%d %H:%M:%S")
    
    chat_instruction = ""
    if not is_explicit_event_mode:
        chat_instruction = "If input is clearly NOT an event/task (e.g. casual chat), reply naturally in plain text. DO NOT output JSON."
    else:
        chat_instruction = "User explicitly requested an event. You MUST return JSON."

    return f"""
    Current User Context: {now} (Timezone: {user_tz}).
    
    【Task】Parse request into Google Calendar Event JSON.
    {chat_instruction}
    
    【RULE 1: Family Categories】
    Classify based on WHO: Kimi (Default), Jason (Son), Kiki (Daughter), Janet (Wife), Family.

    【RULE 2: Tasks vs Events】
    - **Normal Event**: Specific time (e.g. "Meeting at 3pm"). 
      -> Set "is_all_day": false, "start_time": "YYYY-MM-DD HH:MM:SS".
    - **Task/Todo**: No specific time (e.g. "Buy milk", "Call Mom today", "Jason's Football match").
      -> Set "is_all_day": true.
      -> Set "start_time": "YYYY-MM-DD" (Date ONLY, no time).
      -> No need for timezones or end_time.

    【RULE 3: Date Logic】
    - Missing year? Assume UPCOMING relative to Now ({now}).
    - Validate Weekday.

    【Output JSON】
    {{
        "is_event": true,
        "is_all_day": boolean, 
        "category": "Kimi"|...,
        "summary": "Title",
        "start_time": "YYYY-MM-DD HH:MM:SS" OR "YYYY-MM-DD",
        "start_timezone": "IANA_TZ" (Optional if all_day),
        "end_time": "...",
        "end_timezone": "...",
        "location": "...",
        "description": "...",
        "recurrence": []
    }}
    """

# --- 7. Handlers ---
def get_chinese_weekday(dt): return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    user_tz = get_user_timezone(update.effective_user.id)
    tz_obj = pytz.timezone(user_tz)
    now = datetime.now(tz_obj)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    
    service = get_calendar_service()
    if not service: return await update.message.reply_text("❌ Service unavailable.")
    status_msg = await update.message.reply_text("🔍 查询中...")
    tid = os.getenv("GOOGLE_CALENDAR_ID", "primary") 
    
    try:
        events = await asyncio.to_thread(_sync_list_events, service, tid, start_of_day.isoformat(), end_of_day.isoformat())
        if not events: return await status_msg.edit_text(f"📅 今天 ({now.strftime('%Y-%m-%d')}) 暂无日程。")
        text = f"📅 **今日日程** ({now.strftime('%Y-%m-%d')})\n"
        for i, e in enumerate(events, 1):
            start = e['start'].get('dateTime', e['start'].get('date'))
            summary = e.get('summary', '无标题')
            time_str = "全天" # 默认全天
            if 'T' in start:
                dt = datetime.fromisoformat(start)
                dt_local = dt.astimezone(tz_obj)
                time_str = dt_local.strftime('%H:%M')
            text += f"{i}. {time_str} {summary}\n"
        await status_msg.edit_text(text, parse_mode='Markdown')
    except Exception as e: await status_msg.edit_text(f"❌ 查询失败: {str(e)}")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    msg = (
        "🤖 **Calendar Bot v2.7 (Zeabur Control)**\n\n"
        "我是你的 AI 日程秘书。你可以：\n"
        "1. **日程**: \"明天下午3点开会\"\n"
        "2. **任务**: \"记得买牛奶\" (自动设为全天)\n"
        "3. **发图**: 识别海报/机票\n"
        "4. **控制**: `/restartsingboxupdater` (重启服务)\n"
        "5. **指令**: `/today`, `/event`, `/travel`, `/status`"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    user_id = update.effective_user.id
    tz_str = get_user_timezone(user_id)
    now = datetime.now(pytz.timezone(tz_str)).strftime('%Y-%m-%d %H:%M')
    creds_ok = "✅ OK" if os.getenv("GOOGLE_CREDENTIALS_JSON") else "❌ Missing"
    last_evt = get_last_event_summary(user_id)
    last_info = f"{last_evt[0]} ({last_evt[1]})" if last_evt else "无"
    
    msg = (
        f"📊 **System Status (v2.7)**\n\n"
        f"🌍 时区: `{tz_str}`\n"
        f"🕰 时间: `{now}`\n"
        f"🔑 Creds: {creds_ok}\n"
        f"🧠 Model: `{MODEL_NAME}`\n"
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

# --- [新增] Zeabur Restart Handler ---
async def restart_singbox_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler: /restartsingboxupdater
    远程重启 Zeabur 上的 Singbox 服务
    """
    if not await check_auth(update): return

    status_msg = await update.message.reply_text("🔄 正在请求 Zeabur 重启 Singbox Updater...")
    
    # 异步调用同步的 requests 模块，避免阻塞
    success, msg = await asyncio.to_thread(zeabur_remote.restart_singbox)

    if success:
        await status_msg.edit_text(f"{msg}\n⏳ 请等待 1-2 分钟让服务重新上线。")
    else:
        await status_msg.edit_text(f"⚠️ 操作失败: {msg}")

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    if update.update_id in processed_ids: return
    processed_ids.append(update.update_id)

    user_tz = get_user_timezone(update.effective_user.id)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    text_content = update.message.caption if update.message.caption else update.message.text
    text_content = text_content or "" 

    is_explicit_event = False
    if text_content and text_content.startswith("/event"):
        is_explicit_event = True
        text_content = text_content.replace("/event", "", 1).strip()

    sys_prompt = get_system_prompt(user_tz, is_explicit_event_mode=is_explicit_event)
    
    try:
        if update.message.photo:
            f = await update.message.photo[-1].get_file()
            buf = BytesIO()
            await f.download_to_memory(out=buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            user_prompt = text_content if text_content.strip() else "Extract event details from this image."
            logger.info(f"Processing Image with Caption: {user_prompt}")

            resp = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt}, 
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}
                ],
                max_tokens=1000,
                extra_headers={"HTTP-Referer": "https://telegram.org", "X-Title": "Calendar Bot"}
            )
        
        else:
            if not text_content: return 
            
            resp = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_prompt}, 
                    {"role": "user", "content": text_content}
                ],
                temperature=0.3,
                extra_headers={"HTTP-Referer": "https://telegram.org", "X-Title": "Calendar Bot"}
            )

        msg_type, res = await parse_llm_response(resp)
        if msg_type == "TEXT": 
            if is_explicit_event: return await update.message.reply_text(f"⚠️ 无法识别：\n{res}")
            return await update.message.reply_text(f"{res}")

        tmp = await update.message.reply_text("🗓 ...")
        succ, link, confs, dts, dte, cid, eid, fb, is_all_day = await create_calendar_event(res, user_tz)

        if succ:
            if is_all_day:
                date_str = dts.strftime('%Y-%m-%d')
                weekday = get_chinese_weekday(dts)
                tm_str = "📝 全天待办 / 任务"
                icon = "✅"
            else:
                stz_disp = get_timezone_display_name(str(dts.tzinfo))
                etz_disp = get_timezone_display_name(str(dte.tzinfo))
                if str(dts.tzinfo) == str(dte.tzinfo): tm_str = f"{dts.strftime('%H:%M')} - {dte.strftime('%H:%M')} ({stz_disp})"
                else: tm_str = f"{dts.strftime('%H:%M')} ({stz_disp}) - {dte.strftime('%H:%M')} ({etz_disp})"
                
                if str(dts.tzinfo) != user_tz or str(dte.tzinfo) != user_tz:
                    loc_s = dts.astimezone(pytz.timezone(user_tz))
                    loc_e = dte.astimezone(pytz.timezone(user_tz))
                    tm_str += f"\n🕒 **我的时间**: {loc_s.strftime('%H:%M')} - {loc_e.strftime('%H:%M')}"
                
                date_str = dts.strftime('%Y-%m-%d')
                weekday = get_chinese_weekday(dts)
                icon = {'Kimi': '👱‍♂️', 'Janet': '👩‍🎨', 'Jason': '👦', 'Kiki': '👧', 'Family': '🏠'}.get(res.get('category'), '📅')

            rid = save_event_history(update.effective_user.id, cid, eid, res.get('summary'))
            warn = ("\n⚠️ **冲突**: " + "; ".join([c.replace("• ", "") for c in confs])) if confs else ""
            
            txt = (f"✅ 已添加\n\n{icon} **{res.get('summary')}**\n📅 {date_str} ({weekday})\n🕒 {tm_str}\n" + (f"📍 {res['location']}\n" if res.get('location') else "") + f"{warn}{fb}\n🔗 [查看日历]({link})\n\n🧠 {MODEL_NAME}")
            await tmp.edit_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ 撤回", callback_data=f"undo:{rid}")]]))
        else: await tmp.edit_text(f"⚠️ 失败: {link}")

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
        app.add_handler(CommandHandler("today", today_handler)) 
        app.add_handler(CommandHandler("event", process_message)) 
        # [新增] 注册重启指令
        app.add_handler(CommandHandler("restartsingboxupdater", restart_singbox_handler))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_message))
        print("✅ Calendar Bot v2.7 (Task & Zeabur) Started...")
        app.run_polling()