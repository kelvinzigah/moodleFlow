from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: PostgresDsn
    credential_key: SecretStr
    cors_origins: list[str] = ["http://localhost:5173"]
    telegram_mode: Literal["long_polling", "webhook"] = "long_polling"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    heartbeat_interval_seconds: int = 60
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
