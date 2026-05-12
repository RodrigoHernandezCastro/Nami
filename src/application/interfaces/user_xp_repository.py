# src/application/interfaces/user_xp_repository.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from src.domain.entities.user_xp import UserXP


@dataclass
class GlobalLeaderboardEntry:
    """
    Entrada del leaderboard global. No es una UserXP porque no pertenece
    a un guild concreto: es la suma agregada de todos los servidores
    en los que el usuario ha jugado.
    """
    user_id: int
    total_xp: int
    total_games: int


class IUserXPRepository(ABC):
    """
    Puerto de persistencia del XP de los usuarios. Una fila por
    (user_id, guild_id). El leaderboard global se obtiene agregando
    en el motor de BD (no en memoria).
    """

    @abstractmethod
    async def get_or_create(self, user_id: int, guild_id: int) -> UserXP:
        """
        Devuelve la fila del usuario en el guild. Si no existe, la crea
        con XP=0 y la persiste antes de devolverla.
        """
        ...

    @abstractmethod
    async def update(self, entry: UserXP) -> UserXP:
        """Persiste cambios en xp, contadores y updated_at."""
        ...

    @abstractmethod
    async def top_by_guild(
        self, guild_id: int, limit: int = 5
    ) -> List[UserXP]:
        """Top de un servidor ordenado por XP descendente."""
        ...

    @abstractmethod
    async def top_global(
        self, limit: int = 5
    ) -> List[GlobalLeaderboardEntry]:
        """
        Top global: agrega XP por user_id sumando todos los guilds.
        Devuelve dataclass `GlobalLeaderboardEntry`.
        """
        ...