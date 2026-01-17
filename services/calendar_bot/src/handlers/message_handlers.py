"""
Telegram 消息处理器
"""
import logging
from collections import deque
from io import BytesIO

import pytz
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .auth import check_auth
from ..core.timezone_utils import get_timezone_display_name, get_chinese_weekday

logger = logging.getLogger(__name__)


class MessageHandlers:
    """消息处理器"""

    def __init__(
        self,
        config,
        db,
        event_parser,
        google_calendar,
        processed_ids_queue: deque
    ):
        """
        初始化处理器

        Args:
            config: 配置对象
            db: 数据库仓库
            event_parser: 事件解析器
            google_calendar: Google Calendar 客户端
            processed_ids_queue: 已处理消息 ID 队列
        """
        self.config = config
        self.db = db
        self.event_parser = event_parser
        self.google_calendar = google_calendar
        self.processed_ids = processed_ids_queue
        self.family_members = config.get_family_members()

        # 构建辅助数据
        self.valid_categories = {m["name"] for m in self.family_members}
        self.valid_categories.add("Family")

        self.category_to_icon = {m["name"]: m.get("icon", "📅") for m in self.family_members}
        self.category_to_icon["Family"] = "🏠"

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息"""
        if not await check_auth(update, self.config.allowed_ids):
            return

        # 防止重复处理
        if update.update_id in self.processed_ids:
            return
        self.processed_ids.append(update.update_id)

        user_tz = self.db.get_user_timezone(update.effective_user.id)

        # 发送 typing 状态
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=constants.ChatAction.TYPING
        )

        # 提取内容
        text_content = update.message.caption if update.message.caption else update.message.text
        text_content = text_content or ""

        # 检查是否为显式事件请求
        is_explicit_event = False
        if text_content and text_content.startswith("/event"):
            is_explicit_event = True
            text_content = text_content.replace("/event", "", 1).strip()

        try:
            # 处理图片消息
            if update.message.photo:
                await self._handle_image_message(
                    update,
                    text_content,
                    user_tz
                )
            # 处理文本消息
            elif text_content:
                await self._handle_text_message(
                    update,
                    text_content,
                    user_tz,
                    is_explicit_event
                )

        except Exception as e:
            logger.error(f"❌ Message processing error: {e}", exc_info=True)
            await update.message.reply_text("❌ 处理失败，请稍后重试")

    async def _handle_text_message(
        self,
        update: Update,
        text: str,
        user_tz: str,
        is_explicit_event: bool
    ):
        """处理文本消息"""
        # 解析消息
        msg_type, result = await self.event_parser.parse_text_message(
            text=text,
            user_timezone=user_tz,
            family_members=self.family_members,
            is_explicit_event=is_explicit_event
        )

        # 如果是普通聊天
        if msg_type == "TEXT":
            if is_explicit_event:
                await update.message.reply_text(f"⚠️ 无法识别：\n{result}")
            else:
                await update.message.reply_text(result)
            return

        # 如果是事件，创建日历事件
        await self._create_and_send_event(update, result, user_tz)

    async def _handle_image_message(
        self,
        update: Update,
        caption: str,
        user_tz: str
    ):
        """处理图片消息"""
        # 下载图片
        file = await update.message.photo[-1].get_file()
        buffer = BytesIO()
        await file.download_to_memory(out=buffer)
        image_bytes = buffer.getvalue()

        # 解析图片
        msg_type, result = await self.event_parser.parse_image_message(
            image_bytes=image_bytes,
            caption=caption,
            user_timezone=user_tz,
            family_members=self.family_members
        )

        # 如果是普通回复
        if msg_type == "TEXT":
            await update.message.reply_text(result)
            return

        # 如果是事件，创建日历事件
        await self._create_and_send_event(update, result, user_tz)

    async def _create_and_send_event(
        self,
        update: Update,
        event_data: dict,
        user_tz: str
    ):
        """创建事件并发送结果"""
        tmp = await update.message.reply_text("🗓 ...")

        # 获取分类对应的日历 ID
        category = event_data.get('category', self.family_members[0]['name'])
        calendar_id = self.config.get_calendar_id(category)
        default_category = self.family_members[0]['name']

        # 创建事件
        (
            success,
            link,
            conflicts,
            dt_start,
            dt_end,
            cal_id,
            event_id,
            fallback_msg,
            is_all_day
        ) = await self.google_calendar.create_event(
            event_data=event_data,
            calendar_id=calendar_id,
            user_current_tz=user_tz,
            default_category=default_category
        )

        if not success:
            await tmp.edit_text(f"⚠️ 失败: {link}")
            return

        # 构建响应消息
        if is_all_day:
            date_str = dt_start.strftime('%Y-%m-%d')
            weekday = get_chinese_weekday(dt_start)
            time_str = "📝 全天待办 / 任务"
            icon = "✅"
        else:
            start_tz_display = get_timezone_display_name(str(dt_start.tzinfo))
            end_tz_display = get_timezone_display_name(str(dt_end.tzinfo))

            if str(dt_start.tzinfo) == str(dt_end.tzinfo):
                time_str = f"{dt_start.strftime('%H:%M')} - {dt_end.strftime('%H:%M')} ({start_tz_display})"
            else:
                time_str = f"{dt_start.strftime('%H:%M')} ({start_tz_display}) - {dt_end.strftime('%H:%M')} ({end_tz_display})"

            # 如果事件时区与用户时区不同，显示本地时间
            if str(dt_start.tzinfo) != user_tz or str(dt_end.tzinfo) != user_tz:
                local_start = dt_start.astimezone(pytz.timezone(user_tz))
                local_end = dt_end.astimezone(pytz.timezone(user_tz))
                time_str += f"\n🕒 **我的时间**: {local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}"

            date_str = dt_start.strftime('%Y-%m-%d')
            weekday = get_chinese_weekday(dt_start)
            icon = self.category_to_icon.get(category, '📅')

        # 保存历史
        record_id = self.db.save_event_history(
            user_id=update.effective_user.id,
            calendar_id=cal_id,
            google_event_id=event_id,
            summary=event_data.get('summary')
        )

        # 冲突警告
        warning = ""
        if conflicts:
            warning = "\n⚠️ **冲突**: " + "; ".join([c.replace("• ", "") for c in conflicts])

        # 位置信息
        location_info = ""
        if event_data.get('location'):
            location_info = f"📍 {event_data['location']}\n"

        # 完整消息
        message_text = (
            f"✅ 已添加\n\n"
            f"{icon} **{event_data.get('summary')}**\n"
            f"📅 {date_str} ({weekday})\n"
            f"🕒 {time_str}\n"
            f"{location_info}"
            f"{warning}{fallback_msg}\n"
            f"🔗 [查看日历]({link})\n\n"
            f"🧠 {self.config.llm_model_name}"
        )

        # 创建撤回按钮
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ 撤回", callback_data=f"undo:{record_id}")]
        ])

        await tmp.edit_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
