"""
Calendar Bot 主程序
"""
import logging
from collections import deque

from openai import AsyncOpenAI
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from src.config import load_config
from src.database import DatabaseRepository
from src.core import EventParser, EventValidator
from src.integrations import GoogleCalendarClient, ZeaburClient
from src.handlers import CommandHandlers, MessageHandlers, CallbackHandlers


def setup_logging(log_level: str):
    """设置日志"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level.upper(), logging.INFO)
    )


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("🤖 Calendar Bot v3.0 (Refactored) Starting...")

    # 初始化数据库
    db = DatabaseRepository(config.database_path)

    # 初始化 OpenAI 客户端
    openai_client = AsyncOpenAI(
        api_key=config.openrouter_api_key,
        base_url=config.openrouter_base_url,
        timeout=60.0
    )

    # 初始化事件解析器
    event_parser = EventParser(
        openai_client=openai_client,
        model_name=config.llm_model_name
    )

    # 初始化事件验证器
    family_members = config.get_family_members()
    valid_categories = {m["name"] for m in family_members}
    valid_categories.add("Family")
    event_validator = EventValidator(valid_categories=valid_categories)

    # 初始化 Google Calendar 客户端
    google_calendar = GoogleCalendarClient(
        credentials_json=config.google_credentials_json,
        event_validator=event_validator
    )

    # 初始化 Zeabur 客户端（可选）
    zeabur_client = None
    if config.zeabur_api_token:
        zeabur_client = ZeaburClient(
            api_token=config.zeabur_api_token,
            targets_json=config.zeabur_targets
        )
        logger.info("✅ Zeabur client initialized")

    # 初始化处理器
    command_handlers = CommandHandlers(
        config=config,
        db=db,
        google_calendar=google_calendar,
        zeabur_client=zeabur_client
    )

    processed_ids = deque(maxlen=200)  # 防止重复处理
    message_handlers = MessageHandlers(
        config=config,
        db=db,
        event_parser=event_parser,
        google_calendar=google_calendar,
        processed_ids_queue=processed_ids
    )

    callback_handlers = CallbackHandlers(
        config=config,
        db=db,
        google_calendar=google_calendar
    )

    # 创建 Telegram 应用
    app = ApplicationBuilder().token(config.telegram_token).build()

    # 注册命令处理器
    app.add_handler(CommandHandler("start", command_handlers.start_handler))
    app.add_handler(CommandHandler("status", command_handlers.status_handler))
    app.add_handler(CommandHandler("today", command_handlers.today_handler))
    app.add_handler(CommandHandler("travel", command_handlers.travel_handler))
    app.add_handler(CommandHandler("home", command_handlers.home_handler))
    app.add_handler(CommandHandler("restartsingboxupdater", command_handlers.restart_singbox_handler))

    # 注册消息处理器
    app.add_handler(CommandHandler("event", message_handlers.process_message))
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        message_handlers.process_message
    ))

    # 注册回调处理器
    app.add_handler(CallbackQueryHandler(callback_handlers.button_handler))

    # 启动 Bot
    logger.info("✅ Calendar Bot v3.0 Started Successfully!")
    logger.info(f"📊 Configured for {len(family_members)} family members")
    logger.info(f"🔑 Authorized users: {len(config.allowed_ids)}")

    app.run_polling()


if __name__ == '__main__':
    main()
