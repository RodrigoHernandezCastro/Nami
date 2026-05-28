from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import YouTubeChannelNotFoundError
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.logger import ILogger


@dataclass
class RemoveYouTubeCommand:
    guild_id: int
    channel_id: str


class RemoveYouTubeChannelUseCase:
    """Caso de uso: elimina un canal de YouTube del monitoreo."""
    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._logger = logger

    async def execute(self, command: RemoveYouTubeCommand) -> None:
        """
        Elimina el canal por guild_id + channel_id. Lanza
        YouTubeChannelNotFoundError si no estaba monitoreado.
        """
        removed = await self._youtube_repo.remove(
            command.guild_id,
            command.channel_id,
        )
        if not removed:
            raise YouTubeChannelNotFoundError(channel=command.channel_id)

        self._logger.info(
            "youtube_channel_removed",
            guild_id=command.guild_id,
            channel_id=command.channel_id,
        )