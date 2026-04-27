import asyncpg
import json
from typing import List, Optional
from src.domain.entities.streamer import Streamer
from src.domain.exceptions.domain_exceptions import StreamerAlreadyExistsError
from src.application.interfaces.streamer_repository import IStreamerRepository


class PostgresStreamerRepository(IStreamerRepository):
    """
    Adaptador concreto: traduce entre el modelo de dominio
    y el esquema de PostgreSQL. Único lugar con SQL.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add(self, streamer: Streamer) -> Streamer:
        query = """
            INSERT INTO streamers
                (guild_id, username, custom_message, mention_type,
                 mention_role_ids, is_online, added_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id;
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    streamer.guild_id,
                    streamer.username,
                    streamer.custom_message,
                    streamer.mention_type,
                    json.dumps(streamer.mention_role_ids or []),
                    streamer.is_online,
                    streamer.added_at,
                )
                streamer.id = row["id"]
                return streamer
        except asyncpg.UniqueViolationError as e:
            raise StreamerAlreadyExistsError(
                f"'{streamer.username}' ya existe en este servidor."
            ) from e

    async def remove(self, guild_id: int, username: str) -> bool:
        query = """
            DELETE FROM streamers
            WHERE guild_id = $1 AND username = $2
            RETURNING id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, guild_id, username.lower())
            return row is not None

    async def find_by_guild(self, guild_id: int) -> List[Streamer]:
        query = "SELECT * FROM streamers WHERE guild_id = $1 ORDER BY username;"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, guild_id)
            return [self._row_to_entity(r) for r in rows]

    async def find_all_with_channel(self) -> List[Streamer]:
        query = """
            SELECT s.* FROM streamers s
            INNER JOIN guild_configs g ON s.guild_id = g.guild_id
            WHERE g.announcement_channel_id IS NOT NULL;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_entity(r) for r in rows]

    async def count_by_guild(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) FROM streamers WHERE guild_id = $1;"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, guild_id)

    async def update_status(self, streamer_id: int, is_online: bool) -> None:
        query = "UPDATE streamers SET is_online = $1 WHERE id = $2;"
        async with self._pool.acquire() as conn:
            await conn.execute(query, is_online, streamer_id)

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Streamer:
        role_ids = json.loads(row["mention_role_ids"] or "[]")
        return Streamer(
            id=row["id"],
            guild_id=row["guild_id"],
            username=row["username"],
            custom_message=row["custom_message"],
            mention_type=row["mention_type"],
            mention_role_ids=role_ids,
            is_online=row["is_online"],
            added_at=row["added_at"],
        )