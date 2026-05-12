# src/application/use_cases/play_jankenpon.py
from dataclasses import dataclass

from src.application.interfaces.logger import ILogger
from src.application.interfaces.user_xp_repository import IUserXPRepository
from src.domain.value_objects.jankenpon_move import (
    GameResult,
    Move,
    resolve,
)
from src.domain.value_objects.level import level_from_xp, xp_to_next_level


@dataclass
class PlayJankenponCommand:
    user_id: int
    guild_id: int
    user_move: Move


@dataclass
class PlayJankenponResult:
    """
    DTO de salida con todo lo que la capa de presentación necesita
    para renderizar el embed sin pedir nada más al dominio.
    """
    user_move: Move
    bot_move: Move
    result: GameResult

    xp_before: int
    xp_after: int
    xp_delta: int   # delta REAL (puede ser 0 en derrota si ya estaba en 0)

    level_before: int
    level_after: int
    leveled_up: bool

    xp_to_next: int
    games_played: int
    wins: int
    losses: int
    draws: int


class PlayJankenponUseCase:
    """
    Caso de uso: jugar una partida de Jankenpon.

    Reglas de negocio:
    - Bot juega aleatorio.
    - Ganar = +2 xp, Empate = +1 xp, Perder = -1 xp.
    - XP nunca baja de 0 (lo garantiza la entidad UserXP).
    - El nivel se calcula desde la xp; subir de nivel se detecta comparando
      nivel antes vs después de aplicar el delta.
    """

    def __init__(
        self,
        user_xp_repo: IUserXPRepository,
        logger: ILogger,
    ) -> None:
        self._repo = user_xp_repo
        self._logger = logger

    async def execute(
        self, command: PlayJankenponCommand
    ) -> PlayJankenponResult:
        # 1. Cargar / crear el registro del usuario en este guild
        entry = await self._repo.get_or_create(
            user_id=command.user_id,
            guild_id=command.guild_id,
        )

        xp_before = entry.xp
        level_before = level_from_xp(xp_before)

        # 2. Bot tira y se resuelve la partida
        bot_move = Move.random()
        result = resolve(command.user_move, bot_move)

        # 3. Aplicar resultado a la entidad (la entidad encapsula la regla
        #    de "no bajar de 0" y los contadores).
        if result is GameResult.WIN:
            xp_delta = entry.add_win()
        elif result is GameResult.LOSS:
            xp_delta = entry.add_loss()
        else:  # DRAW
            xp_delta = entry.add_draw()

        # 4. Persistir
        await self._repo.update(entry)

        # 5. Calcular nivel después
        level_after = level_from_xp(entry.xp)
        leveled_up = level_after > level_before

        # 6. Logging
        self._logger.info(
            "jankenpon_played",
            user_id=command.user_id,
            guild_id=command.guild_id,
            user_move=command.user_move.value,
            bot_move=bot_move.value,
            result=result.value,
            xp_delta=xp_delta,
            xp_after=entry.xp,
            leveled_up=leveled_up,
        )

        # 7. Devolver DTO completo
        return PlayJankenponResult(
            user_move=command.user_move,
            bot_move=bot_move,
            result=result,
            xp_before=xp_before,
            xp_after=entry.xp,
            xp_delta=xp_delta,
            level_before=level_before,
            level_after=level_after,
            leveled_up=leveled_up,
            xp_to_next=xp_to_next_level(entry.xp),
            games_played=entry.games_played,
            wins=entry.wins,
            losses=entry.losses,
            draws=entry.draws,
        )