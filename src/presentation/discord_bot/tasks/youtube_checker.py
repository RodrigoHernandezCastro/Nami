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
        self.check_videos.start()

    async def cog_unload(self) -> None:
        self.check_videos.cancel()

    @tasks.loop(minutes=5)
    async def check_videos(self) -> None:
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
        await self.bot.wait_until_ready()
        self._logger.info("youtube_checker_started")

    async def _announce_video(self, channel: YouTubeChannel, video: dict) -> None:
        """Publica ANTES de marcar como anunciado (evita race conditions)."""
        config = await self._guild_repo.get_by_id(channel.guild_id)
        if not config or not config.announcement_channel_id:
            return

        channel_obj = self.bot.get_channel(config.announcement_channel_id)
        if not channel_obj:
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
                message_id=msg.id,  # Para debug
            )
        except discord.Forbidden:
            self._logger.warning("no_permission_youtube_announce")