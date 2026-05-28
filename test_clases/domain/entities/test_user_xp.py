import pytest
from src.domain.entities.user_xp import UserXP


class TestUserXP:
    @pytest.fixture
    def entry(self):
        return UserXP(user_id=12345, guild_id=67890)

    def test_default_values(self, entry):
        assert entry.xp == 0
        assert entry.games_played == 0
        assert entry.wins == 0
        assert entry.losses == 0
        assert entry.draws == 0

    def test_add_win(self, entry):
        delta = entry.add_win()
        assert delta == 2
        assert entry.xp == 2
        assert entry.wins == 1
        assert entry.games_played == 1

    def test_add_win_custom_delta(self, entry):
        delta = entry.add_win(xp_delta=5)
        assert delta == 5
        assert entry.xp == 5

    def test_add_loss_reduces_xp(self, entry):
        entry.xp = 10
        delta = entry.add_loss()
        assert delta == -1
        assert entry.xp == 9
        assert entry.losses == 1
        assert entry.games_played == 1

    def test_add_loss_never_below_zero(self, entry):
        delta = entry.add_loss()
        assert delta == -1
        assert entry.xp == 0

    def test_add_loss_from_zero_stays_zero(self, entry):
        entry.add_loss()
        entry.add_loss()
        entry.add_loss()
        assert entry.xp == 0
        assert entry.losses == 3
        assert entry.games_played == 3

    def test_add_loss_always_returns_intended_delta(self, entry):
        entry.xp = 0
        delta = entry.add_loss(xp_delta=-1)
        assert delta == -1
        assert entry.xp == 0

        entry.xp = 2
        delta = entry.add_loss(xp_delta=-1)
        assert delta == -1
        assert entry.xp == 1

    def test_add_draw(self, entry):
        delta = entry.add_draw()
        assert delta == 1
        assert entry.xp == 1
        assert entry.draws == 1
        assert entry.games_played == 1

    def test_add_draw_custom_delta(self, entry):
        delta = entry.add_draw(xp_delta=3)
        assert delta == 3
        assert entry.xp == 3

    def test_multiple_games_accumulate(self, entry):
        entry.add_win()
        entry.add_win()
        entry.add_loss()
        entry.add_draw()
        assert entry.xp == 4
        assert entry.games_played == 4
        assert entry.wins == 2
        assert entry.losses == 1
        assert entry.draws == 1

    def test_custom_user_id_and_guild_id(self):
        entry = UserXP(user_id=111, guild_id=222)
        assert entry.user_id == 111
        assert entry.guild_id == 222
