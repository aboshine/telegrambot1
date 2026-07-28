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
        "/done — submit today's report (or send #отчет)\n"
        "/top — streak leaderboard\n"
        "/new_challenge — create group challenge (admins, groups)\n"
        "/challenge — current challenge and participants\n"
        "/help — this help text"
    )
