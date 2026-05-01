# src/application/interfaces/youtube_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.youtube_channel import YouTubeChannel


class IYouTubeRepository(ABC):
    """Contrato para persistencia de canales YouTube."""

    @abstractmethod
    async def add(self, channel: YouTubeChannel) -> YouTubeChannel: ...

    @abstractmethod
    async def remove(self, guild_id: int, channel_id: str) -> bool: ...

    @abstractmethod
    async def find_by_guild(self, guild_id: int) -> List[YouTubeChannel]: ...

    @abstractmethod
    async def find_all_with_channel(self) -> List[YouTubeChannel]: ...

    @abstractmethod
    async def count_by_guild(self, guild_id: int) -> int: ...

    @abstractmethod
    async def update_video_history(self, channel_id: int, video_id: str) -> bool:
        """Añade video_id al historial de anunciados (últimos 5)."""
        ...