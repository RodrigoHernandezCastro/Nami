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
        """
        Elimina un streamer del monitoreo. El username se normaliza a
        minúsculas antes de buscarlo en BD. Lanza StreamerNotFoundError
        si no existe en el servidor, sin distinguir entre "nunca añadido"
        y "ya eliminado".
        """
        removed = await self._streamer_repo.remove(
            command.guild_id,
            command.username.lower(),
        )
        if not removed:
            raise StreamerNotFoundError(username=command.username)

        self._logger.info(
            "streamer_removed",
            guild_id=command.guild_id,
            username=command.username.lower(),
        )