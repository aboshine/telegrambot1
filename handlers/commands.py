"""Basic command handlers (/start, /help)."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Hello! This bot is running on aiogram 3.\n"
        "Use /help to see available commands."
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Available commands:\n"
        "/start — welcome message\n"
        "/help — this help text"
    )
