"""Entry point: configure logging, build the bot, run long polling."""

import asyncio
import contextlib
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_settings
from database import DB_PATH, init_db
from handlers import router as root_router
from health_server import run_health_server
from reminders import setup_reminders, shutdown_scheduler


def setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


async def main() -> None:
    setup_logging("INFO")
    health_task = asyncio.create_task(run_health_server(), name="health-server")
    await asyncio.sleep(0)

    settings = get_settings()
    setup_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(root_router)

    async def on_startup(bot: Bot) -> None:
        await init_db()
        logging.getLogger(__name__).info("Database initialized at %s", DB_PATH)
        await setup_reminders(bot, settings)

    async def on_shutdown() -> None:
        shutdown_scheduler()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logging.getLogger(__name__).info("Starting bot (long polling)")
    try:
        await dp.start_polling(bot)
    finally:
        health_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await health_task
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
