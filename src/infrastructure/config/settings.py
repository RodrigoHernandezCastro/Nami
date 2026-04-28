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

    # MariaDB / MySQL
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Logging
    LOG_LEVEL: str = "INFO"

    # Reglas de negocio
    DEFAULT_STREAMER_LIMIT: int = 15
    CHECK_INTERVAL_SECONDS: int = 60