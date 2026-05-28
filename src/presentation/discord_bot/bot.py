# src/presentation/discord_bot/bot.py
import discord
from discord.ext import commands

from src.presentation.discord_bot.cogs.monitor_cog import MonitorCog
from src.presentation.discord_bot.cogs.youtube_cog import YouTubeCog
from src.presentation.discord_bot.cogs.admin_cog import AdminCog
from src.presentation.discord_bot.cogs.jankenpon_cog import JankenponCog
from src.presentation.discord_bot.tasks.stream_checker import StreamCheckerTask
from src.presentation.discord_bot.tasks.youtube_checker import YouTubeCheckerTask
from src.presentation.discord_bot.error_handler import GlobalErrorHandler
from src.presentation.discord_bot.app_translator import NamiAppTranslator
from src.presentation.discord_bot.emoji_registry import AppEmojiRegistry


class NamiBot(commands.Bot):
    def __init__(self, container, settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.container = container
        self.settings = settings
        self.translator = container.translator

        # Registry de Application Emojis: vacío al construir, se rellena
        # en on_ready. Las views (jankenpon_embed) lo consultan vía
        # `bot.app_emojis.get("rock")`.
        self.app_emojis = AppEmojiRegistry(logger=container.logger)

    async def setup_hook(self) -> None:
        # 1) Translator de slash commands ANTES de cualquier add_cog.
        await self.tree.set_translator(
            NamiAppTranslator(
                translator=self.container.translator,
                logger=self.container.logger,
            )
        )

        # 2) Cogs
        await self.add_cog(
            MonitorCog(
                bot=self,
                add_streamer_uc=self.container.add_streamer_uc,
                remove_streamer_uc=self.container.remove_streamer_uc,
                list_streamers_uc=self.container.list_streamers_uc,
                update_streamer_uc=self.container.update_streamer_uc,
                configure_channel_uc=self.container.configure_channel_uc,
                configure_youtube_uc=self.container.configure_youtube_uc,
                configure_youtube_live_uc=self.container.configure_youtube_live_uc,
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
                update_youtube_uc=self.container.update_youtube_uc,
                configure_youtube_live_uc=self.container.configure_youtube_live_settings_uc,
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

        # JankenponCog con guard defensivo (por si Postgres en el futuro).
        if self.container.play_jankenpon_uc is not None:
            try:
                await self.add_cog(
                    JankenponCog(
                        bot=self,
                        play_uc=self.container.play_jankenpon_uc,
                        guild_lb_uc=self.container.guild_leaderboard_uc,
                        global_lb_uc=self.container.global_leaderboard_uc,
                        lang_resolver=self.container.lang_resolver,
                        translator=self.container.translator,
                    )
                )
            except commands.CommandRegistrationError as exc:
                existing = sorted(
                    {cmd.name for cmd in self.commands}
                    | {a for cmd in self.commands for a in cmd.aliases}
                )
                self.container.logger.error(
                    "jankenpon_cog_register_failed",
                    conflict=exc.name,
                    already_registered=existing,
                )
        else:
            self.container.logger.warning(
                "jankenpon_cog_skipped",
                reason="user_xp_repo not available for current driver",
                driver=self.settings.db_driver,
            )

        GlobalErrorHandler(self, self.container.logger, self.container.lang_resolver).register()

        # 3) Sync slash commands
        DEV_GUILD_ID = self.settings.DEV_GUILD_ID
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            self.container.logger.info("bot_ready_guild_sync", commands_synced=len(synced))
        else:
            synced = await self.tree.sync()
            self.container.logger.info("bot_ready_global_sync", commands_synced=len(synced))

    async def on_ready(self) -> None:
        """
        Carga las Application Emojis del bot la primera vez que estamos
        ready. on_ready puede dispararse varias veces (reconexiones); el
        registry es idempotente, así que no pasa nada.
        """
        await self.app_emojis.load(self)