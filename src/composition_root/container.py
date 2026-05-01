# src/composition_root/container.py
import importlib
import aiomysql
import asyncpg
from src.infrastructure.config.settings import Settings
from src.infrastructure.logging.structured_logger import StructuredLogger


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool: aiomysql.Pool | asyncpg.Pool | None = None
        self._logger = StructuredLogger(level=settings.LOG_LEVEL)

    async def startup(self) -> None:
        if self.settings.db_driver == "postgres":
            await self._setup_postgres()
        else:
            await self._setup_mariadb()

        # Repositorios (automático según driver)
        await self._setup_repositories()

        # Servicios externos
        await self._setup_external_services()

        # Use Cases
        self._setup_use_cases()

        self._logger.info("container_startup_complete", driver=self.settings.db_driver)

    async def _setup_postgres(self) -> None:
        """Configuración para PostgreSQL local."""
        self._pool = await asyncpg.create_pool(
            dsn=self.settings.database_url,
            min_size=2,
            max_size=10,
        )
        self._logger.info("postgres_pool_created")

        # Importar repositorios PostgreSQL
        from src.infrastructure.persistence.postgres.streamer_repository_pg import PostgresStreamerRepository
        from src.infrastructure.persistence.postgres.guild_repository_pg import PostgresGuildRepository
        from src.infrastructure.persistence.postgres.youtube_repository_pg import PostgresYouTubeRepository

        self.streamer_repo = PostgresStreamerRepository(self._pool)
        self.guild_repo = PostgresGuildRepository(self._pool)
        self.youtube_repo = PostgresYouTubeRepository(self._pool, logger=self._logger)

    async def _setup_mariadb(self) -> None:
        """Configuración para MariaDB Teramont."""
        self._pool = await aiomysql.create_pool(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD,
            db=self.settings.DB_NAME,
            minsize=2,
            maxsize=10,
            autocommit=True,
            charset="utf8mb4",
        )
        self._logger.info("mariadb_pool_created")

        # Importar repositorios MariaDB
        from src.infrastructure.persistence.mariadb.streamer_repository_mysql import MariaDBStreamerRepository
        from src.infrastructure.persistence.mariadb.guild_repository_mysql import MariaDBGuildRepository
        from src.infrastructure.persistence.mariadb.youtube_repository_mysql import MariaDBYouTubeRepository

        self.streamer_repo = MariaDBStreamerRepository(self._pool)
        self.guild_repo = MariaDBGuildRepository(self._pool)
        self.youtube_repo = MariaDBYouTubeRepository(self._pool)

    async def _setup_repositories(self) -> None:
        """Configuración de repositorios (ya hecho arriba)."""
        pass

    async def _setup_external_services(self) -> None:
        """Twitch + YouTube."""
        from src.infrastructure.external_apis.twitch_api_client import TwitchAPIClient
        from src.infrastructure.external_apis.youtube_api_client import YouTubeAPIClient

        self.twitch_service = TwitchAPIClient(
            client_id=self.settings.TWITCH_CLIENT_ID,
            client_secret=self.settings.TWITCH_CLIENT_SECRET,
            logger=self._logger,
        )
        await self.twitch_service.initialize()

        self.youtube_service = YouTubeAPIClient(
            api_key=self.settings.YOUTUBE_API_KEY,
            logger=self._logger,
        )
        await self.youtube_service.initialize()

    def _setup_use_cases(self) -> None:
        """Ensamblar todos los casos de uso."""
        from src.application.use_cases.add_streamer import AddStreamerUseCase
        from src.application.use_cases.remove_streamer import RemoveStreamerUseCase
        from src.application.use_cases.list_streamers import ListStreamersUseCase
        from src.application.use_cases.configure_channel import ConfigureChannelUseCase
        from src.application.use_cases.check_live_streams import CheckLiveStreamsUseCase
        from src.application.use_cases.add_youtube_channel import AddYouTubeChannelUseCase
        from src.application.use_cases.remove_youtube_channel import RemoveYouTubeChannelUseCase
        from src.application.use_cases.list_youtube_channels import ListYouTubeChannelsUseCase
        from src.application.use_cases.check_youtube_videos import CheckYouTubeVideosUseCase

        # Twitch
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
        self.list_streamers_uc = ListStreamersUseCase(self.streamer_repo)
        self.configure_channel_uc = ConfigureChannelUseCase(
            guild_repo=self.guild_repo,
            logger=self._logger,
        )
        self.check_live_uc = CheckLiveStreamsUseCase(
            streamer_repo=self.streamer_repo,
            twitch_service=self.twitch_service,
            logger=self._logger,
        )

        # YouTube
        self.add_youtube_uc = AddYouTubeChannelUseCase(
            youtube_repo=self.youtube_repo,
            guild_repo=self.guild_repo,
            youtube_service=self.youtube_service,
            logger=self._logger,
        )
        self.remove_youtube_uc = RemoveYouTubeChannelUseCase(
            youtube_repo=self.youtube_repo,
            logger=self._logger,
        )
        self.list_youtube_uc = ListYouTubeChannelsUseCase(self.youtube_repo)
        self.check_youtube_uc = CheckYouTubeVideosUseCase(
            youtube_repo=self.youtube_repo,
            youtube_service=self.youtube_service,
            logger=self._logger,
        )

    async def shutdown(self) -> None:
        """Cierra todas las conexiones."""
        if hasattr(self, '_pool') and self._pool:
            if self.settings.db_driver == "postgres":
                await self._pool.close()
            else:
                self._pool.close()
                await self._pool.wait_closed()

        if hasattr(self, 'twitch_service'):
            await self.twitch_service.close()
        if hasattr(self, 'youtube_service'):
            await self.youtube_service.close()

        self._logger.info("container_shutdown_complete")

    @property
    def logger(self):
        return self._logger