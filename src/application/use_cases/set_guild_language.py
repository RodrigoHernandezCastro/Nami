# src/application/use_cases/set_guild_language.py
from dataclasses import dataclass

from src.domain.entities.guild_config import GuildConfig
from src.domain.exceptions.domain_exceptions import DomainError
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.translator import ITranslator
from src.application.interfaces.logger import ILogger


class UnsupportedLanguageError(DomainError):
    """El idioma solicitado no está soportado."""


@dataclass
class SetGuildLanguageCommand:
    guild_id: int
    language: str


class SetGuildLanguageUseCase:
    """
    Caso de uso: cambia el idioma de un servidor.
    Preserva el resto de campos del GuildConfig.
    Si el guild no existía aún, lo crea con valores por defecto.
    """

    def __init__(
        self,
        guild_repo: IGuildRepository,
        translator: ITranslator,
        logger: ILogger,
    ) -> None:
        self._guild_repo = guild_repo
        self._translator = translator
        self._logger = logger

    async def execute(self, command: SetGuildLanguageCommand) -> GuildConfig:
        supported = self._translator.supported_languages()
        if command.language not in supported:
            raise UnsupportedLanguageError(
                f"Idioma '{command.language}' no soportado. Disponibles: {supported}"
            )

        existing = await self._guild_repo.get_by_id(command.guild_id)

        if existing:
            existing.language = command.language
            updated = await self._guild_repo.create_or_update(existing)
        else:
            config = GuildConfig(
                guild_id=command.guild_id,
                language=command.language,
            )
            updated = await self._guild_repo.create_or_update(config)

        self._logger.info(
            "guild_language_changed",
            guild_id=command.guild_id,
            language=command.language,
        )
        return updated