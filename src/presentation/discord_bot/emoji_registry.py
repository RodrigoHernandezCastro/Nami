# src/presentation/discord_bot/emoji_registry.py
"""
Cache de Application Emojis del bot.

Las Application Emojis viven en el Developer Portal de Discord
(no en un servidor) y son específicas del bot. La doc oficial
confirma que NO requieren el permiso USE_EXTERNAL_EMOJIS, así que
funcionan en cualquier servidor donde el bot esté presente.

Este registry:
1. Carga todos los Application Emojis del bot al arrancar (1 sola
   llamada HTTP).
2. Mantiene un dict {nombre: "<:name:id>"} en memoria.
3. Cae a un fallback Unicode si un emoji concreto no existe (p.ej.
   lo borraste o renombraste).

La capa de presentación (jankenpon_embed.py) consulta este registry
en lugar de tener IDs hardcodeados.
"""
from __future__ import annotations

from typing import Dict, Optional

import discord
from discord.ext import commands

from src.application.interfaces.logger import ILogger


class AppEmojiRegistry:
    """
    Cache de Application Emojis. Llama a `load()` UNA VEZ tras el
    `on_ready` (no en setup_hook, ver nota abajo).

    NOTA IMPORTANTE: `bot.fetch_application_emojis()` requiere que el
    bot ya tenga `application_id` resuelto, lo cual sucede después
    del primer `on_ready`. Por eso el bot llama a `load()` desde un
    listener de `on_ready`, no desde `setup_hook`.
    """

    # Fallbacks Unicode por si un emoji no está disponible.
    # Si un nombre no aparece aquí, se devuelve un placeholder vacío
    # (mejor un hueco que un crash).
    _DEFAULT_FALLBACKS: Dict[str, str] = {
        "rock": "🪨",
        "paper": "📄",
        "scissors": "✂️",
        "first_place": "🥇",
        "second_place": "🥈",
        "third_place": "🥉",
    }

    def __init__(self, logger: ILogger) -> None:
        self._logger = logger
        self._cache: Dict[str, str] = {}
        self._loaded: bool = False

    async def load(self, bot: commands.Bot) -> None:
        if self._loaded:
            return

        try:
            # En discord.py 2.4.0, realizamos la petición HTTP manualmente
            app_id = bot.application_id or (await bot.application_info()).id
            route = discord.http.Route("GET", f"/applications/{app_id}/emojis")
            data = await bot.http.request(route)

            # El endpoint devuelve un dict con una lista de emojis en 'items'
            emojis_data = data.get("items", [])

            for emoji_data in emojis_data:
                name = emoji_data["name"]
                emoji_id = emoji_data["id"]
                animated = emoji_data.get("animated", False)
                # Formateamos el string nativo de Discord
                fmt = f"<a:{name}:{emoji_id}>" if animated else f"<:{name}:{emoji_id}>"
                self._cache[name] = fmt

        except discord.HTTPException as exc:
            self._logger.warning(
                "app_emojis_fetch_failed",
                error=str(exc),
                hint="Se usarán fallbacks Unicode.",
            )
            self._loaded = True
            return

        self._loaded = True
        self._logger.info(
            "app_emojis_loaded",
            count=len(self._cache),
            names=list(self._cache.keys()),
        )

    def get(self, name: str, fallback: Optional[str] = None) -> str:
        """
        Devuelve el emoji formateado para Discord.

        Orden de búsqueda:
        1. El emoji custom del bot (si está cacheado).
        2. El argumento `fallback` explícito.
        3. El fallback Unicode definido en _DEFAULT_FALLBACKS.
        4. String vacío (no rompe el render).
        """
        if name in self._cache:
            return self._cache[name]
        if fallback is not None:
            return fallback
        return self._DEFAULT_FALLBACKS.get(name, "")

    def is_loaded(self) -> bool:
        return self._loaded
