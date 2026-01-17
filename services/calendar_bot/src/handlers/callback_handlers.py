"""
Telegram 回调处理器（按钮点击）
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from .auth import check_auth

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """回调处理器"""

    def __init__(self, config, db, google_calendar):
        """
        初始化处理器

        Args:
            config: 配置对象
            db: 数据库仓库
            google_calendar: Google Calendar 客户端
        """
        self.config = config
        self.db = db
        self.google_calendar = google_calendar

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮点击"""
        query = update.callback_query
        await query.answer()

        if not await check_auth(update, self.config.allowed_ids):
            return

        # 撤回事件
        if query.data.startswith("undo:"):
            try:
                record_id = int(query.data.split(":")[1])
                event_info = self.db.get_event_from_history(record_id)

                if not event_info:
                    await query.edit_message_text("❌ 记录已过期")
                    return

                calendar_id, google_event_id, summary = event_info

                # 删除事件
                success, msg = await self.google_calendar.delete_event(
                    calendar_id,
                    google_event_id
                )

                if success:
                    await query.edit_message_text(
                        f"🗑️ **已撤回**\n~~{summary}~~",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(f"❌ 失败: {msg}")

            except Exception as e:
                logger.error(f"❌ Callback error: {e}")
                await query.edit_message_text("❌ 操作失败")
