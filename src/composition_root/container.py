# src/composition_root/container.py
from pathlib import Path

import aiomysql
import asyncpg

from src.infrastructure.config.settings import Settings
from src.infrastructure.logging.structured_logger import StructuredLogger
from src.infrastructure.i18n.translator import JSONTranslator


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

        await self._setup_repositories()
        self._setup_i18n()
        await self._setup_external_services()
        self._setup_use_cases()

        self._logger.info("container_startup_complete", driver=self.settings.db_driver)

    async def _setup_postgres(self) -> None:
        self._pool = await asyncpg.create_pool(
            dsn=self.settings.database_url,
            min_size=2,
            max_size=10,
        )
        self._logger.info("postgres_pool_created")

        from src.infrastructure.persistence.postgres.streamer_repository_pg import PostgresStreamerRepository
        from src.infrastructure.persistence.postgres.guild_repository_pg import PostgresGuildRepository
        from src.infrastructure.persistence.postgres.youtube_repository_pg import PostgresYouTubeRepository

        self.streamer_repo = PostgresStreamerRepository(self._pool)
        self.guild_repo = PostgresGuildRepository(self._pool)
        self.youtube_repo = PostgresYouTubeRepository(self._pool, logger=self._logger)

        # NOTA: el repo de user_xp solo está implementado para MariaDB
        # (decisión del usuario). Si arrancas con Postgres, el cog
        # JankenponCog no podrá registrarse — bot.py debe hacer la
        # comprobación o crear el repo Postgres en el futuro.
        self.user_xp_repo = None

    async def _setup_mariadb(self) -> None:
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

        from src.infrastructure.persistence.mariadb.streamer_repository_mysql import MariaDBStreamerRepository
        from src.infrastructure.persistence.mariadb.guild_repository_mysql import MariaDBGuildRepository
        from src.infrastructure.persistence.mariadb.youtube_repository_mysql import MariaDBYouTubeRepository
        from src.infrastructure.persistence.mariadb.user_xp_repository_mysql import MariaDBUserXPRepository

        self.streamer_repo = MariaDBStreamerRepository(self._pool)
        self.guild_repo = MariaDBGuildRepository(self._pool)
        self.youtube_repo = MariaDBYouTubeRepository(self._pool)
        self.user_xp_repo = MariaDBUserXPRepository(self._pool)

    async def _setup_repositories(self) -> None:
        pass

    def _setup_i18n(self) -> None:
        """Carga el traductor JSON (idioma por defecto: en)."""
        src_dir = Path(__file__).resolve().parent.parent
        locales_dir = src_dir / "resources" / "locales"

        self.translator = JSONTranslator(
            locales_dir=locales_dir,
            logger=self._logger,
        )

        from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
        self.lang_resolver = GuildLanguageResolver(
            guild_repo=self.guild_repo,
            translator=self.translator,
            default_lang="en",
        )

    async def _setup_external_services(self) -> None:
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
        from src.application.use_cases.add_streamer import AddStreamerUseCase
        from src.application.use_cases.remove_streamer import RemoveStreamerUseCase
        from src.application.use_cases.list_streamers import ListStreamersUseCase
        from src.application.use_cases.configure_channel import ConfigureChannelUseCase
        from src.application.use_cases.configure_channel_youtube import ConfigureChannelYouTubeUseCase
        from src.application.use_cases.check_live_streams import CheckLiveStreamsUseCase
        from src.application.use_cases.add_youtube_channel import AddYouTubeChannelUseCase
        from src.application.use_cases.remove_youtube_channel import RemoveYouTubeChannelUseCase
        from src.application.use_cases.list_youtube_channels import ListYouTubeChannelsUseCase
        from src.application.use_cases.check_youtube_videos import CheckYouTubeVideosUseCase
        from src.application.use_cases.set_guild_language import SetGuildLanguageUseCase
        # NUEVO: jankenpon
        from src.application.use_cases.play_jankenpon import PlayJankenponUseCase
        from src.application.use_cases.get_guild_leaderboard import GetGuildLeaderboardUseCase
        from src.application.use_cases.get_global_leaderboard import GetGlobalLeaderboardUseCase

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
        self.configure_youtube_uc = ConfigureChannelYouTubeUseCase(
            guild_repo=self.guild_repo,
            logger=self._logger,
        )

        # Admin / i18n
        self.set_language_uc = SetGuildLanguageUseCase(
            guild_repo=self.guild_repo,
            translator=self.translator,
            logger=self._logger,
        )

        # ─────────────────────────────────────────────────────────────
        # Jankenpon (XP y leaderboards)
        # Solo se cablean si tenemos repo (MariaDB). Con Postgres se
        # quedan en None y bot.py debe omitir el cog.
        # ─────────────────────────────────────────────────────────────
        if self.user_xp_repo is not None:
            self.play_jankenpon_uc = PlayJankenponUseCase(
                user_xp_repo=self.user_xp_repo,
                logger=self._logger,
            )
            self.guild_leaderboard_uc = GetGuildLeaderboardUseCase(
                user_xp_repo=self.user_xp_repo,
            )
            self.global_leaderboard_uc = GetGlobalLeaderboardUseCase(
                user_xp_repo=self.user_xp_repo,
            )
        else:
            self.play_jankenpon_uc = None
            self.guild_leaderboard_uc = None
            self.global_leaderboard_uc = None

    async def shutdown(self) -> None:
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