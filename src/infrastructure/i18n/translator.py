# src/infrastructure/i18n/translator.py
import json
from pathlib import Path
from typing import Any, Dict

from src.application.interfaces.translator import ITranslator
from src.application.interfaces.logger import ILogger


class JSONTranslator(ITranslator):
    """
    Traductor basado en archivos JSON, uno por idioma.
    Carga todos los locales en memoria al arrancar (los ficheros son pequeños).

    El idioma por defecto es 'en'. Si no se encuentra una clave en el
    idioma pedido, hace fallback a 'en' con un warning. Si tampoco
    está en 'en', devuelve la clave literal entre corchetes.
    """

    DEFAULT_LANG = "en"

    def __init__(self, locales_dir: Path, logger: ILogger) -> None:
        self._logger = logger
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_all(locales_dir)

    def _load_all(self, locales_dir: Path) -> None:
        if not locales_dir.exists():
            raise FileNotFoundError(
                f"Directorio de locales no encontrado: {locales_dir}"
            )

        for path in locales_dir.glob("*.json"):
            lang = path.stem
            with path.open("r", encoding="utf-8") as f:
                self._translations[lang] = json.load(f)
            self._logger.info(
                "translations_loaded",
                lang=lang,
                keys=len(self._translations[lang]),
            )

        if self.DEFAULT_LANG not in self._translations:
            raise RuntimeError(
                f"Falta el archivo de idioma por defecto: {self.DEFAULT_LANG}.json"
            )

    def t(self, key: str, lang: str, **kwargs: Any) -> str:
        if lang not in self._translations:
            self._logger.warning(
                "translation_unknown_language",
                requested_lang=lang,
                fallback=self.DEFAULT_LANG,
            )
            lang = self.DEFAULT_LANG

        template = self._translations[lang].get(key)

        if template is None and lang != self.DEFAULT_LANG:
            self._logger.warning(
                "translation_missing_key",
                key=key,
                lang=lang,
                fallback=self.DEFAULT_LANG,
            )
            template = self._translations[self.DEFAULT_LANG].get(key)

        if template is None:
            self._logger.warning(
                "translation_missing_key_in_default",
                key=key,
                lang=self.DEFAULT_LANG,
            )
            return f"[{key}]"

        try:
            return template.format(**kwargs) if kwargs else template
        except (KeyError, IndexError) as e:
            self._logger.warning(
                "translation_interpolation_failed",
                key=key,
                lang=lang,
                error=str(e),
            )
            return template

    def localizations(self, key: str) -> Dict[str, str]:
        """
        Devuelve {lang: texto} para todos los idiomas que tengan la clave.
        El idioma por defecto NO se incluye porque va en el campo
        principal (`name=` / `description=`) del slash command.
        Si una traducción falta en algún idioma, simplemente se omite
        de ese diccionario (Discord caerá al texto por defecto en/inglés).
        """
        result: Dict[str, str] = {}
        for lang, table in self._translations.items():
            if lang == self.DEFAULT_LANG:
                continue
            value = table.get(key)
            if value is not None:
                result[lang] = value
        return result

    def supported_languages(self) -> list[str]:
        return sorted(self._translations.keys())