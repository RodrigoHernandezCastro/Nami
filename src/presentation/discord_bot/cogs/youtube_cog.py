# src/presentation/discord_bot/cogs/youtube_cog.py
"""
Cog de monitoreo de YouTube.

La localización de comandos slash se delega al `app_commands.Translator`
registrado en `bot.py`. Cada `locale_str(...)` recibe:
  - el texto por defecto (en inglés) como primer argumento. Para los
    `name=` debe ser un nombre slash válido.
  - `key=` con la clave del JSON, que `NamiAppTranslator` usará para
    resolver las traducciones a otros idiomas.
"""
import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
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
from src.application.use_cases.update_youtube_channel import (
    UpdateYouTubeChannelUseCase, UpdateYouTubeChannelCommand,
)
from src.application.use_cases.configure_youtube_live_settings import (
    ConfigureYouTubeLiveSettingsUseCase, ConfigureYouTubeLiveSettingsCommand,
)
from src.application.interfaces.translator import ITranslator
from src.domain.exceptions.domain_exceptions import DomainError, ChannelNotFoundError
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver


class YouTubeCog(commands.Cog):
    """Comandos slash para gestionar canales de YouTube."""

    def __init__(
        self,
        bot: commands.Bot,
        add_youtube_uc: AddYouTubeChannelUseCase,
        remove_youtube_uc: RemoveYouTubeChannelUseCase,
        list_youtube_uc: ListYouTubeChannelsUseCase,
        update_youtube_uc: UpdateYouTubeChannelUseCase,
        configure_youtube_live_uc: ConfigureYouTubeLiveSettingsUseCase,
        lang_resolver: GuildLanguageResolver,
        translator: ITranslator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self._add_uc = add_youtube_uc
        self._remove_uc = remove_youtube_uc
        self._list_uc = list_youtube_uc
        self._update_uc = update_youtube_uc
        self._configure_live_uc = configure_youtube_live_uc
        self._i18n = lang_resolver
        self._translator = translator

    # ----------- /add-youtube -----------
    @app_commands.command(
        name=_T("add-youtube", key="cmd.add_youtube.name"),
        description=_T(
            "Add a YouTube channel (@username)", key="cmd.add_youtube.desc"
        ),
    )
    @app_commands.describe(
        user=_T(
            "Channel name (@IlloJuan_, @HakosBaelz)",
            key="cmd.add_youtube.param_user",
        ),
        message=_T(
            "Custom message when announcing a new video",
            key="cmd.add_youtube.param_message",
        ),
        mention=_T(
            "Mention type when announcing", key="cmd.add_youtube.param_mention"
        ),
        role1=_T(
            "First role to mention (only if mention='role')",
            key="cmd.add_youtube.param_role1",
        ),
        role2=_T("Second role (optional)", key="cmd.add_youtube.param_role2"),
        role3=_T("Third role (optional)", key="cmd.add_youtube.param_role3"),
    )
    @app_commands.choices(
        mention=[
            app_commands.Choice(
                name=_T("None", key="choice.mention.none"),
                value="ninguno",
            ),
            app_commands.Choice(
                name=_T("@everyone", key="choice.mention.everyone"),
                value="everyone",
            ),
            app_commands.Choice(
                name=_T("@here", key="choice.mention.here"),
                value="here",
            ),
            app_commands.Choice(
                name=_T("Specific role", key="choice.mention.role"),
                value="rol",
            ),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def add_youtube(
        self,
        interaction: discord.Interaction,
        user: str,
        message: str = "New YouTube video!",
        mention: Optional[app_commands.Choice[str]] = None,
        role1: Optional[discord.Role] = None,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        mention_type = mention.value if mention else "ninguno"
        mention_role_ids = None
        if mention_type == "rol":
            provided_roles = [r for r in (role1, role2, role3) if r is not None]
            if not provided_roles:
                msg = await self._i18n.t("youtube.role_required", interaction.guild_id)
                await interaction.followup.send(msg, ephemeral=True)
                return
            mention_role_ids = [r.id for r in provided_roles]

        try:
            channel_id = await self._add_uc.resolve_username(user)

            cmd = AddYouTubeCommand(
                guild_id=interaction.guild_id,
                channel_id=channel_id,
                custom_message=message,
                mention_type=mention_type,
                mention_role_ids=mention_role_ids,
            )
            channel = await self._add_uc.execute(cmd)

            lang = await self._i18n.get_lang(interaction.guild_id)
            t = self._translator.t

            embed = discord.Embed(
                title=t("youtube.added.title", lang),
                color=discord.Color.red(),
            )
            embed.add_field(
                name=t("youtube.added.field_channel", lang),
                value=channel.display_name,
                inline=True,
            )
            embed.add_field(
                name=t("youtube.added.field_id", lang),
                value=f"`{channel.channel_name}`",
                inline=True,
            )
            embed.add_field(
                name=t("youtube.added.field_mention", lang),
                value=await self._format_mention(
                    mention_type, mention_role_ids, interaction.guild, interaction.guild_id
                ),
                inline=True,
            )
            embed.add_field(
                name=t("youtube.added.field_message", lang),
                value=channel.custom_message,
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /edit-youtube -----------
    @app_commands.command(
        name=_T("edit-youtube", key="cmd.edit_youtube.name"),
        description=_T(
            "Edit a monitored YouTube channel's video settings",
            key="cmd.edit_youtube.desc",
        ),
    )
    @app_commands.describe(
        user=_T(
            "Channel name (@IlloJuan_) or direct ID (UCxxxx)",
            key="cmd.edit_youtube.param_user",
        ),
        message=_T(
            "New custom message for videos",
            key="cmd.edit_youtube.param_message",
        ),
        mention=_T(
            "New mention type for videos",
            key="cmd.edit_youtube.param_mention",
        ),
        role1=_T(
            "First role to mention (only if mention='role')",
            key="cmd.edit_youtube.param_role1",
        ),
        role2=_T("Second role (optional)", key="cmd.edit_youtube.param_role2"),
        role3=_T("Third role (optional)", key="cmd.edit_youtube.param_role3"),
    )
    @app_commands.choices(
        mention=[
            app_commands.Choice(
                name=_T("None", key="choice.mention.none"),
                value="ninguno",
            ),
            app_commands.Choice(
                name=_T("@everyone", key="choice.mention.everyone"),
                value="everyone",
            ),
            app_commands.Choice(
                name=_T("@here", key="choice.mention.here"),
                value="here",
            ),
            app_commands.Choice(
                name=_T("Specific role", key="choice.mention.role"),
                value="rol",
            ),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def edit_youtube(
        self,
        interaction: discord.Interaction,
        user: str,
        message: Optional[str] = None,
        mention: Optional[app_commands.Choice[str]] = None,
        role1: Optional[discord.Role] = None,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if user.startswith("UC") and not user.startswith("@"):
            channel_id = user
        else:
            try:
                channel_id = await self._add_uc.resolve_username(user)
            except ChannelNotFoundError:
                channel_id = user

        channels = await self._list_uc.execute(
            ListYouTubeQuery(guild_id=interaction.guild_id)
        )
        existing = [c for c in channels if c.channel_id == channel_id]
        if not existing:
            msg = await self._i18n.t(
                "youtube.not_found", interaction.guild_id, usuario=user
            )
            await interaction.followup.send(msg, ephemeral=True)
            return

        current = existing[0]
        mention_type = mention.value if mention else current.mention_type

        mention_role_ids = current.mention_role_ids
        if mention_type == "rol":
            provided_roles = [r for r in (role1, role2, role3) if r is not None]
            if provided_roles:
                mention_role_ids = [r.id for r in provided_roles]
            elif not current.mention_role_ids:
                msg = await self._i18n.t("youtube.role_required", interaction.guild_id)
                await interaction.followup.send(msg, ephemeral=True)
                return
        elif mention is not None:
            mention_role_ids = None

        new_message = message if message is not None else current.custom_message

        try:
            await self._update_uc.execute(
                UpdateYouTubeChannelCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel_id,
                    custom_message=new_message,
                    mention_type=mention_type,
                    mention_role_ids=mention_role_ids,
                )
            )
            msg = await self._i18n.t(
                "youtube.edited", interaction.guild_id, usuario=user
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /add-youtube-live -----------
    @app_commands.command(
        name=_T("add-youtube-live", key="cmd.add_youtube_live.name"),
        description=_T(
            "Set live stream settings for a YouTube channel",
            key="cmd.add_youtube_live.desc",
        ),
    )
    @app_commands.describe(
        user=_T(
            "Channel name (@IlloJuan_) or direct ID (UCxxxx)",
            key="cmd.add_youtube_live.param_user",
        ),
        live_message=_T(
            "Custom message for live streams",
            key="cmd.add_youtube_live.param_live_message",
        ),
        live_mention=_T(
            "Mention type for live streams",
            key="cmd.add_youtube_live.param_live_mention",
        ),
        live_role1=_T(
            "First role for live (only if live_mention='role')",
            key="cmd.add_youtube_live.param_live_role1",
        ),
        live_role2=_T(
            "Second role for live (optional)",
            key="cmd.add_youtube_live.param_live_role2",
        ),
        live_role3=_T(
            "Third role for live (optional)",
            key="cmd.add_youtube_live.param_live_role3",
        ),
    )
    @app_commands.choices(
        live_mention=[
            app_commands.Choice(
                name=_T("None", key="choice.mention.none"),
                value="ninguno",
            ),
            app_commands.Choice(
                name=_T("@everyone", key="choice.mention.everyone"),
                value="everyone",
            ),
            app_commands.Choice(
                name=_T("@here", key="choice.mention.here"),
                value="here",
            ),
            app_commands.Choice(
                name=_T("Specific role", key="choice.mention.role"),
                value="rol",
            ),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def add_youtube_live(
        self,
        interaction: discord.Interaction,
        user: str,
        live_message: Optional[str] = None,
        live_mention: Optional[app_commands.Choice[str]] = None,
        live_role1: Optional[discord.Role] = None,
        live_role2: Optional[discord.Role] = None,
        live_role3: Optional[discord.Role] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if user.startswith("UC") and not user.startswith("@"):
            channel_id = user
        else:
            try:
                channel_id = await self._add_uc.resolve_username(user)
            except ChannelNotFoundError:
                channel_id = user

        live_mention_type = live_mention.value if live_mention else None
        live_mention_role_ids = None
        if live_mention_type == "rol":
            provided_roles = [r for r in (live_role1, live_role2, live_role3) if r is not None]
            if not provided_roles:
                msg = await self._i18n.t("youtube.role_required", interaction.guild_id)
                await interaction.followup.send(msg, ephemeral=True)
                return
            live_mention_role_ids = [r.id for r in provided_roles]

        try:
            await self._configure_live_uc.execute(
                ConfigureYouTubeLiveSettingsCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel_id,
                    live_custom_message=live_message,
                    live_mention_type=live_mention_type,
                    live_mention_role_ids=live_mention_role_ids,
                )
            )
            msg = await self._i18n.t(
                "youtube.live_configured", interaction.guild_id, usuario=user
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /list-youtube -----------
    @app_commands.command(
        name=_T("list-youtube", key="cmd.list_youtube.name"),
        description=_T(
            "List monitored YouTube channels", key="cmd.list_youtube.desc"
        ),
    )
    @app_commands.default_permissions(administrator=True)
    async def list_youtube(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        channels = await self._list_uc.execute(
            ListYouTubeQuery(guild_id=interaction.guild_id)
        )

        if not channels:
            msg = await self._i18n.t("youtube.list.empty", interaction.guild_id)
            await interaction.followup.send(msg, ephemeral=True)
            return

        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._translator.t

        embed = discord.Embed(
            title=t("youtube.list.title", lang),
            color=discord.Color.red(),
        )
        for c in channels:
            embed.add_field(
                name=c.display_name,
                value=c.custom_message[:80],
                inline=False,
            )
        embed.set_footer(text=t("youtube.list.footer", lang, count=len(channels)))
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ----------- /remove-youtube -----------
    @app_commands.command(
        name=_T("remove-youtube", key="cmd.remove_youtube.name"),
        description=_T(
            "Stop monitoring a YouTube channel (@username or ID)",
            key="cmd.remove_youtube.desc",
        ),
    )
    @app_commands.describe(
        user=_T(
            "Channel name (@IlloJuan_) or direct ID (UCxxxx)",
            key="cmd.remove_youtube.param_user",
        )
    )
    @app_commands.default_permissions(administrator=True)
    async def remove_youtube(
        self,
        interaction: discord.Interaction,
        user: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            if user.startswith("UC") and not user.startswith("@"):
                channel_id = user
            else:
                try:
                    channel_id = await self._add_uc.resolve_username(user)
                except ChannelNotFoundError:
                    channel_id = user

            await self._remove_uc.execute(
                RemoveYouTubeCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel_id,
                )
            )
            msg = await self._i18n.t(
                "youtube.removed", interaction.guild_id, usuario=user
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- helpers -----------
    async def _format_mention(
        self,
        mention_type: str,
        role_ids: Optional[List[int]],
        guild: discord.Guild,
        guild_id: Optional[int],
    ) -> str:
        if mention_type == "ninguno":
            return await self._i18n.t("mention.none", guild_id)
        if mention_type == "everyone":
            return await self._i18n.t("mention.everyone", guild_id)
        if mention_type == "here":
            return await self._i18n.t("mention.here", guild_id)
        if mention_type == "rol" and role_ids:
            mentions = []
            for rid in role_ids:
                role = guild.get_role(rid)
                mentions.append(role.mention if role else f"<@&{rid}>")
            if mentions:
                return " ".join(mentions)
            return await self._i18n.t("mention.role_not_found", guild_id)
        return await self._i18n.t("mention.unknown", guild_id)

    async def _send_warning(self, interaction: discord.Interaction, message: str) -> None:
        text = await self._i18n.t(
            "common.warning", interaction.guild_id, message=message
        )
        await interaction.followup.send(text, ephemeral=True)