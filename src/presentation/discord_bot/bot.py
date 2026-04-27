import discord
from discord.ext import commands
from src.presentation.discord_bot.cogs.monitor_cog import MonitorCog
from src.presentation.discord_bot.tasks.stream_checker import StreamCheckerTask
from src.presentation.discord_bot.error_handler import GlobalErrorHandler


class NamiBot(commands.Bot):
    def __init__(self, container, settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # No lo necesitamos con slash commands
        super().__init__(command_prefix="!", intents=intents)
        self.container = container
        self.settings = settings

    async def setup_hook(self) -> None:
        # 1) Registrar Cog de comandos
        await self.add_cog(
            MonitorCog(
                bot=self,
                add_streamer_uc=self.container.add_streamer_uc,
                remove_streamer_uc=self.container.remove_streamer_uc,
                list_streamers_uc=self.container.list_streamers_uc,
                configure_channel_uc=self.container.configure_channel_uc,
            )
        )

        # 2) Registrar tarea en segundo plano
        await self.add_cog(
            StreamCheckerTask(
                bot=self,
                check_live_uc=self.container.check_live_uc,
                guild_repo=self.container.guild_repo,
                logger=self.container.logger,
                interval_seconds=self.settings.CHECK_INTERVAL_SECONDS,
            )
        )

        # 3) Handler global de errores
        GlobalErrorHandler(self, self.container.logger).register()

        # 4) Sincronizar slash commands
        synced = await self.tree.sync()
        self.container.logger.info(
            "bot_ready",
            commands_synced=len(synced),
        )