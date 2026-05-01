import asyncpg
import json
from typing import List
from src.application.interfaces import logger
from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository


class PostgresYouTubeRepository(IYouTubeRepository):
    """Repositorio PostgreSQL para canales YouTube."""

    def __init__(self, pool: asyncpg.Pool, logger: None) -> None:
        self._pool = pool
        self._logger = logger

    async def add(self, channel: YouTubeChannel) -> YouTubeChannel:
        query = """
            INSERT INTO youtube_channels
                (guild_id, channel_id, channel_name, custom_message, mention_type,
                mention_role_ids, added_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                channel.guild_id,
                channel.channel_id,
                channel.channel_name,
                channel.custom_message,
                channel.mention_type,
                json.dumps(channel.mention_role_ids or []),
                channel.added_at,
            )
            channel.id = row["id"]
            return channel

    async def remove(self, guild_id: int, channel_id: str) -> bool:
        query = """
            DELETE FROM youtube_channels
            WHERE guild_id = $1 AND channel_id = $2
            RETURNING id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, guild_id, channel_id)
            return row is not None

    async def find_by_guild(self, guild_id: int) -> List[YouTubeChannel]:
        query = """
            SELECT * FROM youtube_channels 
            WHERE guild_id = $1 
            ORDER BY channel_id;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, guild_id)
            return [self._row_to_entity(r) for r in rows]

    async def find_all_with_channel(self) -> List[YouTubeChannel]:
        query = """
            SELECT y.* FROM youtube_channels y
            INNER JOIN guild_configs g ON y.guild_id = g.guild_id
            WHERE g.announcement_channel_id IS NOT NULL;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_entity(r) for r in rows]

    async def count_by_guild(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) FROM youtube_channels WHERE guild_id = $1;"
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(query, guild_id)
            return int(count) if count is not None else 0

    async def update_last_video(self, channel_id: int, video_id: str) -> bool:
        """Actualiza last_announced_video_id y VERIFICA que se guardó."""
        query = """
            UPDATE youtube_channels 
            SET last_announced_video_id = $1 
            WHERE id = $2
            RETURNING last_announced_video_id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, video_id, channel_id)
            if row and self._logger:
                self._logger.debug("youtube_last_video_updated", channel_id=channel_id, video_id=video_id)
            if row and row["last_announced_video_id"] == video_id:
                return True
            else:
                return False

    async def update_video_history(self, channel_id: int, video_id: str) -> bool:
        """Añade video al historial (últimos 5)."""
        query = """
            UPDATE youtube_channels 
            SET announced_video_history = (
                SELECT jsonb_agg(new_history ORDER BY idx)[:5]
                FROM (
                    SELECT elem, ROW_NUMBER() OVER() as idx
                    FROM jsonb_array_elements(announced_video_history || $2::jsonb) elem
                ) t
            )
            WHERE id = $1
            RETURNING announced_video_history;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, channel_id, json.dumps([video_id]))
            return bool(row)

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> YouTubeChannel:
        role_ids = json.loads(row["mention_role_ids"] or "[]")
        return YouTubeChannel(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            channel_name=row["channel_name"],
            custom_message=row["custom_message"],
            mention_type=row["mention_type"],
            mention_role_ids=role_ids,
            last_announced_video_id=row["last_announced_video_id"],
            added_at=row["added_at"],
            announced_video_history=[str(v) for v in row["announced_video_history"] or []],

        )