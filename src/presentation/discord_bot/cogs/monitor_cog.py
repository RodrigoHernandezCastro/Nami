# src/presentation/discord_bot/cogs/monitor_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

import random

from src.application.use_cases.add_streamer import AddStreamerUseCase, AddStreamerCommand
from src.application.use_cases.remove_streamer import RemoveStreamerUseCase, RemoveStreamerCommand
from src.application.use_cases.list_streamers import ListStreamersUseCase, ListStreamersQuery
from src.application.use_cases.configure_channel import ConfigureChannelUseCase, ConfigureChannelCommand
from src.application.use_cases.configure_channel_youtube import (
    ConfigureChannelYouTubeUseCase, ConfigureChannelYouTubeCommand,
)
from src.application.interfaces.translator import ITranslator
from src.domain.exceptions.domain_exceptions import DomainError
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
from src.presentation.discord_bot.command_localizer import CommandLocalizer
from src.presentation.discord_bot.discord_locale_map import expand_localizations


class MonitorCog(commands.Cog):
    """Comandos slash para gestionar el monitoreo de streamers de Twitch."""

    def __init__(
        self,
        bot: commands.Bot,
        add_streamer_uc: AddStreamerUseCase,
        remove_streamer_uc: RemoveStreamerUseCase,
        list_streamers_uc: ListStreamersUseCase,
        configure_channel_uc: ConfigureChannelUseCase,
        configure_youtube_uc: ConfigureChannelYouTubeUseCase,
        lang_resolver: GuildLanguageResolver,
        translator: ITranslator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self._add_uc = add_streamer_uc
        self._remove_uc = remove_streamer_uc
        self._list_uc = list_streamers_uc
        self._configure_uc = configure_channel_uc
        self._configure_youtube_uc = configure_youtube_uc
        self._i18n = lang_resolver
        self._translator = translator
        self._loc = CommandLocalizer(translator)

    # ----------- /configure -----------
    @app_commands.command(name="configure", description="Set the channel where live streams are announced")
    @app_commands.describe(channel="Channel where live stream announcements will be posted")
    @app_commands.default_permissions(administrator=True)
    async def configure(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._configure_uc.execute(
                ConfigureChannelCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel.id,
                )
            )
            msg = await self._i18n.t(
                "configure.twitch.success",
                interaction.guild_id,
                channel_mention=channel.mention,
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /configure-youtube -----------
    @app_commands.command(name="configure-youtube", description="Set the channel where YouTube videos are posted")
    @app_commands.describe(channel="Channel where YouTube videos will be posted")
    @app_commands.default_permissions(administrator=True)
    async def configure_youtube(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._configure_youtube_uc.execute(
                ConfigureChannelYouTubeCommand(
                    guild_id=interaction.guild_id,
                    channel_id=channel.id,
                )
            )
            msg = await self._i18n.t(
                "configure.youtube.success",
                interaction.guild_id,
                channel_mention=channel.mention,
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /add -----------
    @app_commands.command(name="add", description="Add a Twitch streamer to monitor")
    @app_commands.describe(
        user="Twitch username",
        message="Custom announcement message",
        mention="Mention type",
        role1="First role",
        role2="Second role",
        role3="Third role",
    )
    @app_commands.default_permissions(administrator=True)
    async def add_streamer(
        self,
        interaction: discord.Interaction,
        user: str,
        message: str = "Now live!",
        mention: Optional[app_commands.Choice[str]] = None,
        role1: Optional[discord.Role] = None,
        role2: Optional[discord.Role] = None,
        role3: Optional[discord.Role] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        mention_type = mention.value if mention else "ninguno"

        mention_role_ids: Optional[List[int]] = None
        if mention_type == "rol":
            provided_roles = [r for r in (role1, role2, role3) if r is not None]

            if not provided_roles:
                msg = await self._i18n.t(
                    "streamer.role_required", interaction.guild_id
                )
                await interaction.followup.send(msg, ephemeral=True)
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
                username=user,
                custom_message=message,
                mention_type=mention_type,
                mention_role_ids=mention_role_ids,
            )
            streamer = await self._add_uc.execute(cmd)

            lang = await self._i18n.get_lang(interaction.guild_id)
            t = self._translator.t

            embed = discord.Embed(
                title=t("streamer.added.title", lang),
                color=discord.Color.green(),
            )
            embed.add_field(
                name=t("streamer.added.field_user", lang),
                value=streamer.username,
                inline=True,
            )
            embed.add_field(
                name=t("streamer.added.field_mention", lang),
                value=await self._format_mention_info(
                    mention_type, mention_role_ids, interaction.guild, interaction.guild_id
                ),
                inline=True,
            )
            embed.add_field(
                name=t("streamer.added.field_message", lang),
                value=streamer.custom_message[:200],
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /remove -----------
    @app_commands.command(name="remove", description="Stop monitoring a streamer")
    @app_commands.describe(user="Twitch username to remove")
    @app_commands.default_permissions(administrator=True)
    async def remove_streamer(
        self,
        interaction: discord.Interaction,
        user: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._remove_uc.execute(
                RemoveStreamerCommand(
                    guild_id=interaction.guild_id,
                    username=user,
                )
            )
            msg = await self._i18n.t(
                "streamer.removed", interaction.guild_id, username=user
            )
            await interaction.followup.send(msg, ephemeral=True)
        except DomainError as e:
            await self._send_warning(interaction, str(e))

    # ----------- /list -----------
    @app_commands.command(name="list", description="Show monitored streamers")
    async def list_streamers(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        streamers = await self._list_uc.execute(
            ListStreamersQuery(guild_id=interaction.guild_id)
        )

        if not streamers:
            msg = await self._i18n.t("streamer.list.empty", interaction.guild_id)
            await interaction.followup.send(msg, ephemeral=True)
            return

        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._translator.t

        embed = discord.Embed(
            title=t("streamer.list.title", lang),
            color=discord.Color.purple(),
        )

        for s in streamers:
            status = (
                t("streamer.list.status_online", lang)
                if s.is_online
                else t("streamer.list.status_offline", lang)
            )
            mention_info = await self._format_mention_info(
                s.mention_type, s.mention_role_ids, interaction.guild, interaction.guild_id
            )
            mention_label = t("streamer.list.mention_label", lang)
            embed.add_field(
                name=f"{s.username} — {status}",
                value=(
                    f"{s.custom_message[:80]}\n"
                    f"{mention_label}: {mention_info}"
                ),
                inline=False,
            )

        embed.set_footer(text=t("streamer.list.footer", lang, count=len(streamers)))
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ----------- helpers -----------
    async def _format_mention_info(
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
            return " ".join(mentions)
        return await self._i18n.t("mention.unknown", guild_id)

    async def _send_warning(self, interaction: discord.Interaction, message: str) -> None:
        text = await self._i18n.t(
            "common.warning", interaction.guild_id, message=message
        )
        await interaction.followup.send(text, ephemeral=True)

    # ----------- aplicar localizations al cargar -----------
    async def cog_load(self) -> None:
        """Aplica name/desc/localizations a todos los comandos del cog."""
        self._localize(self.configure, "cmd.configure", params={"channel": "cmd.configure.param_channel"})
        self._localize(self.configure_youtube, "cmd.configure_youtube", params={"channel": "cmd.configure_youtube.param_channel"})
        self._localize(
            self.add_streamer,
            "cmd.add",
            params={
                "user": "cmd.add.param_user",
                "message": "cmd.add.param_message",
                "mention": "cmd.add.param_mention",
                "role1": "cmd.add.param_role1",
                "role2": "cmd.add.param_role2",
                "role3": "cmd.add.param_role3",
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
        self._localize(self.remove_streamer, "cmd.remove", params={"user": "cmd.remove.param_user"})
        self._localize(self.list_streamers, "cmd.list")

    def _localize(
        self,
        cmd: app_commands.Command,
        base_key: str,
        params: Optional[dict] = None,
        choices: Optional[dict] = None,
    ) -> None:
        """Aplica name, description y todas las localizations a un comando."""
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

    # ----------- !jankenpon (sin traducir) -----------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot conectado como {self.bot.user} (ID: {self.bot.user.id})")
        print("MonitorCog listo.")

    @commands.command(name="jankenpon")
    async def jankenpon(self, ctx, eleccion: str):
        eleccion = eleccion.lower()
        choices = ["piedra", "papel", "tijera"]
        bot_choice = random.choice(choices)

        if eleccion not in choices:
            await ctx.reply("¡Debes elegir piedra, papel o tijera!")
            return

        wins_against = {"piedra": "tijera", "papel": "piedra", "tijera": "papel"}

        if eleccion == bot_choice:
            resultado = "¡Empate!"
        elif wins_against[eleccion] == bot_choice:
            resultado = "¡Ganaste!"
        else:
            resultado = "¡Perdiste!"

        await ctx.reply(f"Yo elegí **{bot_choice}**. {resultado}")