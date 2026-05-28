import pytest
from src.domain.value_objects.jankenpon_move import Move, GameResult, resolve, _BEATS


class TestMove:
    def test_random_returns_valid_move(self):
        for _ in range(100):
            m = Move.random()
            assert m in (Move.ROCK, Move.PAPER, Move.SCISSORS)

    def test_random_is_not_always_same(self):
        results = {Move.random() for _ in range(100)}
        assert len(results) > 1

    def test_str_values(self):
        assert Move.ROCK.value == "rock"
        assert Move.PAPER.value == "paper"
        assert Move.SCISSORS.value == "scissors"


class TestResolve:
    def test_same_move_is_draw(self):
        for move in Move:
            assert resolve(move, move) == GameResult.DRAW

    def test_rock_beats_scissors(self):
        assert resolve(Move.ROCK, Move.SCISSORS) == GameResult.WIN
        assert resolve(Move.SCISSORS, Move.ROCK) == GameResult.LOSS

    def test_scissors_beats_paper(self):
        assert resolve(Move.SCISSORS, Move.PAPER) == GameResult.WIN
        assert resolve(Move.PAPER, Move.SCISSORS) == GameResult.LOSS

    def test_paper_beats_rock(self):
        assert resolve(Move.PAPER, Move.ROCK) == GameResult.WIN
        assert resolve(Move.ROCK, Move.PAPER) == GameResult.LOSS

    def test_all_combinations_exhaustive(self):
        for user_move in Move:
            for bot_move in Move:
                result = resolve(user_move, bot_move)
                if user_move == bot_move:
                    assert result == GameResult.DRAW
                elif _BEATS[user_move] == bot_move:
                    assert result == GameResult.WIN
                else:
                    assert result == GameResult.LOSS
