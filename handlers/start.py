"""Handler for /start."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import add_or_update_user

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
    await message.answer(
        f"Привет, <b>{name}</b>! 👋\n\n"
        "Добро пожаловать в бота. Здесь можно получать уведомления и пользоваться командами.\n"
        "Напиши /help, чтобы увидеть список команд."
    )
