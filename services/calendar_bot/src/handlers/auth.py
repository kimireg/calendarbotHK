"""
鉴权处理
"""
from telegram import Update


async def check_auth(update: Update, allowed_ids: list) -> bool:
    """
    检查用户是否有权限

    Args:
        update: Telegram Update 对象
        allowed_ids: 允许的用户 ID 列表

    Returns:
        是否有权限
    """
    user_id = update.effective_user.id

    if user_id not in allowed_ids:
        await update.message.reply_text(f"⛔️ 未授权 ID: {user_id}")
        return False

    return True
