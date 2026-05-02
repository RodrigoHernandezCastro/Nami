# src/application/interfaces/youtube_service.py
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
    async def get_latest_videos(self, channel_id: str, max_results: int = 5) -> List[dict]:
        """
        Obtiene videos recientes resolviendo primero el uploads_playlist_id.
        Coste: 2 unidades (channels.list + playlistItems.list).
        Usar solo cuando no se dispone del playlist_id cacheado.
        """
        ...

    @abstractmethod
    async def get_latest_videos_from_playlist(
        self, playlist_id: str, max_results: int = 1
    ) -> List[dict]:
        """
        Obtiene videos recientes directamente desde un playlist ID conocido.
        Coste: 1 unidad (solo playlistItems.list). Usar cuando uploads_playlist_id
        ya está cacheado en la entidad YouTubeChannel.
        """
        ...

    @abstractmethod
    async def get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """
        Resuelve el uploads_playlist_id de un canal.
        Coste: 1 unidad (channels.list). Llamar solo una vez por canal y persistir.
        """
        ...

    @abstractmethod
    async def get_videos_details_batch(self, video_ids: List[str]) -> Dict[str, dict]:
        """
        Detalles de hasta 50 videos en una sola llamada a videos.list.
        Coste: 1 unidad por cada ≤50 IDs.
        """
        ...

    @abstractmethod
    async def get_channel_details(self, channel_id: str) -> Optional[dict]: ...