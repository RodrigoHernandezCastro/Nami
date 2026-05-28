import discord
from discord.ext import commands

from src.domain.exceptions.domain_exceptions import DomainError
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
from src.presentation.discord_bot.error_messages import domain_error_message


class GlobalErrorHandler:
    """Handler centralizado de errores para comandos slash."""

    def __init__(self, bot: commands.Bot, logger, lang_resolver: GuildLanguageResolver) -> None:
        self.bot = bot
        self.logger = logger
        self._i18n = lang_resolver

    def register(self) -> None:
        self.bot.tree.on_error = self._on_app_command_error

    async def _on_app_command_error(self, interaction, error) -> None:
        original = getattr(error, "original", error)
        gid = interaction.guild_id

        if isinstance(original, DomainError):
            self.logger.info(
                "domain_error",
                type=type(original).__name__,
                detail=str(original),
                user_id=interaction.user.id,
                guild_id=gid,
            )
        else:
            self.logger.error(
                "unexpected_error",
                error=str(original),
                error_type=type(original).__name__,
                user_id=interaction.user.id,
                guild_id=gid,
                exc_info=True,
            )

        msg = await domain_error_message(original, gid, self._i18n)
        await self._respond(interaction, msg)

    @staticmethod
    async def _respond(interaction: discord.Interaction, msg: str) -> None:
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            pass
