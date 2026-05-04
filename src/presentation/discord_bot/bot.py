import discord
from discord.ext import commands

from src.presentation.discord_bot.cogs.monitor_cog import MonitorCog
from src.presentation.discord_bot.cogs.youtube_cog import YouTubeCog
from src.presentation.discord_bot.cogs.admin_cog import AdminCog
from src.presentation.discord_bot.tasks.stream_checker import StreamCheckerTask
from src.presentation.discord_bot.error_handler import GlobalErrorHandler
from src.presentation.discord_bot.tasks.youtube_checker import YouTubeCheckerTask


class NamiBot(commands.Bot):
    """
    Bot principal. Recibe el contenedor DI y los settings para
    no instanciar dependencias directamente aquí.

    Expone `self.translator` como atajo para acceso rápido desde cogs.
    """
    def __init__(self, container, settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.container = container
        self.settings = settings
        self.translator = container.translator

    async def setup_hook(self) -> None:
        # 1) Cogs
        await self.add_cog(
            MonitorCog(
                bot=self,
                add_streamer_uc=self.container.add_streamer_uc,
                remove_streamer_uc=self.container.remove_streamer_uc,
                list_streamers_uc=self.container.list_streamers_uc,
                configure_channel_uc=self.container.configure_channel_uc,
                configure_youtube_uc=self.container.configure_youtube_uc,
                lang_resolver=self.container.lang_resolver,
                translator=self.container.translator,
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
                lang_resolver=self.container.lang_resolver,
                translator=self.container.translator,
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
        await self.add_cog(
            AdminCog(
                bot=self,
                set_language_uc=self.container.set_language_uc,
                lang_resolver=self.container.lang_resolver,
                translator=self.container.translator,
            )
        )

        GlobalErrorHandler(self, self.container.logger).register()

        # 2) Sync
        DEV_GUILD_ID = self.settings.DEV_GUILD_ID
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            self.container.logger.info("bot_ready_guild_sync", commands_synced=len(synced))
        else:
            synced = await self.tree.sync()
            self.container.logger.info("bot_ready_global_sync", commands_synced=len(synced))