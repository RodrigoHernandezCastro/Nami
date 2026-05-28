from dataclasses import dataclass
from typing import Optional, List

from src.domain.entities.streamer import Streamer
from src.domain.exceptions.domain_exceptions import StreamerNotFoundError
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.logger import ILogger


@dataclass
class UpdateStreamerCommand:
    guild_id: int
    username: str
    custom_message: str
    mention_type: str
    mention_role_ids: Optional[List[int]] = None


class UpdateStreamerUseCase:
    """Actualiza la configuración de un streamer de Twitch monitoreado."""

    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._logger = logger

    async def execute(self, command: UpdateStreamerCommand) -> Streamer:
        streamers = await self._streamer_repo.find_by_guild(command.guild_id)
        existing = [s for s in streamers if s.username.lower() == command.username.lower()]
        if not existing:
            raise StreamerNotFoundError(
                f"'{command.username}' no está en la lista de monitoreo."
            )

        streamer = existing[0]
        streamer.custom_message = command.custom_message
        streamer.mention_type = command.mention_type
        streamer.mention_role_ids = command.mention_role_ids

        updated = await self._streamer_repo.update(streamer)

        self._logger.info(
            "streamer_updated",
            guild_id=command.guild_id,
            username=command.username.lower(),
        )
        return updated
