# src/presentation/discord_bot/cogs/youtube_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from src.application.use_cases.add_youtube_channel import (
    AddYouTubeChannelUseCase, AddYouTubeCommand,
)
from src.application.use_cases.remove_youtube_channel import (
    RemoveYouTubeChannelUseCase, RemoveYouTubeCommand,
)
from src.application.use_cases.list_youtube_channels import (
    ListYouTubeChannelsUseCase, ListYouTubeQuery,
)
from src.domain.exceptions.domain_exceptions import DomainError, ChannelNotFoundError


class YouTubeCog(commands.Cog):
    """Comandos para monitorear canales de YouTube."""

    def __init__(
        self,
        bot: commands.Bot,
        add_youtube_uc: AddYouTubeChannelUseCase,
        remove_youtube_uc: RemoveYouTubeChannelUseCase,
        list_youtube_uc: ListYouTubeChannelsUseCase,
    ) -> None:
        self.bot = bot
        self._add_uc = add_youtube_uc
        self._remove_uc = remove_youtube_uc
        self._list_uc = list_youtube_uc

    @app_commands.command(
        name="añadir-youtube",
        description="Añade un canal de YouTube (@username)",
    )
    @app_commands.describe(
        usuario="Nombre del canal (@IlloJuan_, @HakosBaelz)",
        mensaje="Mensaje personalizado al anunciar nuevo video",
        mencion="Tipo de mención al anunciar",
        rol1="Primer rol a mencionar (solo si mencion='rol')",
        rol2="Segundo rol (opcional)",
        rol3="Tercer rol (opcional)",
    )
    @app_commands.choices(
        mencion=[
            app_commands.Choice(name="Ninguno", value="ninguno"),
            app_commands.Choice(name="@everyone", value="everyone"),
            app_commands.Choice(name="@here", value="here"),
            app_commands.Choice(name="Rol específico", value="rol"),
        ]
    )
    async def add_youtube(
        self,
        interaction: discord.Interaction,
        usuario: str,
        mensaje: str = "¡Nuevo video en YouTube!",
        mencion: Optional[app_commands.Choice[str]] = None,
        rol1: Optional[discord.Role] = None,
        rol2: Optional[discord.Role] = None,
        rol3: Optional[discord.Role] = None,
    ) -> None:
        """
        Slash /añadir-youtube.
        Resuelve @username → channel_id antes de ejecutar el use case.
        Si mencion='rol' y no se proporciona ningún rol, aborta antes de llamar a la API.
        """
        await interaction.response.defer(ephemeral=True)

        mention_type = mencion.value if mencion else "ninguno"
        mention_role_ids = None
        if mention_type == "rol":
            provided_roles = [r for r in (rol1, rol2, rol3) if r is not None]
            if not provided_roles:
                await interaction.followup.send(
                    "Debes proporcionar al menos un rol si eliges `rol`.",
                    ephemeral=True,
                )
                return
            mention_role_ids = [r.id for r in provided_roles]

        try:
            channel_id = await self._add_uc.resolve_username(usuario)

            cmd = AddYouTubeCommand(
                guild_id=interaction.guild_id,
                channel_id=channel_id,
                custom_message=mensaje,
                mention_type=mention_type,
                mention_role_ids=mention_role_ids,
            )
            channel = await self._add_uc.execute(cmd)

            result_embed = discord.Embed(
                title="✅ Canal YouTube añadido",
                color=discord.Color.red(),
            )
            result_embed.add_field(name="📺 Canal", value=channel.display_name, inline=True)
            result_embed.add_field(name="🔗 ID", value=f"`{channel.channel_name}`", inline=True)
            result_embed.add_field(
                name="Mención",
                value=self._format_mention(mention_type, mention_role_ids, interaction.guild),
                inline=True,
            )
            result_embed.add_field(name="Mensaje", value=channel.custom_message, inline=False)

            await interaction.followup.send(embed=result_embed, ephemeral=True)

        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    @app_commands.command(
        name="listar-youtube",
        description="Lista los canales de YouTube monitoreados",
    )
    async def list_youtube(self, interaction: discord.Interaction) -> None:
        """Slash /listar-youtube. Muestra nombre y mensaje de cada canal monitorizado."""
        await interaction.response.defer(ephemeral=True)

        channels = await self._list_uc.execute(
            ListYouTubeQuery(guild_id=interaction.guild_id)
        )

        if not channels:
            await interaction.followup.send(
                "No hay canales de YouTube monitoreados.",
                ephemeral=True,
            )
            return

        list_embed = discord.Embed(title="📺 Canales YouTube", color=discord.Color.red())
        for c in channels:
            list_embed.add_field(
                name=c.display_name,
                value=c.custom_message[:80],
                inline=False,
            )
        list_embed.set_footer(text=f"Total: {len(channels)}")
        await interaction.followup.send(embed=list_embed, ephemeral=True)

    @app_commands.command(
        name="eliminar-youtube",
        description="Deja de monitorear un canal de YouTube (@username o ID)",
    )
    @app_commands.describe(usuario="Nombre del canal (@IlloJuan_) o ID directo (UCxxxx)")
    async def remove_youtube(
        self,
        interaction: discord.Interaction,
        usuario: str,
    ) -> None:
        """
        Slash /eliminar-youtube.
        Acepta tanto @username como channel_id directo (UCxxxx).
        Si la resolución de @username falla, intenta usar el valor tal cual como fallback.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            # Si empieza por UC y no tiene @, asumimos que ya es un channel_id directo.
            # Si no, intentamos resolver el @username → channel_id.
            if usuario.startswith("UC") and not usuario.startswith("@"):
                channel_id = usuario
            else:
                try:
                    channel_id = await self._add_uc.resolve_username(usuario)
                except ChannelNotFoundError:
                    # Último intento: tratar el valor tal cual como channel_id
                    channel_id = usuario

            await self._remove_uc.execute(
                RemoveYouTubeCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel_id,
                )
            )
            await interaction.followup.send(
                f"Canal `{usuario}` eliminado del monitoreo.",
                ephemeral=True,
            )
        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    @staticmethod
    def _format_mention(
        mention_type: str,
        role_ids: Optional[List[int]],
        guild: discord.Guild,
    ) -> str:
        """
        Igual que MonitorCog._format_mention_info pero devuelve mention directamente.
        Candidato a extraerse a un helper compartido en un futuro refactor.
        """
        if mention_type == "ninguno":
            return "Ninguna"
        if mention_type == "everyone":
            return "@everyone"
        if mention_type == "here":
            return "@here"
        if mention_type == "rol" and role_ids:
            mentions = [
                guild.get_role(rid).mention
                for rid in role_ids
                if guild.get_role(rid)
            ]
            return " ".join(mentions) if mentions else "Rol no encontrado"
        return "Desconocido"