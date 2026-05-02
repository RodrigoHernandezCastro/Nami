from dataclasses import dataclass
from src.domain.entities.guild_config import GuildConfig
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.logger import ILogger


@dataclass
class ConfigureChannelCommand:
    guild_id: int
    channel_id: int


class ConfigureChannelUseCase:
    """Caso de uso: configura el canal de anuncios de un servidor."""

    def __init__(
        self,
        guild_repo: IGuildRepository,
        logger: ILogger,
    ) -> None:
        self._guild_repo = guild_repo
        self._logger = logger

    async def execute(self, command: ConfigureChannelCommand) -> GuildConfig:
        """
        Crea o actualiza la configuración del servidor con el canal de
        anuncios de Twitch. Si ya existe un GuildConfig, preserva el
        resto de campos (youtube_channel_id, límite, idioma, etc.).
        Devuelve la entidad actualizada tal como quedó en BD.
        """
        existing = await self._guild_repo.get_by_id(command.guild_id)

        if existing:
            existing.announcement_channel_id = command.channel_id
            updated = await self._guild_repo.create_or_update(existing)
        else:
            config = GuildConfig(
                guild_id=command.guild_id,
                announcement_channel_id=command.channel_id,
            )
            updated = await self._guild_repo.create_or_update(config)

        self._logger.info(
            "channel_configured",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )
        return updated