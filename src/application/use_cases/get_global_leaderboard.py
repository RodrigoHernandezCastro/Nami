# src/application/use_cases/get_global_leaderboard.py
from dataclasses import dataclass
from typing import List

from src.application.interfaces.user_xp_repository import IUserXPRepository
from src.domain.value_objects.level import level_from_xp


@dataclass
class GlobalLeaderboardQuery:
    limit: int = 5


@dataclass
class GlobalLeaderboardRow:
    rank: int
    user_id: int
    total_xp: int
    level: int
    total_games: int


@dataclass
class GlobalLeaderboardResult:
    rows: List[GlobalLeaderboardRow]


class GetGlobalLeaderboardUseCase:
    """
    Query: top N global. Suma la XP del usuario en todos los servidores
    y ordena descendente. La agregación la hace la BD (más eficiente
    que traer todas las filas y agregar en Python).
    """

    def __init__(self, user_xp_repo: IUserXPRepository) -> None:
        self._repo = user_xp_repo

    async def execute(
        self, query: GlobalLeaderboardQuery
    ) -> GlobalLeaderboardResult:
        entries = await self._repo.top_global(limit=query.limit)
        rows = [
            GlobalLeaderboardRow(
                rank=i + 1,
                user_id=e.user_id,
                total_xp=e.total_xp,
                level=level_from_xp(e.total_xp),
                total_games=e.total_games,
            )
            for i, e in enumerate(entries)
        ]
        return GlobalLeaderboardResult(rows=rows)