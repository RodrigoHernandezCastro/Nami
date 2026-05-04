# src/presentation/discord_bot/cogs/admin_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from src.application.use_cases.set_guild_language import (
    SetGuildLanguageUseCase,
    SetGuildLanguageCommand,
)
from src.domain.exceptions.domain_exceptions import DomainError
from src.application.interfaces.translator import ITranslator
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
from src.presentation.discord_bot.command_localizer import CommandLocalizer
from src.presentation.discord_bot.discord_locale_map import expand_localizations


class AdminCog(commands.Cog):
    """
    Comandos administrativos del bot:
      • /language — cambia el idioma del bot en el servidor
      • /help     — sistema de ayuda con subcomandos por categoría

    NOTA importante: como `/help` es un Group declarado a nivel de clase
    (no instancia), no puede recibir el translator vía __init__. Por eso
    creamos el grupo en __init_subclass__-style: lo construimos en el
    constructor y lo asignamos al árbol del bot. Para eso usamos un
    Group con localizations construido programáticamente.
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
        self._loc = CommandLocalizer(translator)

        # ----- Grupo /help con localizations -----
        # Lo construimos aquí (no como atributo de clase) para tener
        # acceso al translator. Luego le añadimos los subcomandos.
        help_desc_loc = expand_localizations(
            translator.localizations("cmd.help.desc")
        )
        self.help_group = app_commands.Group(
            name="help",
            description=translator.t("cmd.help.desc", translator.DEFAULT_LANG),  # type: ignore[attr-defined]
            description_localizations=help_desc_loc or None,
        )
        self._register_help_subcommands()

        # Registramos el grupo en el árbol del bot.
        # (Los subcomandos ya están enganchados al grupo al definirlos.)
        bot.tree.add_command(self.help_group)

    # ------------------------------------------------------------------
    # /language
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        # Listener vacío para mantener el patrón. La carga real va por setup_hook.
        pass

    # discord.py exige que los slash commands sean métodos decorados.
    # Como el decorador necesita kwargs computados, los aplicamos al
    # importarse el cog generando un closure. El truco: definimos el
    # método con un decorador interno que aplique kwargs dinámicos
    # vía el descriptor app_commands.Command. Dado que esto añade
    # complejidad, optamos por una solución más simple: declarar el
    # método con kwargs estáticos en idioma por defecto y luego, tras
    # registrarse en el cog, sobrescribir name_localizations /
    # description_localizations vía atributos.

    @app_commands.command(name="language", description="Change the bot's language")
    @app_commands.describe(language="Language to use")
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

    async def cog_load(self) -> None:
        """
        Hook que llama discord.py al añadir el cog. Usamos esto para
        aplicar localizations dinámicas a los comandos del cog (no del
        Group, que ya las tiene desde __init__).
        """
        self._apply_localizations_to_language_cmd()

    def _apply_localizations_to_language_cmd(self) -> None:
        """Aplica name/desc/localizations al comando /language y a sus choices."""
        cmd = self.language_cmd  # type: ignore[assignment]
        # cmd es un app_commands.Command (descriptor). Sobrescribimos sus campos.
        kw = self._loc.command("cmd.language")
        cmd.name = kw["name"]
        cmd.description = kw["description"]
        if "name_localizations" in kw:
            cmd._locale_name = None  # reset por si discord.py lo cachea
            cmd.extras["name_localizations"] = kw["name_localizations"]
            # Asignación directa del dict para que la API de Discord lo reciba
            for locale, val in kw["name_localizations"].items():
                cmd.name_localizations[locale] = val
        if "description_localizations" in kw:
            for locale, val in kw["description_localizations"].items():
                cmd.description_localizations[locale] = val

        # Localizar el parámetro `language`
        for param in cmd.parameters:
            if param.name == "language":
                # Descripción del parámetro
                default_lang = self._translator.DEFAULT_LANG  # type: ignore[attr-defined]
                param.description = self._translator.t(
                    "cmd.language.param_lang", default_lang
                )
                desc_loc = expand_localizations(
                    self._translator.localizations("cmd.language.param_lang")
                )
                for locale, val in desc_loc.items():
                    param.description_localizations[locale] = val

                # Choices localizados (es/en/pl/ja)
                param.choices = [
                    self._loc.choice("es", "choice.lang.es"),
                    self._loc.choice("en", "choice.lang.en"),
                    self._loc.choice("pl", "choice.lang.pl"),
                    self._loc.choice("ja", "choice.lang.ja"),
                ]

    # ------------------------------------------------------------------
    # /help all, /help twitch, /help youtube, /help admin
    # ------------------------------------------------------------------
    def _register_help_subcommands(self) -> None:
        """Registra los subcomandos del grupo /help con sus localizations."""
        translator = self._translator
        default_lang = translator.DEFAULT_LANG  # type: ignore[attr-defined]
        i18n = self._i18n
        bot = self.bot

        def make_subcommand(name: str, desc_key: str, build_embed_fn):
            desc_loc = expand_localizations(translator.localizations(desc_key))
            command = app_commands.Command(
                name=name,
                description=translator.t(desc_key, default_lang),
                callback=build_embed_fn,
            )
            if desc_loc:
                for locale, val in desc_loc.items():
                    command.description_localizations[locale] = val
            return command

        async def help_all(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            lang = await i18n.get_lang(interaction.guild_id)
            t = translator.t
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

        async def help_twitch(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            lang = await i18n.get_lang(interaction.guild_id)
            t = translator.t
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

        async def help_youtube(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            lang = await i18n.get_lang(interaction.guild_id)
            t = translator.t
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

        async def help_admin(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            lang = await i18n.get_lang(interaction.guild_id)
            t = translator.t
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

        # Engancha cada subcomando al grupo
        self.help_group.add_command(
            make_subcommand("all", "cmd.help_all.desc", help_all)
        )
        self.help_group.add_command(
            make_subcommand("twitch", "cmd.help_twitch.desc", help_twitch)
        )
        self.help_group.add_command(
            make_subcommand("youtube", "cmd.help_youtube.desc", help_youtube)
        )
        self.help_group.add_command(
            make_subcommand("admin", "cmd.help_admin.desc", help_admin)
        )

    async def cog_unload(self) -> None:
        """Limpia el grupo de help del árbol al descargar el cog."""
        self.bot.tree.remove_command(self.help_group.name)