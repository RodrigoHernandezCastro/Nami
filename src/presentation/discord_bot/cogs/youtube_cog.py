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
from src.application.interfaces.translator import ITranslator
from src.domain.exceptions.domain_exceptions import DomainError, ChannelNotFoundError
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
from src.presentation.discord_bot.command_localizer import CommandLocalizer
from src.presentation.discord_bot.discord_locale_map import expand_localizations


class YouTubeCog(commands.Cog):
    """Comandos slash para gestionar canales de YouTube."""

    def __init__(
        self,
        bot: commands.Bot,
        add_youtube_uc: AddYouTubeChannelUseCase,
        remove_youtube_uc: RemoveYouTubeChannelUseCase,
        list_youtube_uc: ListYouTubeChannelsUseCase,
        lang_resolver: GuildLanguageResolver,
        translator: ITranslator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self._add_uc = add_youtube_uc
        self._remove_uc = remove_youtube_uc
        self._list_uc = list_youtube_uc
        self._i18n = lang_resolver
        self._translator = translator
        self._loc = CommandLocalizer(translator)

    # ----------- /add-youtube -----------
    @app_commands.command(name="add-youtube", description="Add a YouTube channel (@username)")
    @app_commands.describe(
        user="Channel name (@username)",
        message="Custom announcement message",
        mention="Mention type",
        role1="First role",
        role2="Second role",
        role3="Third role",
    )
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

    # ----------- /list-youtube -----------
    @app_commands.command(name="list-youtube", description="List monitored YouTube channels")
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
    @app_commands.command(name="remove-youtube", description="Stop monitoring a YouTube channel")
    @app_commands.describe(user="Channel @username or direct ID (UCxxxx)")
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
            mentions = [
                guild.get_role(rid).mention
                for rid in role_ids
                if guild.get_role(rid)
            ]
            if mentions:
                return " ".join(mentions)
            return await self._i18n.t("mention.role_not_found", guild_id)
        return await self._i18n.t("mention.unknown", guild_id)

    async def _send_warning(self, interaction: discord.Interaction, message: str) -> None:
        text = await self._i18n.t(
            "common.warning", interaction.guild_id, message=message
        )
        await interaction.followup.send(text, ephemeral=True)

    # ----------- aplicar localizations al cargar -----------
    async def cog_load(self) -> None:
        self._localize(
            self.add_youtube,
            "cmd.add_youtube",
            params={
                "user": "cmd.add_youtube.param_user",
                "message": "cmd.add_youtube.param_message",
                "mention": "cmd.add_youtube.param_mention",
                "role1": "cmd.add_youtube.param_role1",
                "role2": "cmd.add_youtube.param_role2",
                "role3": "cmd.add_youtube.param_role3",
            },
            choices={
                "mention": [
                    ("ninguno", "choice.mention.none"),
                    ("everyone", "choice.mention.everyone"),
                    ("here", "choice.mention.here"),
                    ("rol", "choice.mention.role"),
                ],
            },
        )
        self._localize(
            self.remove_youtube,
            "cmd.remove_youtube",
            params={"user": "cmd.remove_youtube.param_user"},
        )
        self._localize(self.list_youtube, "cmd.list_youtube")

    def _localize(
        self,
        cmd: app_commands.Command,
        base_key: str,
        params: Optional[dict] = None,
        choices: Optional[dict] = None,
    ) -> None:
        """Idéntico al de MonitorCog (candidato a extraer a un mixin compartido)."""
        kw = self._loc.command(base_key)
        cmd.name = kw["name"]
        cmd.description = kw["description"]
        if "name_localizations" in kw:
            for locale, val in kw["name_localizations"].items():
                cmd.name_localizations[locale] = val
        if "description_localizations" in kw:
            for locale, val in kw["description_localizations"].items():
                cmd.description_localizations[locale] = val

        if params:
            for param in cmd.parameters:
                key = params.get(param.name)
                if not key:
                    continue
                default = self._translator.DEFAULT_LANG  # type: ignore[attr-defined]
                param.description = self._translator.t(key, default)
                desc_loc = expand_localizations(self._translator.localizations(key))
                for locale, val in desc_loc.items():
                    param.description_localizations[locale] = val

        if choices:
            for param in cmd.parameters:
                if param.name in choices:
                    param.choices = [
                        self._loc.choice(value, name_key)
                        for (value, name_key) in choices[param.name]
                    ]