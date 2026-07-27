"""Async SQLite storage for users and activity."""

from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "data" / "bot.db"

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    streak_count INTEGER NOT NULL DEFAULT 0,
    last_active_date TEXT
);
"""


async def init_db() -> None:
    """Create the database file and tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_USERS_TABLE)
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
