"""Scheduled daily streak reminders."""

import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Settings
from database import get_stored_reminder_chat_id, set_reminder_chat_id_if_unset

logger = logging.getLogger(__name__)

REMINDER_TEXT = (
    "⏰ Напоминание! Не забудь отправить отчёт за сегодня командой /done "
    "или с хештегом #отчет, чтобы не потерять свой стрик!"
)

_scheduler: AsyncIOScheduler | None = None


async def send_daily_reminder(bot: Bot, chat_id: int) -> None:
    try:
        await bot.send_message(chat_id, REMINDER_TEXT)
        logger.info("Daily reminder sent to chat %s", chat_id)
    except Exception:
        logger.exception("Failed to send daily reminder to chat %s", chat_id)


def _ensure_scheduler(settings: Settings) -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        tz = ZoneInfo(settings.reminder_timezone)
        _scheduler = AsyncIOScheduler(timezone=tz)
        _scheduler.start()
        logger.info("Reminder scheduler started (timezone=%s)", settings.reminder_timezone)
    return _scheduler


def schedule_daily_reminder(bot: Bot, chat_id: int, settings: Settings) -> None:
    scheduler = _ensure_scheduler(settings)
    scheduler.add_job(
        send_daily_reminder,
        CronTrigger(
            hour=settings.reminder_hour,
            minute=settings.reminder_minute,
            timezone=ZoneInfo(settings.reminder_timezone),
        ),
        args=[bot, chat_id],
        id="daily_streak_reminder",
        replace_existing=True,
    )
    logger.info(
        "Daily reminder scheduled for chat %s at %02d:%02d %s",
        chat_id,
        settings.reminder_hour,
        settings.reminder_minute,
        settings.reminder_timezone,
    )


async def resolve_reminder_chat_id(settings: Settings) -> int | None:
    if settings.reminder_chat_id is not None:
        return settings.reminder_chat_id
    return await get_stored_reminder_chat_id()


async def setup_reminders(bot: Bot, settings: Settings) -> None:
    chat_id = await resolve_reminder_chat_id(settings)
    if chat_id is None:
        logger.warning(
            "Daily reminders disabled: set CHAT_ID in .env or run /start in a group"
        )
        return
    schedule_daily_reminder(bot, chat_id, settings)


async def register_group_for_reminders(
    bot: Bot,
    chat_id: int,
    settings: Settings,
) -> bool:
    """
    Save group chat id for reminders when not configured in .env.

    Returns True if this call registered a new chat id.
    """
    if settings.reminder_chat_id is not None:
        return False
    registered = await set_reminder_chat_id_if_unset(chat_id)
    if registered:
        schedule_daily_reminder(bot, chat_id, settings)
    return registered


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Reminder scheduler stopped")
