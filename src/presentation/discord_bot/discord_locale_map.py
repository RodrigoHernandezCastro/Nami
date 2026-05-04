# src/presentation/discord_bot/discord_locale_map.py
"""
Mapeo entre códigos cortos de idioma usados en los JSON ('es', 'en', 'pl', 'ja')
y los enums `discord.Locale` que Discord espera en `name_localizations` y
`description_localizations`.

Discord soporta múltiples variantes regionales (es-ES, es-LA, en-US, en-GB).
Mantenemos un único JSON por idioma base y replicamos en las variantes que
existen en discord.Locale; así un usuario con cliente en español de cualquier
variante verá el mismo texto.

Si en el futuro quieres separar es-ES vs es-LA, basta con crear dos JSON
('es_ES.json', 'es_LA.json') y ajustar este mapa.
"""
from typing import Dict, List
import discord


# Cada código corto de JSON puede mapear a una o varias `discord.Locale`.
LANG_TO_DISCORD_LOCALES: Dict[str, List[discord.Locale]] = {
    "es": [discord.Locale.spain_spanish, discord.Locale.latin_american_spanish],
    "en": [discord.Locale.american_english, discord.Locale.british_english],
    "pl": [discord.Locale.polish],
    "ja": [discord.Locale.japanese],
}


def expand_localizations(
    short_code_dict: Dict[str, str],
) -> Dict[discord.Locale, str]:
    """
    Convierte un dict {short_code: text} (lo que devuelve
    ITranslator.localizations()) en un dict {discord.Locale: text}
    listo para pasar a `name_localizations=` o `description_localizations=`.

    Si un short_code no tiene mapeo conocido, se ignora silenciosamente:
    es preferible perder esa localización que romper el arranque del bot.
    """
    result: Dict[discord.Locale, str] = {}
    for short, text in short_code_dict.items():
        for locale in LANG_TO_DISCORD_LOCALES.get(short, []):
            result[locale] = text
    return result