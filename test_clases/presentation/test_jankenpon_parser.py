import pytest
from src.presentation.discord_bot.jankenpon_parser import parse_move, valid_examples
from src.domain.value_objects.jankenpon_move import Move


class TestParseMove:
    def test_rock_aliases(self):
        assert parse_move("rock") == Move.ROCK
        assert parse_move("r") == Move.ROCK
        assert parse_move("piedra") == Move.ROCK
        assert parse_move("kamien") == Move.ROCK
        assert parse_move("kamień") == Move.ROCK
        assert parse_move("kam") == Move.ROCK
        assert parse_move("グー") == Move.ROCK
        assert parse_move("gu") == Move.ROCK
        assert parse_move("guu") == Move.ROCK
        assert parse_move("ぐー") == Move.ROCK
        assert parse_move("pi") == Move.ROCK

    def test_paper_aliases(self):
        assert parse_move("paper") == Move.PAPER
        assert parse_move("papel") == Move.PAPER
        assert parse_move("papier") == Move.PAPER
        assert parse_move("pap") == Move.PAPER
        assert parse_move("パー") == Move.PAPER
        assert parse_move("pa") == Move.PAPER
        assert parse_move("paa") == Move.PAPER
        assert parse_move("ぱー") == Move.PAPER

    def test_scissors_aliases(self):
        assert parse_move("scissors") == Move.SCISSORS
        assert parse_move("tijera") == Move.SCISSORS
        assert parse_move("tijeras") == Move.SCISSORS
        assert parse_move("t") == Move.SCISSORS
        assert parse_move("tij") == Move.SCISSORS
        assert parse_move("nozyce") == Move.SCISSORS
        assert parse_move("nożyce") == Move.SCISSORS
        assert parse_move("noz") == Move.SCISSORS
        assert parse_move("チョキ") == Move.SCISSORS
        assert parse_move("choki") == Move.SCISSORS
        assert parse_move("ちょき") == Move.SCISSORS

    def test_emoji_aliases(self):
        assert parse_move("🪨") == Move.ROCK
        assert parse_move("✊") == Move.ROCK
        assert parse_move("📄") == Move.PAPER
        assert parse_move("✋") == Move.PAPER
        assert parse_move("✂️") == Move.SCISSORS
        assert parse_move("✂") == Move.SCISSORS

    def test_ambiguous_p_is_removed(self):
        assert parse_move("p") is None

    def test_case_insensitive(self):
        assert parse_move("ROCK") == Move.ROCK
        assert parse_move("PiEdRa") == Move.ROCK
        assert parse_move("PapEL") == Move.PAPER

    def test_whitespace_stripped(self):
        assert parse_move("  rock  ") == Move.ROCK
        assert parse_move("\tpaper\n") == Move.PAPER

    def test_empty_input(self):
        assert parse_move("") is None
        assert parse_move(None) is None
        assert parse_move("   ") is None

    def test_garbage_input(self):
        assert parse_move("asdfgh") is None
        assert parse_move("12345") is None
        assert parse_move("!@#$%") is None

    def test_valid_examples_contains_expected(self):
        examples = valid_examples()
        assert "rock" in examples
        assert "paper" in examples
        assert "scissors" in examples
        assert "piedra" in examples
        assert "🪨" not in examples
        assert "📄" not in examples
        assert "✂️" not in examples
