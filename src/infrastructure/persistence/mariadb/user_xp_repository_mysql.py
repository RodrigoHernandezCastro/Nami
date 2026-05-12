# src/infrastructure/persistence/mariadb/user_xp_repository_mysql.py
from typing import List

import aiomysql

from src.application.interfaces.user_xp_repository import (
    GlobalLeaderboardEntry,
    IUserXPRepository,
)
from src.domain.entities.user_xp import UserXP


class MariaDBUserXPRepository(IUserXPRepository):
    """
    Implementación MariaDB de IUserXPRepository.

    Notas:
    - `get_or_create` usa INSERT ... ON DUPLICATE KEY UPDATE para que sea
      atómico bajo concurrencia (dos partidas simultáneas del mismo usuario
      no crean filas duplicadas gracias al UNIQUE KEY).
    - `update` hace UPDATE explícito por (user_id, guild_id) en vez de por
      `id` para no depender de que la entidad tenga id seteado tras un
      get_or_create vía UPSERT.
    """

    def __init__(self, pool: aiomysql.Pool) -> None:
        self._pool = pool

    async def get_or_create(self, user_id: int, guild_id: int) -> UserXP:
        # UPSERT atómico: si la fila no existe la crea con xp=0.
        # ON DUPLICATE KEY UPDATE id=id es un no-op intencional (mantiene
        # la fila intacta) que activa la rama UPDATE para evitar el error
        # de duplicado.
        upsert_sql = """
            INSERT INTO user_xp (user_id, guild_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE id = id;
        """
        select_sql = """
            SELECT id, user_id, guild_id, xp, games_played,
                   wins, losses, draws, updated_at
            FROM user_xp
            WHERE user_id = %s AND guild_id = %s
            LIMIT 1;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(upsert_sql, (user_id, guild_id))

            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(select_sql, (user_id, guild_id))
                row = await cur.fetchone()

        return self._row_to_entity(row)

    async def update(self, entry: UserXP) -> UserXP:
        sql = """
            UPDATE user_xp
            SET xp = %s,
                games_played = %s,
                wins = %s,
                losses = %s,
                draws = %s
            WHERE user_id = %s AND guild_id = %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    sql,
                    (
                        entry.xp,
                        entry.games_played,
                        entry.wins,
                        entry.losses,
                        entry.draws,
                        entry.user_id,
                        entry.guild_id,
                    ),
                )
        return entry

    async def top_by_guild(
        self, guild_id: int, limit: int = 5
    ) -> List[UserXP]:
        sql = """
            SELECT id, user_id, guild_id, xp, games_played,
                   wins, losses, draws, updated_at
            FROM user_xp
            WHERE guild_id = %s
            ORDER BY xp DESC, games_played DESC
            LIMIT %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (guild_id, limit))
                rows = await cur.fetchall()
        return [self._row_to_entity(r) for r in rows]

    async def top_global(
        self, limit: int = 5
    ) -> List[GlobalLeaderboardEntry]:
        # Suma de XP por usuario a través de todos los guilds.
        sql = """
            SELECT user_id,
                   SUM(xp)            AS total_xp,
                   SUM(games_played)  AS total_games
            FROM user_xp
            GROUP BY user_id
            ORDER BY total_xp DESC, total_games DESC
            LIMIT %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (limit,))
                rows = await cur.fetchall()
        return [
            GlobalLeaderboardEntry(
                user_id=int(r["user_id"]),
                total_xp=int(r["total_xp"] or 0),
                total_games=int(r["total_games"] or 0),
            )
            for r in rows
        ]

    @staticmethod
    def _row_to_entity(row: dict) -> UserXP:
        return UserXP(
            id=row["id"],
            user_id=int(row["user_id"]),
            guild_id=int(row["guild_id"]),
            xp=int(row["xp"]),
            games_played=int(row["games_played"]),
            wins=int(row["wins"]),
            losses=int(row["losses"]),
            draws=int(row["draws"]),
            updated_at=row["updated_at"],
        )