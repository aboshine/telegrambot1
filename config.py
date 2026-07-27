"""Application settings loaded from environment variables."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot configuration. Values are read from the process environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr = Field(..., description="Telegram Bot API token from @BotFather")
    log_level: str = Field(default="INFO", description="Python logging level (DEBUG, INFO, WARNING, ERROR)")


def get_settings() -> Settings:
    return Settings()
