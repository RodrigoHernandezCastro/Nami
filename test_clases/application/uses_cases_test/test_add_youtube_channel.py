import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.use_cases.add_youtube_channel import (
    AddYouTubeChannelUseCase,
    AddYouTubeCommand,
)
from src.domain.entities.guild_config import GuildConfig
from src.domain.entities.youtube_channel import YouTubeChannel
from src.domain.exceptions.domain_exceptions import (
    ChannelNotFoundError,
    ChannelNotConfiguredError,
    ChannelLimitReachedError,
)


@pytest.fixture
def mock_youtube_repo():
    return AsyncMock()


@pytest.fixture
def mock_guild_repo():
    return AsyncMock()


@pytest.fixture
def mock_youtube_service():
    svc = AsyncMock()
    svc.channel_exists.return_value = True
    svc.get_channel_details.return_value = {
        "title": "Test Channel",
        "description": "A test channel",
        "subscriber_count": 100,
        "view_count": 5000,
        "thumbnail": "https://example.com/thumb.jpg",
    }
    return svc


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def use_case(mock_youtube_repo, mock_guild_repo, mock_youtube_service, mock_logger):
    return AddYouTubeChannelUseCase(
        youtube_repo=mock_youtube_repo,
        guild_repo=mock_guild_repo,
        youtube_service=mock_youtube_service,
        logger=mock_logger,
    )


def make_guild_config(
    guild_id=1,
    announcement_channel_id=111,
    youtube_channel_id=None,
    youtube_live_channel_id=None,
    streamer_limit=15,
):
    return GuildConfig(
        guild_id=guild_id,
        announcement_channel_id=announcement_channel_id,
        youtube_channel_id=youtube_channel_id,
        youtube_live_channel_id=youtube_live_channel_id,
        streamer_limit=streamer_limit,
    )


class TestAddYouTubeChannelUseCase:
    @pytest.mark.asyncio
    async def test_add_channel_with_announcement_channel(self, use_case, mock_guild_repo, mock_youtube_repo):
        mock_guild_repo.get_by_id.return_value = make_guild_config(
            announcement_channel_id=111
        )
        mock_youtube_repo.count_by_guild.return_value = 0
        mock_youtube_repo.add.return_value = YouTubeChannel(
            guild_id=1, channel_id="UCtest", id=42
        )

        result = await use_case.execute(
            AddYouTubeCommand(
                guild_id=1,
                channel_id="UCtest",
                custom_message="New video!",
                mention_type="ninguno",
            )
        )

        assert result.id == 42
        assert result.channel_id == "UCtest"

    @pytest.mark.asyncio
    async def test_add_channel_with_youtube_channel_only(self, use_case, mock_guild_repo, mock_youtube_repo):
        mock_guild_repo.get_by_id.return_value = make_guild_config(
            announcement_channel_id=None,
            youtube_channel_id=222,
        )
        mock_youtube_repo.count_by_guild.return_value = 0
        mock_youtube_repo.add.return_value = YouTubeChannel(
            guild_id=1, channel_id="UCtest", id=43
        )

        result = await use_case.execute(
            AddYouTubeCommand(
                guild_id=1,
                channel_id="UCtest",
                custom_message="New video!",
                mention_type="ninguno",
            )
        )

        assert result.id == 43

    @pytest.mark.asyncio
    async def test_add_channel_with_youtube_live_channel_only(self, use_case, mock_guild_repo, mock_youtube_repo):
        mock_guild_repo.get_by_id.return_value = make_guild_config(
            announcement_channel_id=None,
            youtube_channel_id=None,
            youtube_live_channel_id=333,
        )
        mock_youtube_repo.count_by_guild.return_value = 0
        mock_youtube_repo.add.return_value = YouTubeChannel(
            guild_id=1, channel_id="UCtest", id=44
        )

        result = await use_case.execute(
            AddYouTubeCommand(
                guild_id=1,
                channel_id="UCtest",
                custom_message="New video!",
                mention_type="ninguno",
            )
        )

        assert result.id == 44

    @pytest.mark.asyncio
    async def test_add_channel_no_channel_configured_raises_error(self, use_case, mock_guild_repo):
        mock_guild_repo.get_by_id.return_value = make_guild_config(
            announcement_channel_id=None,
            youtube_channel_id=None,
            youtube_live_channel_id=None,
        )

        with pytest.raises(ChannelNotConfiguredError):
            await use_case.execute(
                AddYouTubeCommand(
                    guild_id=1,
                    channel_id="UCtest",
                    custom_message="New video!",
                    mention_type="ninguno",
                )
            )

    @pytest.mark.asyncio
    async def test_channel_not_found_in_youtube(self, use_case, mock_youtube_service):
        mock_youtube_service.channel_exists.return_value = False

        with pytest.raises(ChannelNotFoundError):
            await use_case.execute(
                AddYouTubeCommand(
                    guild_id=1,
                    channel_id="UCnonexistent",
                    custom_message="New video!",
                    mention_type="ninguno",
                )
            )

    @pytest.mark.asyncio
    async def test_channel_limit_reached(self, use_case, mock_guild_repo, mock_youtube_repo):
        mock_guild_repo.get_by_id.return_value = make_guild_config(
            announcement_channel_id=111,
            streamer_limit=5,
        )
        mock_youtube_repo.count_by_guild.return_value = 5

        with pytest.raises(ChannelLimitReachedError):
            await use_case.execute(
                AddYouTubeCommand(
                    guild_id=1,
                    channel_id="UCtest",
                    custom_message="New video!",
                    mention_type="ninguno",
                )
            )

    @pytest.mark.asyncio
    async def test_resolve_username_success(self, use_case, mock_youtube_service):
        mock_youtube_service.username_to_channel_id.return_value = "UCresolved"

        result = await use_case.resolve_username("@testchannel")
        assert result == "UCresolved"
        mock_youtube_service.username_to_channel_id.assert_called_once_with("@testchannel")

    @pytest.mark.asyncio
    async def test_resolve_username_not_found(self, use_case, mock_youtube_service):
        mock_youtube_service.username_to_channel_id.return_value = None

        with pytest.raises(ChannelNotFoundError):
            await use_case.resolve_username("@unknown")
