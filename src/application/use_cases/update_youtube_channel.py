from dataclasses import dataclass
from typing import Optional, List

from src.domain.entities.youtube_channel import YouTubeChannel
from src.domain.exceptions.domain_exceptions import YouTubeChannelNotFoundError
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


@dataclass
class UpdateYouTubeChannelCommand:
    guild_id: int
    channel_id: str
    custom_message: str
    mention_type: str
    mention_role_ids: Optional[List[int]] = None


class UpdateYouTubeChannelUseCase:
    """Actualiza la configuración de video de un canal de YouTube monitoreado."""

    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        youtube_service: IYouTubeService,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._youtube_service = youtube_service
        self._logger = logger

    async def execute(self, command: UpdateYouTubeChannelCommand) -> YouTubeChannel:
        channels = await self._youtube_repo.find_by_guild(command.guild_id)
        existing = [c for c in channels if c.channel_id == command.channel_id]
        if not existing:
            raise YouTubeChannelNotFoundError(
                f"Canal '{command.channel_id}' no está monitoreado."
            )

        channel = existing[0]
        channel.custom_message = command.custom_message
        channel.mention_type = command.mention_type
        channel.mention_role_ids = command.mention_role_ids

        updated = await self._youtube_repo.update(channel)

        self._logger.info(
            "youtube_channel_updated",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )
        return updated
