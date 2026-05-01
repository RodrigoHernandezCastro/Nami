from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IYouTubeService(ABC):
    """Contrato para el cliente de YouTube API."""

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def channel_exists(self, channel_id: str) -> bool: ...

    @abstractmethod
    async def get_live_streams(self, channel_ids: List[str]) -> Dict[str, dict]: ...

    @abstractmethod
    async def get_latest_videos(self, channel_id: str, max_results: int = 5) -> List[dict]: ...

    @abstractmethod
    async def get_channel_details(self, channel_id: str) -> Optional[dict]: ...