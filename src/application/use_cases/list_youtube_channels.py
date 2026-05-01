from dataclasses import dataclass
from typing import List
from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository


@dataclass
class ListYouTubeQuery:
    guild_id: int


class ListYouTubeChannelsUseCase:
    def __init__(self, youtube_repo: IYouTubeRepository) -> None:
        self._youtube_repo = youtube_repo

    async def execute(self, query: ListYouTubeQuery) -> List[YouTubeChannel]:
        return await self._youtube_repo.find_by_guild(query.guild_id)