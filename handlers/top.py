"""Leaderboard command /top."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import TopUser, get_top_users

router = Router(name="top")

_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

_EMPTY_TEXT = (
    "Список лидеров пока пуст. Будь первым, кто отправит /done!"
)


def _format_user_line(place: int, user: TopUser) -> str:
    name = user["full_name"] or "Пользователь"
    if user["username"]:
        identity = f"{name} (@{user['username']})"
    else:
        identity = name

    streak = user["streak_count"]
    if place in _MEDALS:
        prefix = f"{place}. {_MEDALS[place]}"
    else:
        prefix = f"{place}."

    return f"{prefix} {identity} — 🔥 {streak} дней"


def _format_leaderboard(users: list[TopUser]) -> str:
    lines = ["🏆 <b>Таблица лидеров</b>", ""]
    for place, user in enumerate(users, start=1):
        lines.append(_format_user_line(place, user))
    return "\n".join(lines)


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    users = await get_top_users()
    if not users:
        await message.answer(_EMPTY_TEXT)
        return
    await message.answer(_format_leaderboard(users))
