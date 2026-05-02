# src/application/use_cases/configure_channel_youtube.py
from dataclasses import dataclass

from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.logger import ILogger
from src.domain.entities.guild_config import GuildConfig


@dataclass
class ConfigureChannelYouTubeCommand:
    guild_id: int
    channel_id: int


class ConfigureChannelYouTubeUseCase:
    """
    Caso de uso: configura el canal de Discord donde se publicarán
    los videos (y shorts) de YouTube. Independiente del canal de streams en vivo.
    """

    def __init__(
        self,
        guild_repo: IGuildRepository,
        logger: ILogger,
    ) -> None:
        self._guild_repo = guild_repo
        self._logger = logger

    async def execute(self, command: ConfigureChannelYouTubeCommand) -> GuildConfig:
        """
        Crea o actualiza la configuración del servidor con el canal de
        anuncios de YouTube. Independiente de announcement_channel_id:
        ambos canales pueden apuntar al mismo o a distintos canales de Discord.
        Preserva el resto de campos si el GuildConfig ya existía.
        """
        existing = await self._guild_repo.get_by_id(command.guild_id)

        if existing:
            existing.youtube_channel_id = command.channel_id
            updated = await self._guild_repo.create_or_update(existing)
        else:
            config = GuildConfig(
                guild_id=command.guild_id,
                youtube_channel_id=command.channel_id,
            )
            updated = await self._guild_repo.create_or_update(config)

        self._logger.info(
            "youtube_channel_configured",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )
        return updated