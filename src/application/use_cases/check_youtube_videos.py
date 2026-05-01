# src/application/use_cases/check_youtube_videos.py
from typing import List, Tuple

import dateutil.parser

from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository
from src.application.interfaces.youtube_service import IYouTubeService
from src.application.interfaces.logger import ILogger


class CheckYouTubeVideosUseCase:
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

        if not channels:
            return newly_published

        channel_ids = [c.channel_id for c in channels]
        live_streams = await self._youtube_service.get_live_streams(channel_ids)

        for channel in channels:

            if channel.channel_id in live_streams:
                live = live_streams[channel.channel_id]
                video_id = live["video_id"]

                if channel.has_announced_video(video_id):
                    self._logger.debug(
                        "youtube_live_already_announced",
                        channel_id=channel.channel_id,
                        video_id=video_id,
                    )
                else:
                    await self._youtube_repo.update_video_history(channel.id, video_id)
                    newly_published.append((channel, {**live, "liveBroadcastContent": "live"}))
                    
                    self._logger.info(
                        "youtube_live_started",
                        channel_id=channel.channel_id,
                        video_id=video_id,
                    )
                continue

            videos = await self._youtube_service.get_latest_videos(channel.channel_id, 10)
            if not videos:
                continue

            newest_video = videos[0]

            broadcast_status = newest_video.get("liveBroadcastContent", "none")
            if broadcast_status == "upcoming":
                continue

            if channel.has_announced_video(newest_video["video_id"]):
                self._logger.debug(
                    "youtube_video_already_announced",
                    channel_id=channel.channel_id,
                    video_id=newest_video["video_id"],
                )
                continue

            video_date = dateutil.parser.isoparse(newest_video["published_at"]).replace(tzinfo=None)
            channel_date = channel.added_at.replace(tzinfo=None)

            if video_date < channel_date and not channel.announced_video_history:
                await self._youtube_repo.update_video_history(
                    channel.id,
                    newest_video["video_id"],
                )
                continue

            await self._youtube_repo.update_video_history(
                channel.id,
                newest_video["video_id"],
            )

            newly_published.append((channel, newest_video))

            self._logger.info(
                "youtube_new_video_found",
                channel_id=channel.channel_id,
                video_id=newest_video["video_id"],
            )

        return newly_published