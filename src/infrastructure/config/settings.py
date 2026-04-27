from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Discord
    DISCORD_TOKEN: str

    # Twitch
    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str

    # PostgreSQL
    DATABASE_URL: str  # postgresql://user:pass@host:5432/db

    # Logging
    LOG_LEVEL: str = "INFO"

    # Reglas de negocio
    DEFAULT_STREAMER_LIMIT: int = 15
    CHECK_INTERVAL_SECONDS: int = 60