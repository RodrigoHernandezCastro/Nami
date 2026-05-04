# src/presentation/discord_bot/command_localizer.py
"""
Helper que produce los kwargs necesarios para los decoradores
@app_commands.command y @app_commands.describe con localizations.

Uso típico desde un Cog:

    loc = CommandLocalizer(translator)
    kwargs = loc.command("cmd.add")     # name, description, name_localizations, description_localizations
    @app_commands.command(**kwargs)
    async def add(...): ...

Para parámetros (describe):
    desc_kwargs = loc.describe(
        usuario="cmd.add.param_user",
        mensaje="cmd.add.param_message",
    )
    @app_commands.describe(**desc_kwargs)  # esto solo da el texto en el idioma por defecto

Discord también permite localizar las descripciones de parámetros vía
`Parameter.description_localizations`, pero eso requiere usar el modelo
de Transformers o app_commands.Range con descripciones por separado y
queda fuera del alcance aquí: las descripciones de parámetros quedan
solo en el idioma por defecto (en).
"""
from typing import Dict, Any
import discord
from discord import app_commands

from src.application.interfaces.translator import ITranslator
from src.presentation.discord_bot.discord_locale_map import expand_localizations


class CommandLocalizer:
    def __init__(self, translator: ITranslator) -> None:
        self._t = translator

    # ------------------------------------------------------------------
    # Construcción de kwargs para @app_commands.command(...)
    # ------------------------------------------------------------------
    def command(self, base_key: str, *, with_name: bool = True) -> Dict[str, Any]:
        """
        Devuelve dict con `name`, `description`, `name_localizations`,
        `description_localizations` listos para `@app_commands.command(**kwargs)`.

        `base_key` es el prefijo de las claves en los JSON. Por ejemplo
        "cmd.add" busca:
          - cmd.add.name
          - cmd.add.desc
        en cada idioma.

        Si `with_name=False` se omite name_localizations (útil para
        subcomandos de un Group, donde el name_localizations va en el
        decorador del subcomando pero name viene fijo).
        """
        default = self._t.DEFAULT_LANG  # type: ignore[attr-defined]
        kwargs: Dict[str, Any] = {
            "name": self._t.t(f"{base_key}.name", default),
            "description": self._t.t(f"{base_key}.desc", default),
        }

        desc_loc = expand_localizations(self._t.localizations(f"{base_key}.desc"))
        if desc_loc:
            kwargs["description_localizations"] = desc_loc

        if with_name:
            name_loc_short = self._t.localizations(f"{base_key}.name")
            # Discord exige que los nombres localizados cumplan el regex
            # de nombres de comandos: lowercase, sin espacios, etc.
            # Aquí confiamos en que los JSON ya los cumplen (validado en CI).
            name_loc = expand_localizations(name_loc_short)
            if name_loc:
                kwargs["name_localizations"] = name_loc

        return kwargs

    # ------------------------------------------------------------------
    # describe(...) NO acepta diccionario ya formado: necesita kwargs
    # con el nombre exacto del parámetro. Lo hace el caller.
    # Esta función solo da el texto en el idioma por defecto.
    # ------------------------------------------------------------------
    def describe_text(self, key: str) -> str:
        """Texto de descripción de parámetro en el idioma por defecto."""
        return self._t.t(key, self._t.DEFAULT_LANG)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Choices localizados
    # ------------------------------------------------------------------
    def choice(
        self,
        value: str,
        name_key: str,
    ) -> app_commands.Choice[str]:
        """
        Crea un app_commands.Choice con name en idioma por defecto y
        name_localizations en los demás.
        """
        default = self._t.DEFAULT_LANG  # type: ignore[attr-defined]
        choice = app_commands.Choice(
            name=self._t.t(name_key, default),
            value=value,
        )
        # discord.py 2.4+ soporta name_localizations en Choice vía
        # asignación directa al atributo (no expuesto en el constructor
        # para mantener compatibilidad). Si tu versión no lo soporta,
        # los choices quedarán solo en el idioma por defecto y eso es OK.
        loc = expand_localizations(self._t.localizations(name_key))
        if loc:
            try:
                choice.name_localizations = loc
            except (AttributeError, TypeError):
                pass
        return choice