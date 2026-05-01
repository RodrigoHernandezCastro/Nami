import asyncio
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


class YouTubeAPIClient(IYouTubeService):
    """
    Cliente oficial de YouTube API v3.
    Soporta LIVE, videos, shorts, canales, etc.
    """

    def __init__(self, api_key: str, logger: ILogger) -> None:
        self.api_key = api_key
        self._logger = logger
        self._youtube = None

    async def initialize(self) -> None:
        """Inicializa el cliente YouTube."""
        self._youtube = build("youtube", "v3", developerKey=self.api_key)
        self._logger.info("youtube_client_initialized")

    async def close(self) -> None:
        """Cierra conexiones (si aplica)."""
        pass

    async def _execute(self, request) -> dict:
        """Ejecuta una petición síncrona de googleapiclient sin bloquear el event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, request.execute)

    async def channel_exists(self, channel_id: str) -> bool:
        """Verifica si un canal existe."""
        try:
            response = await self._execute(
                self._youtube.channels().list(
                    part="snippet",
                    id=channel_id,
                )
            )
            return len(response.get("items", [])) > 0
        except HttpError as e:
            if e.resp.status == 404:
                return False
            self._logger.warning("youtube_channel_check_failed", error=str(e))
            return False

    async def get_live_streams(self, channel_ids: List[str]) -> Dict[str, dict]:
        """
        Obtiene streams en vivo de múltiples canales.
        Retorna {channel_id: stream_data}.
        """
        if not channel_ids:
            return {}

        try:
            response = await self._execute(
                self._youtube.search().list(
                    part="snippet",
                    channelId=",".join(channel_ids),
                    type="video",
                    eventType="live",
                    maxResults=50,
                )
            )

            live_streams = {}
            for item in response.get("items", []):
                channel_id = item["snippet"]["channelId"]
                live_streams[channel_id] = {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    "published_at": item["snippet"]["publishedAt"],
                }
            return live_streams
        except HttpError as e:
            self._logger.error("youtube_live_streams_error", status=e.resp.status)
            return {}

    async def get_latest_videos(self, channel_id: str, max_results: int = 5) -> List[dict]:
        """Obtiene los videos más recientes (incluye shorts)."""
        try:
            uploads_response = await self._execute(
                self._youtube.channels().list(
                    part="contentDetails",
                    id=channel_id,
                )
            )

            if not uploads_response.get("items"):
                return []

            uploads_playlist = uploads_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            playlist_response = await self._execute(
                self._youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist,
                    maxResults=max_results,
                )
            )

            videos = []
            for item in playlist_response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "thumbnail": snippet["thumbnails"]["medium"]["url"],
                    "published_at": snippet["publishedAt"],
                    "type": "short" if len(snippet["title"]) < 50 else "video",
                })
            return videos
        except HttpError as e:
            self._logger.error("youtube_videos_error", status=e.resp.status)
            return []

    async def get_channel_details(self, channel_id: str) -> Optional[dict]:
        """Obtiene información detallada del canal."""
        try:
            response = await self._execute(
                self._youtube.channels().list(
                    part="snippet,statistics",
                    id=channel_id,
                )
            )

            if not response.get("items"):
                return None

            item = response["items"][0]
            return {
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"][:200],
                "subscriber_count": int(item["statistics"].get("subscriberCount", 0)),
                "view_count": int(item["statistics"].get("viewCount", 0)),
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            }
        except HttpError:
            return None

    async def username_to_channel_id(self, username: str) -> Optional[str]:
        """
        Convierte @username → channel_id (UC_xxxxxxxx).
        Ej: "@IlloJuan_" → "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        """
        try:
            handle = username if username.startswith("@") else f"@{username}"

            response = await self._execute(
                self._youtube.channels().list(
                    part="id",
                    forHandle=handle,
                )
            )

            print(f"DEBUG YOUTUBE ({handle}):", response)

            items = response.get("items", [])
            if items:
                return items[0]["id"]
            return None

        except HttpError as e:
            self._logger.warning("youtube_username_to_id_failed", username=username, error=str(e))
            return None