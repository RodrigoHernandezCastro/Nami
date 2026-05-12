# src/domain/value_objects/jankenpon_move.py
from __future__ import annotations
from enum import Enum
import random


class Move(str, Enum):
    """Las 3 jugadas válidas de Jankenpon (piedra/papel/tijera)."""
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

    @classmethod
    def random(cls) -> "Move":
        """Devuelve una jugada aleatoria — usada por el bot."""
        return random.choice(list(cls))


class GameResult(str, Enum):
    """Resultado de una partida desde la perspectiva del usuario."""
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


# Tabla de qué le gana a qué (regla de dominio pura).
# La clave gana a su valor.
_BEATS = {
    Move.ROCK: Move.SCISSORS,
    Move.PAPER: Move.ROCK,
    Move.SCISSORS: Move.PAPER,
}


def resolve(user_move: Move, bot_move: Move) -> GameResult:
    """
    Resuelve una partida desde la perspectiva del usuario.
    Función pura, sin efectos secundarios.
    """
    if user_move == bot_move:
        return GameResult.DRAW
    if _BEATS[user_move] == bot_move:
        return GameResult.WIN
    return GameResult.LOSS