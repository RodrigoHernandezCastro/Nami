# src/infrastructure/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Discord
    DISCORD_TOKEN: str
    DEV_GUILD_ID: Optional[str] = None

    # Twitch
    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str

    # YouTube
    YOUTUBE_API_KEY: str

    # PostgreSQL (local)
    DATABASE_URL: Optional[str] = None

    # MariaDB (Teramont)
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 3306
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    # Reglas de negocio
    DEFAULT_STREAMER_LIMIT: int = 15
    CHECK_INTERVAL_SECONDS: int = 60

    @property
    def database_url(self) -> str:
        """
        Devuelve la URL de BD según el entorno.
        Prioridad: DATABASE_URL > MariaDB vars
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        raise ValueError(
            "Debes configurar DATABASE_URL (PostgreSQL) O las variables MariaDB (DB_HOST, DB_USER, etc.)"
        )

    @property
    def db_driver(self) -> str:
        """Detecta automáticamente el driver según la URL."""
        if self.DATABASE_URL and "postgresql" in self.DATABASE_URL.lower():
            return "postgres"
        return "mariadb"