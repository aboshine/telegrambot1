"""Group challenge commands and join callback."""

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database import (
    ActiveChallenge,
    ChallengeParticipant,
    add_or_update_user,
    create_challenge,
    get_active_challenge,
    join_challenge,
)

router = Router(name="challenges")

JOIN_CALLBACK_PREFIX = "challenge_join:"


def _participate_keyboard(challenge_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Участвовать",
                    callback_data=f"{JOIN_CALLBACK_PREFIX}{challenge_id}",
                )
            ]
        ]
    )


async def _is_chat_admin(message: Message) -> bool:
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return True
    if message.from_user is None:
        return False
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in {"creator", "administrator"}


def _format_participant(participant: ChallengeParticipant) -> str:
    name = participant["full_name"] or "Пользователь"
    if participant["username"]:
        return f"• {name} (@{participant['username']})"
    return f"• {name}"


async def _participants_in_chat(
    message: Message,
    participants: list[ChallengeParticipant],
) -> list[ChallengeParticipant]:
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return participants

    in_chat: list[ChallengeParticipant] = []
    for participant in participants:
        try:
            member = await message.bot.get_chat_member(
                message.chat.id,
                participant["user_id"],
            )
        except Exception:
            continue
        if member.status not in {"left", "kicked"}:
            in_chat.append(participant)
    return in_chat


def _format_challenge_view(
    challenge: ActiveChallenge,
    participants: list[ChallengeParticipant],
) -> str:
    lines = [
        f"🎯 <b>{challenge['title']}</b>",
        "",
        challenge["description"],
        "",
        f"<b>Участники ({len(participants)}):</b>",
    ]
    if participants:
        lines.extend(_format_participant(p) for p in participants)
    else:
        lines.append("Пока никого нет. Нажми «🎯 Участвовать» в анонсе челленджа!")
    return "\n".join(lines)


@router.message(Command("new_challenge"))
async def cmd_new_challenge(message: Message, command: CommandObject) -> None:
    if not await _is_chat_admin(message):
        await message.answer("Создавать челлендж могут только администраторы группы.")
        return

    raw = (command.args or "").strip()
    if "|" not in raw:
        await message.answer(
            "Формат команды:\n"
            "<code>/new_challenge Название | Описание</code>\n\n"
            "Пример:\n"
            "<code>/new_challenge 30 дней кода | Каждый день минимум 1 коммит</code>"
        )
        return

    title, description = (part.strip() for part in raw.split("|", 1))
    if not title or not description:
        await message.answer("Укажи и название, и описание через символ |.")
        return

    challenge_id = await create_challenge(title, description)

    await message.answer(
        "🎯 <b>Новый челлендж!</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        "Нажми кнопку ниже, чтобы участвовать.",
        reply_markup=_participate_keyboard(challenge_id),
    )


@router.message(Command("challenge"))
async def cmd_challenge(message: Message) -> None:
    challenge = await get_active_challenge()
    if challenge is None:
        await message.answer("Сейчас нет активного челленджа.")
        return

    participants = await _participants_in_chat(message, challenge["participants"])
    await message.answer(_format_challenge_view(challenge, participants))


@router.callback_query(F.data.startswith(JOIN_CALLBACK_PREFIX))
async def on_join_challenge(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer()
        return

    challenge_id_str = callback.data.removeprefix(JOIN_CALLBACK_PREFIX)
    if not challenge_id_str.isdigit():
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return

    challenge_id = int(challenge_id_str)
    active = await get_active_challenge()
    if active is None or active["id"] != challenge_id:
        await callback.answer(
            "Этот челлендж уже завершён. Дождись нового анонса.",
            show_alert=True,
        )
        return

    user = callback.from_user
    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name or user.first_name,
    )

    joined = await join_challenge(challenge_id, user.id)
    if joined:
        await callback.answer(
            "Ты успешно присоединился к челленджу!",
            show_alert=True,
        )
    else:
        await callback.answer("Ты уже участвуешь в этом челлендже.", show_alert=True)
