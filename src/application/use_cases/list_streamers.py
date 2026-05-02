from dataclasses import dataclass
from typing import List
from src.domain.entities.streamer import Streamer
from src.application.interfaces.streamer_repository import IStreamerRepository


@dataclass
class ListStreamersQuery:
    guild_id: int


class ListStreamersUseCase:
    """Caso de uso: lista todos los streamers monitoreados de un servidor."""

    def __init__(self, streamer_repo: IStreamerRepository) -> None:
        self._streamer_repo = streamer_repo

    async def execute(self, query: ListStreamersQuery) -> List[Streamer]:
        """
        Devuelve todos los streamers del servidor, incluyendo los que
        actualmente están online. Sin paginación: el límite de streamers
        por servidor garantiza que el resultado siempre es manejable.
        """
        return await self._streamer_repo.find_by_guild(query.guild_id)