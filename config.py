"""Application settings loaded from environment variables."""

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot configuration. Values are read from the process environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    bot_token: SecretStr = Field(..., description="Telegram Bot API token from @BotFather")
    log_level: str = Field(default="INFO", description="Python logging level (DEBUG, INFO, WARNING, ERROR)")
    reminder_chat_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("CHAT_ID", "REMINDER_CHAT_ID"),
        description="Telegram chat id for daily reminders (group or channel)",
    )
    reminder_timezone: str = Field(
        default="Asia/Tashkent",
        validation_alias=AliasChoices("TIMEZONE", "REMINDER_TIMEZONE"),
        description="IANA timezone for scheduled reminders",
    )
    reminder_hour: int = Field(default=20, ge=0, le=23)
    reminder_minute: int = Field(default=0, ge=0, le=59)


def get_settings() -> Settings:
    return Settings()
