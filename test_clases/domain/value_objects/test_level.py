import pytest
from src.domain.value_objects.level import (
    level_from_xp,
    xp_for_level,
    xp_to_next_level,
    XP_PER_LEVEL,
)


class TestLevel:
    def test_xp_per_level_constant(self):
        assert XP_PER_LEVEL == 50

    def test_level_0_below_50(self):
        for xp in range(0, 50):
            assert level_from_xp(xp) == 0

    def test_level_1_at_50_xp(self):
        assert level_from_xp(50) == 1

    def test_level_1_up_to_99(self):
        for xp in range(50, 100):
            assert level_from_xp(xp) == 1

    def test_level_2_at_100(self):
        assert level_from_xp(100) == 2

    def test_negative_xp_returns_0(self):
        assert level_from_xp(-1) == 0
        assert level_from_xp(-100) == 0

    def test_high_levels(self):
        assert level_from_xp(500) == 10
        assert level_from_xp(1000) == 20

    def test_xp_for_level(self):
        assert xp_for_level(0) == 0
        assert xp_for_level(1) == 50
        assert xp_for_level(2) == 100
        assert xp_for_level(10) == 500

    def test_xp_for_level_negative(self):
        assert xp_for_level(-1) == 0

    def test_xp_to_next_level_from_zero(self):
        assert xp_to_next_level(0) == 50

    def test_xp_to_next_level_mid_level(self):
        assert xp_to_next_level(10) == 40
        assert xp_to_next_level(49) == 1
        assert xp_to_next_level(50) == 50

    def test_xp_to_next_level_exact_boundary(self):
        assert xp_to_next_level(0) == 50
        assert xp_to_next_level(50) == 50
        assert xp_to_next_level(100) == 50

    def test_roundtrip_level_to_xp_to_level(self):
        for level in range(0, 20):
            xp = xp_for_level(level)
            assert level_from_xp(xp) == level
