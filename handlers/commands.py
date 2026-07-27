"""Basic command handlers (/help)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="commands")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Available commands:\n"
        "/start — welcome message\n"
        "/help — this help text"
    )
