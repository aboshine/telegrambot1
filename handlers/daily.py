"""Daily report / streak handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import add_or_update_user, process_daily_report

router = Router(name="daily")

_HASHTAG_REPORT = F.text.regexp(r"(?i)^#отчет$")


@router.message(Command("done"))
@router.message(_HASHTAG_REPORT)
async def daily_report(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name or user.first_name,
    )

    status, streak = await process_daily_report(user.id)

    if status == "success":
        await message.answer(
            f"🔥 Отличная работа! Твой стрик увеличился до {streak} дней подряд!"
        )
    elif status == "already_done":
        await message.answer(
            "Ты уже засчитал отчёт за сегодня! Возвращайся завтра."
        )
    else:
        await message.answer(
            "Стрик начат заново! Текущий стрик: 1 день. Не пропускай дни!"
        )
