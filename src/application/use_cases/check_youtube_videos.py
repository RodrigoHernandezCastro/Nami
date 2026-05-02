# src/application/use_cases/check_youtube_videos.py
from typing import List, Tuple

import dateutil.parser

from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


class CheckYouTubeVideosUseCase:
    """
    Detecta nuevos videos de YouTube con consumo mínimo de cuota API.

    Coste por ciclo (N canales):
    - Canal con playlist_id cacheado : 1 unidad  (playlistItems.list)
    - Canal sin playlist_id cacheado : 2 unidades (channels.list + playlistItems.list)
                                       → solo ocurre la primera vez, luego se cachea en BD
    - Batch de detalles (si hay nuevos): 1 unidad por cada ≤50 candidatos

    Ejemplo estable con 10 canales, 0 novedades: 10 unidades/ciclo.
    Con 10 canales, 2 novedades: 11 unidades/ciclo.
    """

    def __init__(
        self,
        youtube_repo: IYouTubeRepository,
        youtube_service: IYouTubeService,
        logger: ILogger,
    ) -> None:
        self._youtube_repo = youtube_repo
        self._youtube_service = youtube_service
        self._logger = logger

    async def execute(self) -> List[Tuple[YouTubeChannel, dict]]:
        channels = await self._youtube_repo.find_all_with_channel()
        if not channels:
            return []

        # ------------------------------------------------------------------
        # Fase 1: Obtener el último video de cada canal (secuencial por lock)
        # ------------------------------------------------------------------
        candidates: List[Tuple[YouTubeChannel, dict]] = []

        for channel in channels:
            video = await self._fetch_latest_video(channel)
            if video is None:
                continue

            video_id = video["video_id"]

            if channel.has_announced_video(video_id):
                self._logger.debug(
                    "youtube_video_already_announced",
                    channel_id=channel.channel_id,
                    video_id=video_id,
                )
                continue

            candidates.append((channel, video))

        if not candidates:
            return []

        # ------------------------------------------------------------------
        # Fase 2: Enriquecer candidatos con liveBroadcastContent (1 batch)
        # ------------------------------------------------------------------
        candidate_ids = [v["video_id"] for _, v in candidates]
        batch_details = await self._youtube_service.get_videos_details_batch(candidate_ids)

        # ------------------------------------------------------------------
        # Fase 3: Filtrar, persistir y retornar
        # ------------------------------------------------------------------
        newly_published: List[Tuple[YouTubeChannel, dict]] = []

        for channel, base_video in candidates:
            video_id = base_video["video_id"]
            video = {**base_video, **batch_details.get(video_id, {})}

            broadcast_status = video.get("liveBroadcastContent", "none")
            if broadcast_status == "upcoming":
                self._logger.debug(
                    "youtube_video_upcoming_skipped",
                    channel_id=channel.channel_id,
                    video_id=video_id,
                )
                continue

            video_date = dateutil.parser.isoparse(video["published_at"]).replace(tzinfo=None)
            channel_date = channel.added_at.replace(tzinfo=None)

            if video_date < channel_date and not channel.announced_video_history:
                # Publicado antes de añadir el canal: registrar sin anunciar
                await self._youtube_repo.update_video_history(channel.id, video_id)
                self._logger.debug(
                    "youtube_video_predates_channel_added",
                    channel_id=channel.channel_id,
                    video_id=video_id,
                )
                continue

            await self._youtube_repo.update_video_history(channel.id, video_id)
            newly_published.append((channel, video))

            self._logger.info(
                "youtube_new_video_found",
                channel_id=channel.channel_id,
                video_id=video_id,
                live=broadcast_status == "live",
            )

        return newly_published

    # ------------------------------------------------------------------
    # Helper: fetch con caché de playlist_id
    # ------------------------------------------------------------------

    async def _fetch_latest_video(self, channel: YouTubeChannel):
        """
        Obtiene el último video del canal usando el playlist_id cacheado si existe.
        Si no existe, lo resuelve (1 unidad extra), lo persiste y luego obtiene el video.
        """
        if channel.uploads_playlist_id:
            # Camino rápido: 1 unidad
            videos = await self._youtube_service.get_latest_videos_from_playlist(
                channel.uploads_playlist_id, max_results=1
            )
        else:
            # Primera vez: resolver y cachear el playlist_id (2 unidades esta vez)
            playlist_id = await self._youtube_service.get_uploads_playlist_id(channel.channel_id)
            if not playlist_id:
                self._logger.warning(
                    "youtube_playlist_id_not_found",
                    channel_id=channel.channel_id,
                )
                return None

            await self._youtube_repo.update_uploads_playlist_id(channel.id, playlist_id)
            channel.uploads_playlist_id = playlist_id
            self._logger.info(
                "youtube_playlist_id_cached",
                channel_id=channel.channel_id,
                playlist_id=playlist_id,
            )

            videos = await self._youtube_service.get_latest_videos_from_playlist(
                playlist_id, max_results=1
            )

        if not videos:
            self._logger.warning("youtube_no_videos_found", channel_id=channel.channel_id)
            return None

        return videos[0]