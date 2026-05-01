# src/presentation/discord_bot/cogs/monitor_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from src.application.use_cases.add_streamer import AddStreamerUseCase, AddStreamerCommand
from src.application.use_cases.remove_streamer import RemoveStreamerUseCase, RemoveStreamerCommand
from src.application.use_cases.list_streamers import ListStreamersUseCase, ListStreamersQuery
from src.application.use_cases.configure_channel import ConfigureChannelUseCase, ConfigureChannelCommand
from src.application.use_cases.configure_channel_youtube import (
    ConfigureChannelYouTubeUseCase, ConfigureChannelYouTubeCommand,
)
from src.domain.exceptions.domain_exceptions import DomainError


class MonitorCog(commands.Cog):
    """Comandos slash para gestionar el monitoreo de streamers."""

    def __init__(
        self,
        bot: commands.Bot,
        add_streamer_uc: AddStreamerUseCase,
        remove_streamer_uc: RemoveStreamerUseCase,
        list_streamers_uc: ListStreamersUseCase,
        configure_channel_uc: ConfigureChannelUseCase,
        configure_youtube_uc: ConfigureChannelYouTubeUseCase,
    ) -> None:
        self.bot = bot
        self._add_uc = add_streamer_uc
        self._remove_uc = remove_streamer_uc
        self._list_uc = list_streamers_uc
        self._configure_uc = configure_channel_uc
        self._configure_youtube_uc = configure_youtube_uc

    # ----------- /configurar -----------
    @app_commands.command(
        name="configurar",
        description="Configura el canal donde se anunciarán los streams en vivo (Twitch y YouTube Live)",
    )
    @app_commands.describe(canal="Canal donde se publicarán los anuncios de streams en vivo")
    @app_commands.default_permissions(administrator=True)
    async def configure(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._configure_uc.execute(
                ConfigureChannelCommand(
                    guild_id=interaction.guild_id,
                    channel_id=canal.id,
                )
            )
            await interaction.followup.send(
                f"✅ Canal de **streams en vivo** configurado: {canal.mention}\n"
                f"💡 Para configurar dónde se publican los videos de YouTube usa `/configurar-youtube`.",
                ephemeral=True,
            )
        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    # ----------- /configurar-youtube -----------
    @app_commands.command(
        name="configurar-youtube",
        description="Configura el canal donde se publicarán los videos y shorts de YouTube",
    )
    @app_commands.describe(canal="Canal donde se publicarán los videos de YouTube")
    @app_commands.default_permissions(administrator=True)
    async def configure_youtube(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._configure_youtube_uc.execute(
                ConfigureChannelYouTubeCommand(
                    guild_id=interaction.guild_id,
                    channel_id=canal.id,
                )
            )
            await interaction.followup.send(
                f"✅ Canal de **videos de YouTube** configurado: {canal.mention}",
                ephemeral=True,
            )
        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    # ----------- /añadir -----------
    @app_commands.command(
        name="añadir",
        description="Añade un streamer de Twitch para monitorear",
    )
    @app_commands.describe(
        usuario="Nombre de usuario de Twitch",
        mensaje="Mensaje personalizado al anunciar el stream",
        mencion="Tipo de mención al anunciar",
        rol1="Primer rol a mencionar (solo si mencion='rol')",
        rol2="Segundo rol a mencionar (opcional)",
        rol3="Tercer rol a mencionar (opcional)",
    )
    @app_commands.default_permissions(administrator=True)

    @app_commands.choices(
        mencion=[
            app_commands.Choice(name="Ninguno", value="ninguno"),
            app_commands.Choice(name="@everyone", value="everyone"),
            app_commands.Choice(name="@here", value="here"),
            app_commands.Choice(name="Rol específico", value="rol"),
        ]
    )
    async def add_streamer(
        self,
        interaction: discord.Interaction,
        usuario: str,
        mensaje: str = "¡Ya está en vivo!",
        mencion: Optional[app_commands.Choice[str]] = None,
        rol1: Optional[discord.Role] = None,
        rol2: Optional[discord.Role] = None,
        rol3: Optional[discord.Role] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        mention_type = mencion.value if mencion else "ninguno"

        mention_role_ids: Optional[List[int]] = None
        if mention_type == "rol":
            provided_roles = [r for r in (rol1, rol2, rol3) if r is not None]

            if not provided_roles:
                await interaction.followup.send(
                    "Debes proporcionar al menos un rol si eliges `mencion: Rol específico`.",
                    ephemeral=True,
                )
                return

            seen = set()
            unique_roles = []
            for role in provided_roles:
                if role.id not in seen:
                    seen.add(role.id)
                    unique_roles.append(role)

            mention_role_ids = [r.id for r in unique_roles]

        try:
            cmd = AddStreamerCommand(
                guild_id=interaction.guild_id,
                username=usuario,
                custom_message=mensaje,
                mention_type=mention_type,
                mention_role_ids=mention_role_ids,
            )
            streamer = await self._add_uc.execute(cmd)

            embed = discord.Embed(
                title="Streamer añadido correctamente",
                color=discord.Color.green(),
            )
            embed.add_field(name="👤 Usuario", value=streamer.username, inline=True)
            embed.add_field(
                name="Mención",
                value=self._format_mention_info(mention_type, mention_role_ids, interaction.guild),
                inline=True,
            )
            embed.add_field(
                name="Mensaje",
                value=streamer.custom_message[:200],
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    @staticmethod
    def _format_mention_info(
        mention_type: str,
        role_ids: Optional[List[int]],
        guild: discord.Guild,
    ) -> str:
        if mention_type == "ninguno":
            return "Ninguna"
        if mention_type == "everyone":
            return "@everyone"
        if mention_type == "here":
            return "@here"
        if mention_type == "rol" and role_ids:
            mentions = []
            for rid in role_ids:
                role = guild.get_role(rid)
                mentions.append(role.mention if role else f"<@&{rid}>")
            return " ".join(mentions)
        return "Desconocido"

    # ----------- /eliminar -----------
    @app_commands.command(
        name="eliminar",
        description="Deja de monitorear a un streamer",
    )
    @app_commands.describe(usuario="Nombre de usuario de Twitch a eliminar")
    @app_commands.default_permissions(administrator=True)
    async def remove_streamer(
        self,
        interaction: discord.Interaction,
        usuario: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._remove_uc.execute(
                RemoveStreamerCommand(
                    guild_id=interaction.guild_id,
                    username=usuario,
                )
            )
            await interaction.followup.send(
                f"**{usuario}** eliminado del monitoreo.",
                ephemeral=True,
            )
        except DomainError as e:
            await interaction.followup.send(f"⚠️ {e}", ephemeral=True)

    # ----------- /listar -----------
    @app_commands.command(
        name="listar",
        description="Muestra los streamers que estás monitoreando",
    )
    async def list_streamers(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        streamers = await self._list_uc.execute(
            ListStreamersQuery(guild_id=interaction.guild_id)
        )

        if not streamers:
            await interaction.followup.send(
                "No hay streamers monitoreados. Usa `/añadir` para empezar.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📡 Streamers Monitoreados",
            color=discord.Color.purple(),
        )

        for s in streamers:
            status = "EN VIVO" if s.is_online else "Offline"
            mention_info = self._format_mention_info(
                s.mention_type, s.mention_role_ids, interaction.guild
            )
            embed.add_field(
                name=f"{s.username} — {status}",
                value=(
                    f"{s.custom_message[:80]}\n"
                    f"Mención: {mention_info}"
                ),
                inline=False,
            )

        embed.set_footer(text=f"Total: {len(streamers)} streamers")
        await interaction.followup.send(embed=embed, ephemeral=True)