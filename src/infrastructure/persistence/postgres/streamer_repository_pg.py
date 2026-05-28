# src/infrastructure/persistence/postgres/streamer_repository_pg.py
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
            raise StreamerAlreadyExistsError(username=streamer.username) from e

    async def update(self, streamer: Streamer) -> Streamer:
        query = """
            UPDATE streamers
            SET custom_message = $1, mention_type = $2, mention_role_ids = $3
            WHERE guild_id = $4 AND LOWER(username) = LOWER($5);
        """
        async with self._pool.acquire() as conn:
            await conn.execute(
                query,
                streamer.custom_message,
                streamer.mention_type,
                json.dumps(streamer.mention_role_ids or []),
                streamer.guild_id,
                streamer.username,
            )
        return streamer

    async def remove(self, guild_id: int, username: str) -> bool:
        query = """
            DELETE FROM streamers
            WHERE guild_id = $1 AND LOWER(username) = LOWER($2)
            RETURNING id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, guild_id, username)
            return row is not None

    async def find_by_guild(self, guild_id: int) -> List[Streamer]:
        query = """
            SELECT * FROM streamers 
            WHERE guild_id = $1 
            ORDER BY username;
        """
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
            count = await conn.fetchval(query, guild_id)
            return int(count) if count is not None else 0

    async def update_status(self, streamer_id: int, is_online: bool) -> None:
        query = """
            UPDATE streamers 
            SET is_online = $1 
            WHERE id = $2;
        """
        async with self._pool.acquire() as conn:
            await conn.execute(query, is_online, streamer_id)

    async def find_by_username(self, username: str) -> Optional[Streamer]:
        """Busca streamer por username (case insensitive)."""
        query = """
            SELECT * FROM streamers 
            WHERE LOWER(username) = LOWER($1) 
            LIMIT 1;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, username)
            return self._row_to_entity(row) if row else None

    async def find_live_streamers(self) -> List[Streamer]:
        """Streamers actualmente en vivo."""
        query = "SELECT * FROM streamers WHERE is_online = true;"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_entity(r) for r in rows]

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Streamer:
        """Convierte fila PG → entidad Streamer."""
        # PostgreSQL guarda JSON como jsonb → json.loads funciona
        role_ids_json = row["mention_role_ids"] or "[]"
        role_ids = json.loads(role_ids_json)

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