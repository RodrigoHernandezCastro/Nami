from dataclasses import dataclass
from typing import List
from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository


@dataclass
class ListYouTubeQuery:
    guild_id: int


class ListYouTubeChannelsUseCase:
    """Caso de uso: lista todos los canales de YouTube monitoreados de un servidor."""
    def __init__(self, youtube_repo: IYouTubeRepository) -> None:
        self._youtube_repo = youtube_repo

    async def execute(self, query: ListYouTubeQuery) -> List[YouTubeChannel]:
        """
        Devuelve todos los canales del servidor. Incluye announced_video_history
        y uploads_playlist_id tal como están en BD, útil para depuración
        desde el Cog sin necesitar una consulta adicional.
        """
        return await self._youtube_repo.find_by_guild(query.guild_id)