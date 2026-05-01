import discord
from discord.ext import commands
from src.presentation.discord_bot.cogs.monitor_cog import MonitorCog
from src.presentation.discord_bot.cogs.youtube_cog import YouTubeCog
from src.presentation.discord_bot.tasks.stream_checker import StreamCheckerTask
from src.presentation.discord_bot.error_handler import GlobalErrorHandler
from src.presentation.discord_bot.tasks.youtube_checker import YouTubeCheckerTask


class NamiBot(commands.Bot):
    def __init__(self, container, settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # No lo necesitamos con slash commands
        super().__init__(command_prefix="!", intents=intents)
        self.container = container
        self.settings = settings

    async def setup_hook(self) -> None:
        # 1) Todos los cogs PRIMERO
        await self.add_cog(
            MonitorCog(
                bot=self,
                add_streamer_uc=self.container.add_streamer_uc,
                remove_streamer_uc=self.container.remove_streamer_uc,
                list_streamers_uc=self.container.list_streamers_uc,
                configure_channel_uc=self.container.configure_channel_uc,
            )
        )
        await self.add_cog(
            StreamCheckerTask(
                bot=self,
                check_live_uc=self.container.check_live_uc,
                guild_repo=self.container.guild_repo,
                logger=self.container.logger,
                interval_seconds=self.settings.CHECK_INTERVAL_SECONDS,
            )
        )
        await self.add_cog(
            YouTubeCog(
                bot=self,
                add_youtube_uc=self.container.add_youtube_uc,
                remove_youtube_uc=self.container.remove_youtube_uc,
                list_youtube_uc=self.container.list_youtube_uc,
            )
        )
        await self.add_cog(
            YouTubeCheckerTask(
                bot=self,
                check_videos_uc=self.container.check_youtube_uc,
                guild_repo=self.container.guild_repo,
                logger=self.container.logger,
            )
        )

        GlobalErrorHandler(self, self.container.logger).register()

        # 2) Guild sync INSTANTÁNEO para desarrollo
        DEV_GUILD_ID = self.settings.DEV_GUILD_ID  # añade esto a tu .env
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            self.container.logger.info("bot_ready_guild_sync", commands_synced=len(synced))
        else:
            # Global sync (hasta 1 hora de propagación)
            synced = await self.tree.sync()
            self.container.logger.info("bot_ready_global_sync", commands_synced=len(synced))