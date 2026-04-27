from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import StreamerNotFoundError
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.logger import ILogger


@dataclass
class RemoveStreamerCommand:
    guild_id: int
    username: str


class RemoveStreamerUseCase:
    """Caso de uso: elimina un streamer de la lista de monitoreo."""

    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._logger = logger

    async def execute(self, command: RemoveStreamerCommand) -> None:
        removed = await self._streamer_repo.remove(
            command.guild_id,
            command.username.lower(),
        )
        if not removed:
            raise StreamerNotFoundError(
                f"'{command.username}' no está en la lista de monitoreo."
            )

        self._logger.info(
            "streamer_removed",
            guild_id=command.guild_id,
            username=command.username.lower(),
        )