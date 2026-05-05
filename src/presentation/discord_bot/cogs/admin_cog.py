# src/presentation/discord_bot/cogs/admin_cog.py
"""
Cog de administración: `/language` y el grupo `/help`.

Igual que `monitor_cog.py` y `youtube_cog.py`, la localización de los
slash commands se delega 100% al `app_commands.Translator` registrado
en `bot.py` (`NamiAppTranslator`). Aquí solo declaramos las claves en
los decoradores con `locale_str(default_text, key="...")`.

Decisión: los nombres del grupo `help` y sus subcomandos (`all`,
`twitch`, `youtube`, `admin`) se mantienen en inglés en todos los
idiomas (las descripciones SÍ se localizan). Si en el futuro quieres
localizar también los nombres, basta con cambiar los strings por
`locale_str(...)` y añadir las claves correspondientes a los JSON.

Sobre el grupo `/help`:
- Lo declaramos como SUBCLASE de `app_commands.Group` con sus
  subcomandos como métodos decorados. Esta es la forma idiomática en
  discord.py 2.x. Los subcomandos comparten el `__init__` del grupo,
  donde guardamos las dependencias (translator, lang_resolver).
- Para que el grupo se registre en el árbol del bot al cargar el cog,
  lo declaramos como atributo de clase del cog (discord.py descubre
  los grupos por inspección al hacer `add_cog`). Pero como necesita
  dependencias, lo creamos en `__init__` y lo añadimos al árbol
  manualmente, removiéndolo en `cog_unload`.
"""
import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands
from typing import Optional

from src.application.use_cases.set_guild_language import (
    SetGuildLanguageUseCase,
    SetGuildLanguageCommand,
)
from src.domain.exceptions.domain_exceptions import DomainError
from src.application.interfaces.translator import ITranslator
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver


# ---------------------------------------------------------------------------
# Grupo /help como subclase de app_commands.Group
# ---------------------------------------------------------------------------
class HelpGroup(app_commands.Group):
    """
    Grupo `/help` con subcomandos `all`, `twitch`, `youtube`, `admin`.

    Recibe `translator` y `lang_resolver` por constructor para poder
    construir embeds traducidos en cada subcomando.
    """

    def __init__(
        self,
        translator: ITranslator,
        lang_resolver: GuildLanguageResolver,
    ) -> None:
        # `name` queda como string literal (sin localizar). `description`
        # va con locale_str para que el translator lo resuelva por idioma.
        super().__init__(
            name="help",
            description=_T("Show available commands", key="cmd.help.desc"),
        )
        self._t = translator
        self._i18n = lang_resolver

    @app_commands.command(
        name="all",
        description=_T("Show all bot commands", key="cmd.help_all.desc"),
    )
    async def help_all(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._t.t

        embed = discord.Embed(
            title=t("help.title", lang),
            description=t("help.description", lang),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name=t("help.twitch.title", lang),
            value=(
                f"{t('help.twitch.configure', lang)}\n\n"
                f"{t('help.twitch.add', lang)}\n\n"
                f"{t('help.twitch.remove', lang)}\n\n"
                f"{t('help.twitch.list', lang)}"
            ),
            inline=False,
        )
        embed.add_field(
            name=t("help.youtube.title", lang),
            value=(
                f"{t('help.youtube.configure', lang)}\n\n"
                f"{t('help.youtube.add', lang)}\n\n"
                f"{t('help.youtube.remove', lang)}\n\n"
                f"{t('help.youtube.list', lang)}"
            ),
            inline=False,
        )
        embed.add_field(
            name=t("help.admin.title", lang),
            value=(
                f"{t('help.admin.language', lang)}\n\n"
                f"{t('help.admin.help', lang)}"
            ),
            inline=False,
        )
        embed.set_footer(text=t("help.footer", lang))
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="twitch",
        description=_T("Twitch commands", key="cmd.help_twitch.desc"),
    )
    async def help_twitch(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._t.t

        embed = discord.Embed(
            title=t("help.twitch.title", lang),
            color=discord.Color.purple(),
            description=(
                f"{t('help.twitch.configure', lang)}\n\n"
                f"{t('help.twitch.add', lang)}\n\n"
                f"{t('help.twitch.remove', lang)}\n\n"
                f"{t('help.twitch.list', lang)}"
            ),
        )
        embed.set_footer(text=t("help.footer", lang))
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="youtube",
        description=_T("YouTube commands", key="cmd.help_youtube.desc"),
    )
    async def help_youtube(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._t.t

        embed = discord.Embed(
            title=t("help.youtube.title", lang),
            color=discord.Color.red(),
            description=(
                f"{t('help.youtube.configure', lang)}\n\n"
                f"{t('help.youtube.add', lang)}\n\n"
                f"{t('help.youtube.remove', lang)}\n\n"
                f"{t('help.youtube.list', lang)}"
            ),
        )
        embed.set_footer(text=t("help.footer", lang))
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="admin",
        description=_T("Admin commands", key="cmd.help_admin.desc"),
    )
    async def help_admin(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        lang = await self._i18n.get_lang(interaction.guild_id)
        t = self._t.t

        embed = discord.Embed(
            title=t("help.admin.title", lang),
            color=discord.Color.blurple(),
            description=(
                f"{t('help.admin.language', lang)}\n\n"
                f"{t('help.admin.help', lang)}"
            ),
        )
        embed.set_footer(text=t("help.footer", lang))
        await interaction.followup.send(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# AdminCog
# ---------------------------------------------------------------------------
class AdminCog(commands.Cog):
    """
    Comandos administrativos:
      • /language — cambia el idioma del bot en el servidor
      • /help (grupo con subcomandos) — sistema de ayuda
    """

    def __init__(
        self,
        bot: commands.Bot,
        set_language_uc: SetGuildLanguageUseCase,
        lang_resolver: GuildLanguageResolver,
        translator: ITranslator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self._set_language_uc = set_language_uc
        self._i18n = lang_resolver
        self._translator = translator

        # Construimos el grupo con sus dependencias y lo añadimos al
        # árbol del bot. Lo guardamos como atributo para poder removerlo
        # en cog_unload.
        self.help_group = HelpGroup(
            translator=translator,
            lang_resolver=lang_resolver,
        )
        bot.tree.add_command(self.help_group)

    async def cog_unload(self) -> None:
        """Limpia el grupo /help del árbol al descargar el cog."""
        self.bot.tree.remove_command(self.help_group.name)

    # ----------- /language -----------
    @app_commands.command(
        name=_T("language", key="cmd.language.name"),
        description=_T("Change the bot's language", key="cmd.language.desc"),
    )
    @app_commands.describe(
        language=_T("Language to use", key="cmd.language.param_lang")
    )
    @app_commands.choices(
        language=[
            app_commands.Choice(
                name=_T("Spanish", key="choice.lang.es"), value="es"
            ),
            app_commands.Choice(
                name=_T("English", key="choice.lang.en"), value="en"
            ),
            app_commands.Choice(
                name=_T("Polish", key="choice.lang.pl"), value="pl"
            ),
            app_commands.Choice(
                name=_T("Japanese", key="choice.lang.ja"), value="ja"
            ),
        ]
    )
    @app_commands.default_permissions(administrator=True)
    async def language_cmd(
        self,
        interaction: discord.Interaction,
        language: app_commands.Choice[str],
    ) -> None:
        """Cambia el idioma del servidor. Solo administradores."""
        await interaction.response.defer(ephemeral=True)

        try:
            await self._set_language_uc.execute(
                SetGuildLanguageCommand(
                    guild_id=interaction.guild_id,
                    language=language.value,
                )
            )
            self._i18n.invalidate(interaction.guild_id)

            lang_name_key = f"language.choice_{language.value}"
            lang_name = await self._i18n.t(lang_name_key, interaction.guild_id)

            msg = await self._i18n.t(
                "language.changed",
                interaction.guild_id,
                lang_name=lang_name,
            )
            await interaction.followup.send(msg, ephemeral=True)

        except DomainError as e:
            warning = await self._i18n.t(
                "common.warning", interaction.guild_id, message=str(e)
            )
            await interaction.followup.send(warning, ephemeral=True)