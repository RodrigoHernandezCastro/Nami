import discord
from discord.ext import commands
from src.domain.exceptions.domain_exceptions import (
    ChannelLimitReachedError, ChannelNotFoundError, DomainError, StreamerAlreadyExistsError, StreamerLimitReachedError,
    StreamerNotOnTwitchError, ChannelNotConfiguredError, StreamerNotFoundError, YouTubeChannelNotFoundError,
)


class GlobalErrorHandler:
    """Handler centralizado de errores para comandos slash."""

    ERROR_MAP = {
        StreamerAlreadyExistsError: ("⚠️", "Ese streamer ya está registrado."),
        StreamerLimitReachedError:  ("📛", "Has alcanzado el límite de streamers."),
        StreamerNotOnTwitchError:   ("❌", "Ese usuario no existe en Twitch."),
        ChannelNotConfiguredError:  ("⚙️", "Configura primero el canal con `/configurar`."),
        StreamerNotFoundError:      ("🔍", "No encontré ese streamer."),
        YouTubeChannelNotFoundError:("📺", "Ese canal de YouTube no está monitoreado."),
        ChannelNotFoundError:       ("❌", "El canal de YouTube no existe."),
        ChannelLimitReachedError:   ("📛", "Has alcanzado el límite de canales."),
    }

    def __init__(self, bot: commands.Bot, logger) -> None:
        self.bot = bot
        self.logger = logger

    def register(self) -> None:
        self.bot.tree.on_error = self._on_app_command_error

    async def _on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        original = getattr(error, "original", error)

        for exc_type, (emoji, default_msg) in self.ERROR_MAP.items():
            if isinstance(original, exc_type):
                msg = str(original) or default_msg
                await self._respond(interaction, f"{emoji} {msg}")
                self.logger.info(
                    "domain_error",
                    type=exc_type.__name__,
                    user_id=interaction.user.id,
                    guild_id=interaction.guild_id,
                )
                return

        if isinstance(original, DomainError):
            await self._respond(interaction, f"{original}")
            return

        self.logger.error(
            "unexpected_error",
            error=str(original),
            error_type=type(original).__name__,
            user_id=interaction.user.id,
            guild_id=interaction.guild_id,
            exc_info=True,
        )
        await self._respond(
            interaction,
            "Ocurrió un error inesperado. El equipo ha sido notificado.",
        )

    @staticmethod
    async def _respond(interaction: discord.Interaction, msg: str) -> None:
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            pass