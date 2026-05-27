# src/application/use_cases/configure_channel_youtube_live.py
from dataclasses import dataclass
from typing import Optional

from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.logger import ILogger
from src.domain.entities.guild_config import GuildConfig


@dataclass
class ConfigureChannelYouTubeLiveCommand:
    guild_id: int
    channel_id: int


class ConfigureChannelYouTubeLiveUseCase:
    """
    Caso de uso: configura el canal de Discord donde se publicarán
    los directos de YouTube. Implementación atómica.
    """

    def __init__(
        self,
        guild_repo: IGuildRepository,
        logger: ILogger,
    ) -> None:
        self._guild_repo = guild_repo
        self._logger = logger

    async def execute(self, command: ConfigureChannelYouTubeLiveCommand) -> Optional[GuildConfig]:
        # 1. Ejecución atómica directamente en el motor SQL
        await self._guild_repo.set_youtube_live_channel(
            guild_id=command.guild_id,
            channel_id=command.channel_id
        )

        # 2. Registro de la operación
        self._logger.info(
            "youtube_live_channel_configured",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )

        # 3. Retornamos la entidad actualizada con todos los campos vigentes
        return await self._guild_repo.get_by_id(command.guild_id)
