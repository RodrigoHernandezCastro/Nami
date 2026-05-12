# src/presentation/discord_bot/jankenpon_parser.py
"""
Parser del input del usuario para !jankenpon <jugada>.

Acepta sinónimos en los 4 idiomas soportados, alias cortos y emojis.
Es lógica de presentación pura: parsea texto → Move. No tiene reglas
de negocio.

Decisión: este mapeo vive en código y NO en los JSON de i18n porque
los JSON están pensados para CONTENIDO mostrado al usuario, no para
diccionarios de parsing inverso. Mantenerlo aquí lo hace simple de
extender sin tocar la capa de application.
"""
from __future__ import annotations
from typing import Dict, Optional

from src.domain.value_objects.jankenpon_move import Move


# Todas las claves se normalizan a lowercase antes de buscar.
_ALIASES: Dict[str, Move] = {
    # ---- ROCK ----
    "rock": Move.ROCK,
    "r": Move.ROCK,
    "🪨": Move.ROCK,
    "✊": Move.ROCK,
    "piedra": Move.ROCK,        # es
    "p": Move.ROCK,             # choca con paper si se usa solo, ver nota
    "kamien": Move.ROCK,        # pl (sin diacríticos)
    "kamień": Move.ROCK,        # pl
    "kam": Move.ROCK,
    "グー": Move.ROCK,           # ja (gū)
    "gu": Move.ROCK,
    "guu": Move.ROCK,
    "ぐー": Move.ROCK,

    # ---- PAPER ----
    "paper": Move.PAPER,
    "papel": Move.PAPER,        # es
    "papier": Move.PAPER,       # pl
    "pap": Move.PAPER,
    "📄": Move.PAPER,
    "✋": Move.PAPER,
    "パー": Move.PAPER,          # ja (pā)
    "pa": Move.PAPER,
    "paa": Move.PAPER,
    "ぱー": Move.PAPER,

    # ---- SCISSORS ----
    "scissors": Move.SCISSORS,
    "tijera": Move.SCISSORS,    # es
    "tijeras": Move.SCISSORS,
    "t": Move.SCISSORS,
    "tij": Move.SCISSORS,
    "nozyce": Move.SCISSORS,    # pl (sin diacríticos)
    "nożyce": Move.SCISSORS,    # pl
    "noz": Move.SCISSORS,
    "✂️": Move.SCISSORS,
    "✂": Move.SCISSORS,
    "チョキ": Move.SCISSORS,      # ja (choki)
    "choki": Move.SCISSORS,
    "ちょき": Move.SCISSORS,
}

# Nota: "p" es ambiguo (paper en inglés / piedra en español). Si lo
# resolvemos como PAPER por defecto, los hispanohablantes que escriban
# "!jankenpon p" pensando en "piedra" se confundirán. Lo quitamos para
# forzar a usar al menos "pa" o "pi".
_ALIASES.pop("p", None)
_ALIASES["pi"] = Move.ROCK   # piedra
_ALIASES["pa"] = Move.PAPER  # paper / papel / papier (inequívoco)


def parse_move(raw: str) -> Optional[Move]:
    """
    Devuelve el Move correspondiente al input del usuario o None si no
    se reconoce. La normalización es: strip + lowercase. Los emojis se
    comparan tal cual (ya están en su forma canónica Unicode).
    """
    if not raw:
        return None
    normalized = raw.strip().lower()
    return _ALIASES.get(normalized)


def valid_examples() -> str:
    """Devuelve una lista corta de ejemplos válidos para mostrar al usuario."""
    return "rock, paper, scissors, piedra, papel, tijera, 🪨, 📄, ✂️"