# src/presentation/discord_bot/i18n_helper.py
from typing import Optional
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.translator import ITranslator


class GuildLanguageResolver:
    """
    Helper de presentación: resuelve el idioma de un guild y traduce.
    Mantiene un caché en memoria muy simple (dict guild_id -> lang) para
    no consultar la BD en cada interacción. El caché se invalida cuando
    cambia el idioma vía SetGuildLanguageUseCase llamando a `invalidate()`.

    Para multi-process se necesitaría Redis (no es el caso aquí).
    """

    def __init__(
        self,
        guild_repo: IGuildRepository,
        translator: ITranslator,
        default_lang: str = "en",
    ) -> None:
        self._guild_repo = guild_repo
        self._translator = translator
        self._default = default_lang
        self._cache: dict[int, str] = {}

    async def get_lang(self, guild_id: Optional[int]) -> str:
        if guild_id is None:
            return self._default

        cached = self._cache.get(guild_id)
        if cached is not None:
            return cached

        config = await self._guild_repo.get_by_id(guild_id)
        lang = config.language if config else self._default
        self._cache[guild_id] = lang
        return lang

    def invalidate(self, guild_id: int) -> None:
        """Llamar tras cambiar el idioma para que el caché no quede stale."""
        self._cache.pop(guild_id, None)

    async def t(self, key: str, guild_id: Optional[int], **kwargs) -> str:
        """Atajo: resuelve idioma + traduce en una llamada."""
        lang = await self.get_lang(guild_id)
        return self._translator.t(key, lang, **kwargs)