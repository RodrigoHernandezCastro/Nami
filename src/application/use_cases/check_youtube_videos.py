from typing import List, Tuple, Optional

import dateutil.parser

from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


class CheckYouTubeVideosUseCase:
    """
    Detecta SOLO el video MÁS NUEVO por canal.
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
        newly_published = []

        for channel in channels:
            videos = await self._youtube_service.get_latest_videos(channel.channel_id, 10)
            if not videos:
                continue

            newest_video = videos[0]
            
            if channel.has_announced_video(newest_video["video_id"]):
                self._logger.debug("youtube_video_already_announced")
                continue

            video_date = dateutil.parser.isoparse(newest_video["published_at"]).replace(tzinfo=None)
            channel_date = channel.added_at.replace(tzinfo=None)

            if video_date < channel_date and not channel.announced_video_history:
                channel.add_announced_video(newest_video["video_id"])
                await self._youtube_repo.update_video_history(
                    channel.id, 
                    channel.announced_video_history
                )
                continue

            newly_published.append((channel, newest_video))
            
            channel.add_announced_video(newest_video["video_id"])
            
            await self._youtube_repo.update_video_history(
                channel.id, 
                channel.announced_video_history 
            )
            
            self._logger.info(
                "youtube_new_video_announced",
                channel_id=channel.channel_id,
                video_id=newest_video["video_id"],
                history_len=len(channel.announced_video_history),
            )

        return newly_published