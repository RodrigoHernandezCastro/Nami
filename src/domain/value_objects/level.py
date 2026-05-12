# src/domain/value_objects/level.py
"""
Cálculo de nivel a partir de XP.

Fórmula: lineal suave de 50 xp por nivel.
- Nivel 0: 0-49 xp
- Nivel 1: 50-99 xp
- Nivel 2: 100-149 xp
- ...

Es un módulo de funciones puras, no una clase, porque no tiene estado
ni identidad. Si en el futuro cambia la fórmula, solo se toca aquí.
"""

XP_PER_LEVEL = 50


def level_from_xp(xp: int) -> int:
    """Devuelve el nivel actual dado un total de xp."""
    if xp < 0:
        return 0
    return xp // XP_PER_LEVEL


def xp_for_level(level: int) -> int:
    """XP total necesaria para alcanzar exactamente `level`."""
    return max(0, level) * XP_PER_LEVEL


def xp_to_next_level(xp: int) -> int:
    """Cuánta XP falta para subir al siguiente nivel."""
    current = level_from_xp(xp)
    return xp_for_level(current + 1) - xp