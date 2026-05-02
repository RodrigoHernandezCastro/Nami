# src/presentation/discord_bot/tasks/youtube_checker.py
import discord
from discord.ext import commands, tasks

from src.application.use_cases.check_youtube_videos import CheckYouTubeVideosUseCase
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.logger import ILogger
from src.presentation.discord_bot.views.youtube_embed import YouTubeEmbedBuilder
from src.domain.entities.youtube_channel import YouTubeChannel


class YouTubeCheckerTask(commands.Cog):
    """Tarea en segundo plano que chequea nuevos videos de YouTube."""

    def __init__(
        self,
        bot: commands.Bot,
        check_videos_uc: CheckYouTubeVideosUseCase,
        guild_repo: IGuildRepository,
        logger: ILogger,
        interval_minutes: int = 5,
    ) -> None:
        self.bot = bot
        self._check_uc = check_videos_uc
        self._guild_repo = guild_repo
        self._logger = logger
        self.check_videos.change_interval(minutes=interval_minutes)

    async def cog_load(self) -> None:
        """Arranca el loop al registrar el Cog en el bot."""
        self.check_videos.start()

    async def cog_unload(self) -> None:
        """Detiene el loop limpiamente al desregistrar el Cog."""
        self.check_videos.cancel()

    @tasks.loop(minutes=5)
    async def check_videos(self) -> None:
        """
        Loop principal. Intervalo configurable vía interval_minutes en el constructor.
        El intervalo de 5 min es suficiente dado el coste bajo de cuota de la estrategia
        de playlist_id cacheado (1 unidad por canal por ciclo).
        """
        try:
            new_videos = await self._check_uc.execute()
            for channel, video in new_videos:
                await self._announce_video(channel, video)
        except Exception as e:
            self._logger.error(
                "youtube_checker_failed",
                error=str(e),
                exc_info=True,
            )

    @check_videos.before_loop
    async def before_check(self) -> None:
        """Espera a que el bot esté completamente listo antes del primer ciclo."""
        await self.bot.wait_until_ready()
        self._logger.info("youtube_checker_started")

    async def _announce_video(self, channel: YouTubeChannel, video: dict) -> None:
        """
        Publica el video en el canal correcto:
        - Usa youtube_channel_id si está configurado (canal exclusivo de videos).
        - Si no, usa announcement_channel_id como fallback.
        """
        config = await self._guild_repo.get_by_id(channel.guild_id)
        if not config:
            return

        # Prioridad: canal dedicado a YouTube > canal general de anuncios
        target_channel_id = config.youtube_channel_id or config.announcement_channel_id
        if not target_channel_id:
            self._logger.warning(
                "youtube_no_channel_configured",
                guild_id=channel.guild_id,
            )
            return

        channel_obj = self.bot.get_channel(target_channel_id)
        if not channel_obj:
            self._logger.warning(
                "youtube_channel_not_found",
                guild_id=channel.guild_id,
                channel_id=target_channel_id,
            )
            return

        embed = YouTubeEmbedBuilder.build_video_embed(video, channel)
        content = YouTubeEmbedBuilder.build_mention_content(channel)

        try:
            msg = await channel_obj.send(content=content, embed=embed)
            self._logger.info(
                "youtube_video_announced",
                guild_id=channel.guild_id,
                channel_id=channel.channel_id,
                video_id=video["video_id"],
                discord_channel_id=target_channel_id,
                message_id=msg.id,
            )
        except discord.Forbidden:
            self._logger.warning(
                "no_permission_youtube_announce",
                guild_id=channel.guild_id,
                channel_id=target_channel_id,
            )