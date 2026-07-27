"""Entry point: configure logging, build the bot, run long polling."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_settings
from database import DB_PATH, init_db
from handlers import router as root_router


def setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(root_router)

    async def on_startup() -> None:
        await init_db()
        logging.getLogger(__name__).info("Database initialized at %s", DB_PATH)

    dp.startup.register(on_startup)

    logging.getLogger(__name__).info("Starting bot (long polling)")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
