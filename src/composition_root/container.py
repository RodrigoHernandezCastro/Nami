# src/composition_root/container.py
import asyncpg
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.postgres.streamer_repository_pg import (
    PostgresStreamerRepository,
)
from src.infrastructure.persistence.postgres.guild_repository_pg import (
    PostgresGuildRepository,
)
from src.infrastructure.external_apis.twitch_api_client import TwitchAPIClient
from src.infrastructure.logging.structured_logger import StructuredLogger
from src.application.use_cases.add_streamer import AddStreamerUseCase
from src.application.use_cases.remove_streamer import RemoveStreamerUseCase
from src.application.use_cases.list_streamers import ListStreamersUseCase
from src.application.use_cases.configure_channel import ConfigureChannelUseCase
from src.application.use_cases.check_live_streams import CheckLiveStreamsUseCase


class Container:
    """Composition Root: único lugar donde se ensamblan las dependencias."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool: asyncpg.Pool | None = None
        self._logger = StructuredLogger(level=settings.LOG_LEVEL)

    async def startup(self) -> None:
        # 1) Pool de PostgreSQL
        self._pool = await asyncpg.create_pool(
            dsn=self.settings.DATABASE_URL,
            min_size=2,
            max_size=10,
        )
        self._logger.info("postgres_pool_created")

        # 2) Repositorios
        self.streamer_repo = PostgresStreamerRepository(self._pool)
        self.guild_repo = PostgresGuildRepository(self._pool)

        # 3) Servicios externos
        self.twitch_service = TwitchAPIClient(
            client_id=self.settings.TWITCH_CLIENT_ID,
            client_secret=self.settings.TWITCH_CLIENT_SECRET,
            logger=self._logger,
        )
        await self.twitch_service.initialize()

        # 4) Use Cases
        self.add_streamer_uc = AddStreamerUseCase(
            streamer_repo=self.streamer_repo,
            guild_repo=self.guild_repo,
            twitch_service=self.twitch_service,
            logger=self._logger,
        )
        self.remove_streamer_uc = RemoveStreamerUseCase(
            streamer_repo=self.streamer_repo,
            logger=self._logger,
        )
        self.list_streamers_uc = ListStreamersUseCase(
            streamer_repo=self.streamer_repo,
        )
        self.configure_channel_uc = ConfigureChannelUseCase(
            guild_repo=self.guild_repo,
            logger=self._logger,
        )
        self.check_live_uc = CheckLiveStreamsUseCase(
            streamer_repo=self.streamer_repo,
            twitch_service=self.twitch_service,
            logger=self._logger,
        )

        self._logger.info("container_startup_complete")

    async def shutdown(self) -> None:
        if self._pool:
            await self._pool.close()
            self._logger.info("postgres_pool_closed")
        await self.twitch_service.close()
        self._logger.info("container_shutdown_complete")

    @property
    def logger(self):
        return self._logger