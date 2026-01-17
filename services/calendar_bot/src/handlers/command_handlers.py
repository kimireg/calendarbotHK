"""
Telegram 命令处理器
"""
import asyncio
import logging
from datetime import datetime, timedelta

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from .auth import check_auth
from ..core.timezone_utils import get_chinese_weekday

logger = logging.getLogger(__name__)


class CommandHandlers:
    """命令处理器"""

    def __init__(self, config, db, google_calendar, zeabur_client):
        """
        初始化处理器

        Args:
            config: 配置对象
            db: 数据库仓库
            google_calendar: Google Calendar 客户端
            zeabur_client: Zeabur 客户端
        """
        self.config = config
        self.db = db
        self.google_calendar = google_calendar
        self.zeabur_client = zeabur_client
        self.family_members = config.get_family_members()

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        default_name = self.family_members[0]['name']
        msg = (
            f"🤖 **Calendar Bot v3.0 (Refactored)**\n"
            f"Serving: {default_name} & Family\n\n"
            "1. **日程**: \"明天下午3点开会\"\n"
            "2. **任务**: \"记得买牛奶\" (自动设为全天)\n"
            "3. **发图**: 识别海报/机票\n"
            "4. **控制**: `/restartsingboxupdater`\n"
            "5. **指令**: `/today`, `/event`, `/travel`, `/status`"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        user_id = update.effective_user.id
        tz_str = self.db.get_user_timezone(user_id)
        now = datetime.now(pytz.timezone(tz_str)).strftime('%Y-%m-%d %H:%M')

        creds_ok = "✅ OK" if self.config.google_credentials_json else "❌ Missing"
        last_evt = self.db.get_last_event_summary(user_id)
        last_info = f"{last_evt[0]} ({last_evt[1]})" if last_evt else "无"

        members_str = ", ".join([m['name'] for m in self.family_members])

        msg = (
            f"📊 **System Status (v3.0)**\n\n"
            f"🌍 时区: `{tz_str}`\n"
            f"🕰 时间: `{now}`\n"
            f"👪 成员: `{members_str}`\n"
            f"🔑 Creds: {creds_ok}\n"
            f"📝 最近: {last_info}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def today_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /today 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        user_tz = self.db.get_user_timezone(update.effective_user.id)
        tz_obj = pytz.timezone(user_tz)
        now = datetime.now(tz_obj)

        status_msg = await update.message.reply_text("🔍 查询中...")

        try:
            # 使用主日历
            calendar_id = self.config.google_calendar_id or "primary"
            events = await self.google_calendar.list_today_events(calendar_id, user_tz)

            if not events:
                await status_msg.edit_text(f"📅 今天 ({now.strftime('%Y-%m-%d')}) 暂无日程。")
                return

            text = f"📅 **今日日程** ({now.strftime('%Y-%m-%d')})\n"
            for i, event in enumerate(events, 1):
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', '无标题')

                time_str = "全天"
                if 'T' in start:
                    dt = datetime.fromisoformat(start)
                    dt_local = dt.astimezone(tz_obj)
                    time_str = dt_local.strftime('%H:%M')

                text += f"{i}. {time_str} {summary}\n"

            await status_msg.edit_text(text, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"❌ Today handler error: {e}")
            await status_msg.edit_text(f"❌ 查询失败: {str(e)}")

    async def travel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /travel 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /travel London")
            return

        tz = context.args[0]

        # 时区别名
        alias = {
            "London": "Europe/London",
            "Tokyo": "Asia/Tokyo",
            "HK": "Asia/Hong_Kong",
            "CN": "Asia/Shanghai",
            "SG": "Asia/Singapore"
        }

        final_tz = alias.get(tz, tz)

        try:
            pytz.timezone(final_tz)
            self.db.set_user_timezone(update.effective_user.id, final_tz)
            await update.message.reply_text(f"✈️ Switched: `{final_tz}`", parse_mode='Markdown')
        except pytz.UnknownTimeZoneError:
            await update.message.reply_text("❌ Invalid Timezone")

    async def home_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /home 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        self.db.set_user_timezone(update.effective_user.id, self.config.default_timezone)
        await update.message.reply_text(
            f"🏠 Home: `{self.config.default_timezone}`",
            parse_mode='Markdown'
        )

    async def restart_singbox_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /restartsingboxupdater 命令"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        if not self.zeabur_client or not self.zeabur_client.api_token:
            await update.message.reply_text("❌ Zeabur 未配置")
            return

        status_msg = await update.message.reply_text("🔄 正在请求 Zeabur 重启 Singbox Updater...")

        try:
            success, msg = await asyncio.to_thread(self.zeabur_client.restart_singbox)

            if success:
                await status_msg.edit_text(f"{msg}\n⏳ 请等待 1-2 分钟让服务重新上线。")
            else:
                await status_msg.edit_text(f"⚠️ 操作失败: {msg}")

        except Exception as e:
            logger.error(f"❌ Restart singbox error: {e}")
            await status_msg.edit_text(f"❌ 操作失败: {str(e)}")
