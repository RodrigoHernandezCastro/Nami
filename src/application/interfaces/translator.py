# src/application/interfaces/translator.py
from abc import ABC, abstractmethod
from typing import Any, Dict


class ITranslator(ABC):
    """
    Puerto de la capa de aplicación para obtener textos traducidos.
    La implementación concreta vive en infrastructure/i18n.
    """

    @abstractmethod
    def t(self, key: str, lang: str, **kwargs: Any) -> str:
        """
        Devuelve el texto traducido para `key` en el idioma `lang`.
        Soporta interpolación con kwargs: t("greeting", "en", name="Ana").
        Si la clave no existe en `lang`, hace fallback al idioma por defecto
        y loggea warning. Si tampoco existe en el por defecto, devuelve
        la clave entre corchetes.
        """
        ...

    @abstractmethod
    def localizations(self, key: str) -> Dict[str, str]:
        """
        Devuelve un dict {lang_code: texto} con la traducción de `key` en
        TODOS los idiomas cargados. Útil para construir
        `name_localizations` / `description_localizations` de Discord.
        Las claves son códigos cortos ('es', 'en', 'pl', 'ja'); el caller
        debe mapearlos a discord.Locale (ver discord_locale_map).
        """
        ...

    @abstractmethod
    def supported_languages(self) -> list[str]:
        """Lista de códigos de idioma soportados, p.ej. ['en', 'es', 'pl', 'ja']."""
        ...