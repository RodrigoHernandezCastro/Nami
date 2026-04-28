import aiomysql
import json
from typing import List
from src.domain.entities.streamer import Streamer
from src.domain.exceptions.domain_exceptions import StreamerAlreadyExistsError
from src.application.interfaces.streamer_repository import IStreamerRepository


class MariaDBStreamerRepository(IStreamerRepository):
    """Adaptador concreto para MariaDB/MySQL."""

    def __init__(self, pool: aiomysql.Pool) -> None:
        self._pool = pool

    async def add(self, streamer: Streamer) -> Streamer:
        query = """
            INSERT INTO streamers
                (guild_id, username, custom_message, mention_type,
                 mention_role_ids, is_online, added_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        query,
                        (
                            streamer.guild_id,
                            streamer.username,
                            streamer.custom_message,
                            streamer.mention_type,
                            json.dumps(streamer.mention_role_ids or []),
                            streamer.is_online,
                            streamer.added_at,
                        ),
                    )
                    streamer.id = cur.lastrowid
                    return streamer
                except aiomysql.IntegrityError as e:
                    # Código 1062 = Duplicate entry
                    if e.args[0] == 1062:
                        raise StreamerAlreadyExistsError(
                            f"'{streamer.username}' ya existe en este servidor."
                        ) from e
                    raise

    async def remove(self, guild_id: int, username: str) -> bool:
        query = "DELETE FROM streamers WHERE guild_id = %s AND username = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (guild_id, username.lower()))
                return cur.rowcount > 0

    async def find_by_guild(self, guild_id: int) -> List[Streamer]:
        query = """
            SELECT id, guild_id, username, custom_message, mention_type,
                   mention_role_ids, is_online, added_at
            FROM streamers
            WHERE guild_id = %s
            ORDER BY username;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                rows = await cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    async def find_all_with_channel(self) -> List[Streamer]:
        query = """
            SELECT s.id, s.guild_id, s.username, s.custom_message,
                   s.mention_type, s.mention_role_ids, s.is_online, s.added_at
            FROM streamers s
            INNER JOIN guild_configs g ON s.guild_id = g.guild_id
            WHERE g.announcement_channel_id IS NOT NULL;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    async def count_by_guild(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) AS total FROM streamers WHERE guild_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                row = await cur.fetchone()
                return row["total"] if row else 0

    async def update_status(self, streamer_id: int, is_online: bool) -> None:
        query = "UPDATE streamers SET is_online = %s WHERE id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (is_online, streamer_id))

    @staticmethod
    def _row_to_entity(row: dict) -> Streamer:
        # MariaDB guarda JSON como string en LONGTEXT → parseamos manualmente
        raw_roles = row.get("mention_role_ids") or "[]"
        try:
            role_ids = json.loads(raw_roles) if isinstance(raw_roles, str) else raw_roles
        except (json.JSONDecodeError, TypeError):
            role_ids = []

        return Streamer(
            id=row["id"],
            guild_id=row["guild_id"],
            username=row["username"],
            custom_message=row["custom_message"],
            mention_type=row["mention_type"],
            mention_role_ids=role_ids,
            is_online=bool(row["is_online"]),
            added_at=row["added_at"],
        )