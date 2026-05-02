# src/application/use_cases/add_youtube_channel.py
from dataclasses import dataclass
from typing import Optional, List

from src.domain.entities.youtube_channel import YouTubeChannel
from src.domain.exceptions.domain_exceptions import (
    ChannelNotFoundError,
    ChannelLimitReachedError,
    ChannelNotConfiguredError,
)
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


@dataclass
class AddYouTubeCommand:
    guild_id: int
    channel_id: str
    custom_message: str
    mention_type: str
    mention_role_ids: Optional[List[int]] = None


class AddYouTubeChannelUseCase:
    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        guild_repo: IGuildRepository,
        youtube_service: IYouTubeService,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._guild_repo = guild_repo
        self._youtube_service = youtube_service
        self._logger = logger

    async def execute(self, command: AddYouTubeCommand) -> YouTubeChannel:
        """
        Valida y persiste un nuevo canal de YouTube. Orden de validaciones:
        1. El channel_id existe en YouTube y se obtiene su nombre (2 llamadas API)
        2. El servidor tiene canal de anuncios configurado
        3. El límite de canales no está superado
        El channel_name se resuelve aquí para no repetir la llamada a la API
        en el Cog. Si details falla, usa channel_id como fallback.
        """
        # 1) Validar que el canal existe en YouTube y obtener su nombre
        if not await self._youtube_service.channel_exists(command.channel_id):
            raise ChannelNotFoundError(
                f"El canal '{command.channel_id}' no existe en YouTube."
            )

        details = await self._youtube_service.get_channel_details(command.channel_id)
        channel_name = details["title"] if details else command.channel_id

        # 2) Validar que el servidor tiene canal de anuncios configurado
        guild_config = await self._guild_repo.get_by_id(command.guild_id)
        if not guild_config or not guild_config.announcement_channel_id:
            raise ChannelNotConfiguredError(
                "El canal de anuncios no está configurado. "
                "Usa /configurar-canal primero."
            )

        # 3) Validar límite de canales
        current_count = await self._youtube_repo.count_by_guild(command.guild_id)
        if current_count >= guild_config.streamer_limit:
            raise ChannelLimitReachedError(
                f"Límite alcanzado: {guild_config.streamer_limit} canales."
            )

        # 4) Persistir
        channel = YouTubeChannel(
            guild_id=command.guild_id,
            channel_id=command.channel_id,
            channel_name=channel_name,
            custom_message=command.custom_message,
            mention_type=command.mention_type,
            mention_role_ids=command.mention_role_ids,
        )
        created = await self._youtube_repo.add(channel)

        self._logger.info(
            "youtube_channel_added",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
            channel_name=channel_name,
            db_id=created.id,
        )
        return created

    async def resolve_username(self, username: str) -> str:
        """
        Convierte @username o nombre de canal → channel_id (UCxxxx).
        Llama esto DESDE el Cog antes de construir AddYouTubeCommand.

        Ejemplo en el Cog:
            channel_id = await self._add_uc.resolve_username(usuario)
            cmd = AddYouTubeCommand(guild_id=..., channel_id=channel_id, ...)
            await self._add_uc.execute(cmd)
        """
        channel_id = await self._youtube_service.username_to_channel_id(username)
        if not channel_id:
            raise ChannelNotFoundError(
                f"No se encontró ningún canal de YouTube para '{username}'."
            )
        return channel_id