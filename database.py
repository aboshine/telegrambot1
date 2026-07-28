"""Async SQLite storage for users and activity."""

from datetime import date, timedelta
from pathlib import Path
from typing import Literal, TypedDict

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "data" / "bot.db"

ReportStatus = Literal["already_done", "success", "reset"]


class TopUser(TypedDict):
    user_id: int
    username: str | None
    full_name: str | None
    streak_count: int


class ChallengeParticipant(TypedDict):
    user_id: int
    username: str | None
    full_name: str | None


class ActiveChallenge(TypedDict):
    id: int
    title: str
    description: str
    participants: list[ChallengeParticipant]

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    streak_count INTEGER NOT NULL DEFAULT 0,
    last_active_date TEXT
);
"""

_CREATE_CHALLENGES_TABLE = """
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0
);
"""

_CREATE_CHALLENGE_PARTICIPANTS_TABLE = """
CREATE TABLE IF NOT EXISTS challenge_participants (
    challenge_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (challenge_id, user_id),
    FOREIGN KEY (challenge_id) REFERENCES challenges(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

_CREATE_BOT_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

REMINDER_CHAT_ID_KEY = "reminder_chat_id"


async def init_db() -> None:
    """Create the database file and tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_USERS_TABLE)
        await db.execute(_CREATE_CHALLENGES_TABLE)
        await db.execute(_CREATE_CHALLENGE_PARTICIPANTS_TABLE)
        await db.execute(_CREATE_BOT_SETTINGS_TABLE)
        await db.commit()


async def add_or_update_user(
    user_id: int,
    username: str | None,
    full_name: str | None,
) -> None:
    """Insert a new user or refresh username and full_name for an existing one."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name),
        )
        await db.commit()


async def process_daily_report(user_id: int) -> tuple[ReportStatus, int]:
    """
    Record today's report and update streak.

    Returns (status, streak_count):
    - already_done — already reported today
    - success — continued from yesterday, streak incremented
    - reset — first report or gap, streak set to 1
    """
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT streak_count, last_active_date FROM users WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            await db.execute(
                """
                INSERT INTO users (user_id, streak_count, last_active_date)
                VALUES (?, 1, ?)
                """,
                (user_id, today),
            )
            await db.commit()
            return "reset", 1

        streak_count = int(row["streak_count"])
        last_active_date = row["last_active_date"]

        if last_active_date == today:
            return "already_done", streak_count

        if last_active_date == yesterday:
            new_streak = streak_count + 1
            await db.execute(
                """
                UPDATE users
                SET streak_count = ?, last_active_date = ?
                WHERE user_id = ?
                """,
                (new_streak, today, user_id),
            )
            await db.commit()
            return "success", new_streak

        await db.execute(
            """
            UPDATE users
            SET streak_count = 1, last_active_date = ?
            WHERE user_id = ?
            """,
            (today, user_id),
        )
        await db.commit()
        return "reset", 1


async def get_top_users(limit: int = 10) -> list[TopUser]:
    """Return users with the highest streak_count, descending."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT user_id, username, full_name, streak_count
            FROM users
            WHERE streak_count > 0
            ORDER BY streak_count DESC, user_id ASC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
    return [
        TopUser(
            user_id=int(row["user_id"]),
            username=row["username"],
            full_name=row["full_name"],
            streak_count=int(row["streak_count"]),
        )
        for row in rows
    ]


async def create_challenge(title: str, description: str) -> int:
    """Deactivate previous challenges and create a new active one. Returns new challenge id."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE challenges SET is_active = 0 WHERE is_active = 1")
        cursor = await db.execute(
            """
            INSERT INTO challenges (title, description, is_active)
            VALUES (?, ?, 1)
            """,
            (title.strip(), description.strip()),
        )
        await db.commit()
        return int(cursor.lastrowid)


async def get_active_challenge() -> ActiveChallenge | None:
    """Return the active challenge and all registered participants."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, title, description
            FROM challenges
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        ) as cursor:
            challenge_row = await cursor.fetchone()

        if challenge_row is None:
            return None

        challenge_id = int(challenge_row["id"])
        async with db.execute(
            """
            SELECT u.user_id, u.username, u.full_name
            FROM challenge_participants cp
            JOIN users u ON u.user_id = cp.user_id
            WHERE cp.challenge_id = ?
            ORDER BY u.full_name COLLATE NOCASE, u.user_id
            """,
            (challenge_id,),
        ) as cursor:
            participant_rows = await cursor.fetchall()

    participants = [
        ChallengeParticipant(
            user_id=int(row["user_id"]),
            username=row["username"],
            full_name=row["full_name"],
        )
        for row in participant_rows
    ]
    return ActiveChallenge(
        id=challenge_id,
        title=str(challenge_row["title"]),
        description=str(challenge_row["description"]),
        participants=participants,
    )


async def join_challenge(challenge_id: int, user_id: int) -> bool:
    """
    Register user as participant.

    Returns True if newly joined, False if already participating.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO challenge_participants (challenge_id, user_id)
                VALUES (?, ?)
                """,
                (challenge_id, user_id),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_stored_reminder_chat_id() -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (REMINDER_CHAT_ID_KEY,),
        ) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    try:
        return int(row[0])
    except (TypeError, ValueError):
        return None


async def set_reminder_chat_id_if_unset(chat_id: int) -> bool:
    """Persist reminder chat id when none is stored yet. Returns True if saved."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (REMINDER_CHAT_ID_KEY,),
        ) as cursor:
            existing = await cursor.fetchone()
        if existing is not None:
            return False
        await db.execute(
            """
            INSERT INTO bot_settings (key, value)
            VALUES (?, ?)
            """,
            (REMINDER_CHAT_ID_KEY, str(chat_id)),
        )
        await db.commit()
        return True
