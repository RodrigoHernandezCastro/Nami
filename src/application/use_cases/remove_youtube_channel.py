from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import YouTubeChannelNotFoundError
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.logger import ILogger


@dataclass
class RemoveYouTubeCommand:
    guild_id: int
    channel_id: str


class RemoveYouTubeChannelUseCase:
    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._logger = logger

    async def execute(self, command: RemoveYouTubeCommand) -> None:
        removed = await self._youtube_repo.remove(
            command.guild_id,
            command.channel_id,
        )
        if not removed:
            raise YouTubeChannelNotFoundError(
                f"Canal {command.channel_id} no está monitoreado."
            )

        self._logger.info(
            "youtube_channel_removed",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )