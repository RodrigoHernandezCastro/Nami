# src/infrastructure/external_apis/youtube_api_client.py
import asyncio
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


class YouTubeAPIClient(IYouTubeService):
    """
    Cliente YouTube API v3 con consumo mínimo de cuota.

    Coste por ciclo de chequeo (N canales, con playlist_id cacheado):
    ┌──────────────────────────────────────────────────┬──────────────┐
    │ Operación                                        │ Unidades     │
    ├──────────────────────────────────────────────────┼──────────────┤
    │ N × playlistItems.list  (playlist_id cacheado)   │ N × 1        │
    │ K × videos.list batch   (K = canales con novedad)│ ceil(K/50)   │
    │ 1 × channels.list  (solo primera vez por canal)  │ 1 (una vez)  │
    │ search.list                                      │ NUNCA        │
    └──────────────────────────────────────────────────┴──────────────┘
    """

    def __init__(self, api_key: str, logger: ILogger) -> None:
        self.api_key = api_key
        self._logger = logger
        self._youtube = None
        # httplib2 (usado por googleapiclient) NO es thread-safe.
        # El lock serializa todas las llamadas para evitar corrupción TLS
        # cuando asyncio.gather lanza varias corrutinas en paralelo.
        self._api_lock: asyncio.Lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._youtube = build("youtube", "v3", developerKey=self.api_key)
        self._logger.info("youtube_client_initialized")

    async def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Helper interno
    # ------------------------------------------------------------------

    async def _execute(self, request) -> dict:
        """
        Ejecuta una petición síncrona de googleapiclient en un thread separado.
        El lock garantiza que httplib2 nunca se use concurrentemente.
        """
        loop = asyncio.get_event_loop()
        async with self._api_lock:
            return await loop.run_in_executor(None, request.execute)

    # ------------------------------------------------------------------
    # Playlist ID — 1 unidad, llamar solo una vez por canal
    # ------------------------------------------------------------------

    async def get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """
        Obtiene el uploads_playlist_id de un canal.
        Coste: 1 unidad. Persistir en BD para no volver a llamar.
        """
        try:
            response = await self._execute(
                self._youtube.channels().list(
                    part="contentDetails",
                    id=channel_id,
                )
            )
            items = response.get("items", [])
            if not items:
                return None
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except HttpError as e:
            self._logger.error(
                "youtube_get_playlist_id_error",
                channel_id=channel_id,
                status=e.resp.status,
            )
            return None

    # ------------------------------------------------------------------
    # Videos desde playlist — 1 unidad por llamada
    # ------------------------------------------------------------------

    async def get_latest_videos_from_playlist(
        self, playlist_id: str, max_results: int = 1
    ) -> List[dict]:
        """
        Obtiene los últimos videos directamente desde un playlist ID conocido.
        Coste: 1 unidad. Usar siempre que uploads_playlist_id esté cacheado.
        """
        try:
            response = await self._execute(
                self._youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=max_results,
                )
            )
            return self._parse_playlist_items(response)
        except HttpError as e:
            self._logger.error(
                "youtube_playlist_items_error",
                playlist_id=playlist_id,
                status=e.resp.status,
            )
            return []

    # ------------------------------------------------------------------
    # Videos con resolución de playlist — 2 unidades por llamada
    # ------------------------------------------------------------------

    async def get_latest_videos(self, channel_id: str, max_results: int = 5) -> List[dict]:
        """
        Obtiene videos recientes resolviendo primero el playlist ID.
        Coste: 2 unidades (channels.list + playlistItems.list).
        Usar solo cuando uploads_playlist_id no está cacheado todavía.
        """
        playlist_id = await self.get_uploads_playlist_id(channel_id)
        if not playlist_id:
            return []
        return await self.get_latest_videos_from_playlist(playlist_id, max_results)

    # ------------------------------------------------------------------
    # Batch de detalles — 1 unidad por cada ≤50 video IDs
    # ------------------------------------------------------------------

    async def get_videos_details_batch(self, video_ids: List[str]) -> Dict[str, dict]:
        """
        Obtiene detalles de hasta 50 videos en una sola llamada a videos.list.
        Coste: 1 unidad por chunk de 50. Incluye liveBroadcastContent y duration.
        """
        if not video_ids:
            return {}

        results: Dict[str, dict] = {}
        chunks = [video_ids[i:i + 50] for i in range(0, len(video_ids), 50)]

        for chunk in chunks:
            try:
                response = await self._execute(
                    self._youtube.videos().list(
                        part="snippet,contentDetails",
                        id=",".join(chunk),
                    )
                )
                for item in response.get("items", []):
                    vid = item["id"]
                    snippet = item["snippet"]
                    results[vid] = {
                        "video_id": vid,
                        "title": snippet.get("title", ""),
                        "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "channel_id": snippet.get("channelId", ""),
                        "liveBroadcastContent": snippet.get("liveBroadcastContent", "none"),
                        "duration": item.get("contentDetails", {}).get("duration", ""),
                    }
            except HttpError as e:
                self._logger.error(
                    "youtube_batch_details_error",
                    status=e.resp.status,
                    chunk=chunk,
                )

        return results

    # ------------------------------------------------------------------
    # Canal — 1 unidad
    # ------------------------------------------------------------------

    async def channel_exists(self, channel_id: str) -> bool:
        try:
            response = await self._execute(
                self._youtube.channels().list(part="snippet", id=channel_id)
            )
            return len(response.get("items", [])) > 0
        except HttpError as e:
            if e.resp.status == 404:
                return False
            self._logger.warning("youtube_channel_check_failed", error=str(e))
            return False

    async def get_channel_details(self, channel_id: str) -> Optional[dict]:
        try:
            response = await self._execute(
                self._youtube.channels().list(part="snippet,statistics", id=channel_id)
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
        try:
            handle = username if username.startswith("@") else f"@{username}"
            response = await self._execute(
                self._youtube.channels().list(part="id", forHandle=handle)
            )
            items = response.get("items", [])
            return items[0]["id"] if items else None
        except HttpError as e:
            self._logger.warning("youtube_username_to_id_failed", username=username, error=str(e))
            return None

    # ------------------------------------------------------------------
    # Live streams — 100 unidades (search.list) — evitar
    # ------------------------------------------------------------------

    async def get_live_streams(self, channel_ids: List[str]) -> Dict[str, dict]:
        """
        Detecta streams en vivo. Coste: 100 unidades. No usar en polling frecuente.
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
                cid = item["snippet"]["channelId"]
                live_streams[cid] = {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    "published_at": item["snippet"]["publishedAt"],
                    "liveBroadcastContent": "live",
                }
            return live_streams
        except HttpError as e:
            self._logger.error("youtube_live_streams_error", status=e.resp.status)
            return {}

    # ------------------------------------------------------------------
    # Helper de parseo
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_playlist_items(response: dict) -> List[dict]:
        videos = []
        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = snippet.get("resourceId", {}).get("videoId")
            if not video_id:
                continue
            thumbnails = snippet.get("thumbnails", {})
            thumbnail = (
                thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "thumbnail": thumbnail,
                "published_at": snippet.get("publishedAt", ""),
                "liveBroadcastContent": "unknown",  # se enriquece con videos.list batch
            })
        return videos