# src/domain/entities/user_xp.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserXP:
    """
    Representa la progresión de XP de un usuario en un servidor concreto.
    El leaderboard global se calcula agregando filas por user_id en el repo.

    XP nunca baja de 0 (regla de dominio). El nivel se calcula de forma
    derivada con el value object `Level`, no se persiste.
    """
    user_id: int
    guild_id: int
    xp: int = 0
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    id: Optional[int] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_win(self, xp_delta: int = 2) -> int:
        """Aplica una victoria. Devuelve el delta real de XP aplicado."""
        self.xp += xp_delta
        self.wins += 1
        self.games_played += 1
        return xp_delta

    def add_loss(self, xp_delta: int = -1) -> int:
        """
        Aplica una derrota. La XP nunca baja de 0, así que el delta real
        puede ser menor que el solicitado si el usuario está cerca de 0.
        """
        before = self.xp
        self.xp = max(0, self.xp + xp_delta)
        self.losses += 1
        self.games_played += 1
        return self.xp - before  # delta real (puede ser 0 si ya estaba en 0)

    def add_draw(self, xp_delta: int = 1) -> int:
        """Aplica un empate."""
        self.xp += xp_delta
        self.draws += 1
        self.games_played += 1
        return xp_delta