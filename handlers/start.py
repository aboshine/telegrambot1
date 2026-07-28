"""Handler for /start."""

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import get_settings
from database import add_or_update_user
from reminders import register_group_for_reminders

router = Router(name="start")


def _display_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "друг"
    return user.full_name or user.first_name or "друг"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is not None:
        await add_or_update_user(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name or user.first_name,
        )

    name = _display_name(message)
    extra = ""
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        settings = get_settings()
        if await register_group_for_reminders(message.bot, message.chat.id, settings):
            extra = (
                "\n\n⏰ Эта группа сохранена для ежедневных напоминаний в 20:00 "
                f"({settings.reminder_timezone})."
            )

    await message.answer(
        f"Привет, <b>{name}</b>! 👋\n\n"
        "Добро пожаловать в бота. Здесь можно получать уведомления и пользоваться командами.\n"
        "Напиши /help, чтобы увидеть список команд."
        f"{extra}"
    )
