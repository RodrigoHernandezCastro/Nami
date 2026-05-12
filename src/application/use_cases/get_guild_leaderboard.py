# src/application/use_cases/get_guild_leaderboard.py
from dataclasses import dataclass
from typing import List

from src.application.interfaces.user_xp_repository import IUserXPRepository
from src.domain.entities.user_xp import UserXP
from src.domain.value_objects.level import level_from_xp


@dataclass
class GuildLeaderboardQuery:
    guild_id: int
    limit: int = 5


@dataclass
class LeaderboardRow:
    """Fila renderizable: ya trae el nivel calculado."""
    rank: int
    user_id: int
    xp: int
    level: int
    games_played: int
    wins: int
    losses: int
    draws: int


@dataclass
class GuildLeaderboardResult:
    guild_id: int
    rows: List[LeaderboardRow]


class GetGuildLeaderboardUseCase:
    """Query: top N de un servidor por XP descendente."""

    def __init__(self, user_xp_repo: IUserXPRepository) -> None:
        self._repo = user_xp_repo

    async def execute(
        self, query: GuildLeaderboardQuery
    ) -> GuildLeaderboardResult:
        entries: List[UserXP] = await self._repo.top_by_guild(
            guild_id=query.guild_id,
            limit=query.limit,
        )
        rows = [
            LeaderboardRow(
                rank=i + 1,
                user_id=e.user_id,
                xp=e.xp,
                level=level_from_xp(e.xp),
                games_played=e.games_played,
                wins=e.wins,
                losses=e.losses,
                draws=e.draws,
            )
            for i, e in enumerate(entries)
        ]
        return GuildLeaderboardResult(guild_id=query.guild_id, rows=rows)