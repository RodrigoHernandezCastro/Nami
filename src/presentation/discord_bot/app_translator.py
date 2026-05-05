# src/presentation/discord_bot/app_translator.py
"""
Translator oficial de discord.py (`app_commands.Translator`) que delega en
nuestro `ITranslator` (JSONTranslator).

Funcionamiento:
- En cada decorador usamos `locale_str(default_text, key="cmd.algo.name")`.
- `default_text` es el texto en inglés (idioma por defecto). Para
  nombres de comando DEBE cumplir el regex de Discord
  (lowercase, dígitos, '-', '_', máximo 32 caracteres).
- `key` es la clave que usaremos para buscar las traducciones en los
  JSON. Va en `extras` y NO la valida Discord.
- discord.py llama a `translate(string, locale, context)` durante
  `tree.sync()`. Aquí sacamos `string.extras["key"]`, miramos el
  `discord.Locale`, mapeamos a nuestro código corto ('es', 'ja', etc.)
  y consultamos el JSON.
- Si no hay traducción para ese idioma, devolvemos `None` y discord.py
  cae automáticamente al `default_text` del `locale_str`.
- Si el `locale_str` no trae `key` en extras (caso edge), usamos
  `string.message` como clave: así se puede mezclar con código viejo
  o pasar claves directamente cuando el contexto lo permite.
"""
from __future__ import annotations

from typing import Optional, Dict
import discord
from discord import app_commands
from discord.app_commands import locale_str, TranslationContext

from src.application.interfaces.translator import ITranslator
from src.application.interfaces.logger import ILogger


# Mapeo: discord.Locale -> código corto del JSON.
# Cubre las variantes regionales: es-ES y es-419 ambas resuelven a 'es'.
DISCORD_LOCALE_TO_SHORT: Dict[discord.Locale, str] = {
    discord.Locale.american_english: "en",
    discord.Locale.british_english: "en",
    discord.Locale.spain_spanish: "es",
    discord.Locale.latin_american_spanish: "es",
    discord.Locale.japanese: "ja",
    discord.Locale.polish: "pl",
}


class NamiAppTranslator(app_commands.Translator):
    """Adaptador entre discord.py y nuestro `ITranslator`."""

    def __init__(self, translator: ITranslator, logger: ILogger) -> None:
        super().__init__()
        self._t = translator
        self._logger = logger

    async def load(self) -> None:
        self._logger.info("app_translator_loaded")

    async def unload(self) -> None:
        self._logger.info("app_translator_unloaded")

    async def translate(
        self,
        string: locale_str,
        locale: discord.Locale,
        context: TranslationContext,
    ) -> Optional[str]:
        """
        Resuelve `string` al idioma `locale`.

        Devuelve `None` para indicar a discord.py que use el texto por
        defecto (el primer argumento de `locale_str`).
        """
        # Idioma no soportado por nosotros: usar el default.
        short_lang = DISCORD_LOCALE_TO_SHORT.get(locale)
        if short_lang is None:
            return None

        # Extraer la clave de búsqueda. Preferimos `extras["key"]`;
        # si no existe, usamos `message` (compatibilidad con casos
        # donde la clave sí cumple el regex de Discord).
        key = string.extras.get("key") if string.extras else None
        if key is None:
            key = string.message

        # Si no parece una clave nuestra (no contiene punto), asumimos
        # que es texto literal y no lo traducimos.
        if "." not in key:
            return None

        # Para el idioma por defecto, discord.py usa el `default_text`
        # del decorador, así que normalmente no nos lo pedirá. Si
        # llega, devolvemos None y se queda con el default.
        if short_lang == self._t.DEFAULT_LANG:  # type: ignore[attr-defined]
            return None

        try:
            translations = self._t.localizations(key)
        except Exception as e:
            self._logger.warning(
                "app_translator_lookup_failed",
                key=key,
                locale=str(locale),
                error=str(e),
            )
            return None

        text = translations.get(short_lang)
        if text is None:
            # Sin traducción en ese idioma: que use el default.
            return None

        return text