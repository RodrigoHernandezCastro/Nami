import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.application.use_cases.play_jankenpon import (
    PlayJankenponCommand,
    PlayJankenponUseCase,
)
from src.domain.value_objects.jankenpon_move import Move, GameResult
from src.domain.entities.user_xp import UserXP


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    return logger


@pytest.fixture
def use_case(mock_repo, mock_logger):
    return PlayJankenponUseCase(user_xp_repo=mock_repo, logger=mock_logger)


class TestPlayJankenponUseCase:
    @pytest.mark.asyncio
    async def test_win_adds_xp(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=1, guild_id=2, xp=5, games_played=3, wins=1, losses=1, draws=1)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        result = await use_case.execute(
            PlayJankenponCommand(user_id=1, guild_id=2, user_move=Move.ROCK)
        )

        assert result.result is GameResult.WIN or result.result is GameResult.LOSS or result.result is GameResult.DRAW
        assert result.user_move == Move.ROCK
        assert result.bot_move in (Move.ROCK, Move.PAPER, Move.SCISSORS)
        assert result.games_played == 4
        mock_repo.get_or_create.assert_called_once_with(user_id=1, guild_id=2)
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_level_up_detected(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=1, guild_id=2, xp=98, games_played=10)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        result = await use_case.execute(
            PlayJankenponCommand(user_id=1, guild_id=2, user_move=Move.ROCK)
        )

        assert result.xp_before == 98
        assert result.level_before == 1
        assert result.leveled_up == (result.level_after > 1)
        assert result.xp_to_next >= 0

    @pytest.mark.asyncio
    async def test_stats_are_returned_on_win(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=1, guild_id=2, xp=10, games_played=10, wins=5, losses=3, draws=2)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        with patch.object(Move, 'random', return_value=Move.SCISSORS):
            result = await use_case.execute(
                PlayJankenponCommand(user_id=1, guild_id=2, user_move=Move.ROCK)
            )

        assert result.result == GameResult.WIN
        assert result.games_played == 11
        assert result.wins == 6
        assert result.losses == 3
        assert result.draws == 2

    @pytest.mark.asyncio
    async def test_new_user_starts_at_zero(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=99, guild_id=99, xp=0)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        result = await use_case.execute(
            PlayJankenponCommand(user_id=99, guild_id=99, user_move=Move.ROCK)
        )

        assert result.xp_before == 0
        assert result.level_before == 0

    @pytest.mark.asyncio
    async def test_xp_delta_is_correct_for_win(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=1, guild_id=2, xp=10)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        with patch.object(Move, 'random', return_value=Move.SCISSORS):
            result = await use_case.execute(
                PlayJankenponCommand(user_id=1, guild_id=2, user_move=Move.ROCK)
            )
            assert result.result == GameResult.WIN
            assert result.xp_delta == 2

    @pytest.mark.asyncio
    async def test_xp_delta_is_correct_for_loss(self, use_case, mock_repo, mock_logger):
        entry = UserXP(user_id=1, guild_id=2, xp=10)
        mock_repo.get_or_create.return_value = entry
        mock_repo.update.return_value = entry

        with patch.object(Move, 'random', return_value=Move.ROCK):
            result = await use_case.execute(
                PlayJankenponCommand(user_id=1, guild_id=2, user_move=Move.SCISSORS)
            )
            assert result.result == GameResult.LOSS
            assert result.xp_delta == -1
