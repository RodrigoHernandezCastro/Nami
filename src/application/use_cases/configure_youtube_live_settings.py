from dataclasses import dataclass
from typing import Optional, List

from src.domain.exceptions.domain_exceptions import YouTubeChannelNotFoundError
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.logger import ILogger


@dataclass
class ConfigureYouTubeLiveSettingsCommand:
    guild_id: int
    channel_id: str
    live_custom_message: Optional[str] = None
    live_mention_type: Optional[str] = None
    live_mention_role_ids: Optional[List[int]] = None


class ConfigureYouTubeLiveSettingsUseCase:
    """Configura mensaje/mención específicos para directos de un canal YouTube."""

    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._logger = logger

    async def execute(self, command: ConfigureYouTubeLiveSettingsCommand) -> None:
        channels = await self._youtube_repo.find_by_guild(command.guild_id)
        existing = [c for c in channels if c.channel_id == command.channel_id]
        if not existing:
            raise YouTubeChannelNotFoundError(channel=command.channel_id)

        updated = await self._youtube_repo.update_live_settings(
            guild_id=command.guild_id,
            channel_id=command.channel_id,
            live_custom_message=command.live_custom_message,
            live_mention_type=command.live_mention_type,
            live_mention_role_ids=command.live_mention_role_ids,
        )

        if updated:
            self._logger.info(
                "youtube_live_settings_configured",
                guild_id=command.guild_id,
                channel_id=command.channel_id,
            )
