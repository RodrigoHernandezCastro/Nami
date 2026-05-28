# src/infrastructure/persistence/mariadb/youtube_repository_mysql.py
import aiomysql
import json
from typing import List, Optional
from src.domain.entities.youtube_channel import YouTubeChannel
from src.application.interfaces.youtube_repository import IYouTubeRepository


class MariaDBYouTubeRepository(IYouTubeRepository):
    """Repositorio MariaDB para canales YouTube."""

    def __init__(self, pool: aiomysql.Pool, logger=None) -> None:
        self._pool = pool
        self._logger = logger

    async def add(self, channel: YouTubeChannel) -> YouTubeChannel:
        query = """
            INSERT INTO youtube_channels
                (guild_id, channel_id, channel_name, custom_message,
                 live_custom_message, mention_type, live_mention_type,
                 mention_role_ids, live_mention_role_ids, added_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    (
                        channel.guild_id,
                        channel.channel_id,
                        channel.channel_name,
                        channel.custom_message,
                        channel.live_custom_message,
                        channel.mention_type,
                        channel.live_mention_type,
                        json.dumps(channel.mention_role_ids or []),
                        json.dumps(channel.live_mention_role_ids) if channel.live_mention_role_ids is not None else None,
                        channel.added_at,
                    ),
                )
                channel.id = cur.lastrowid
                return channel

    async def remove(self, guild_id: int, channel_id: str) -> bool:
        query = "DELETE FROM youtube_channels WHERE guild_id = %s AND channel_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (guild_id, channel_id))
                return cur.rowcount > 0

    async def find_by_guild(self, guild_id: int) -> List[YouTubeChannel]:
        query = """
            SELECT id, guild_id, channel_id, channel_name, custom_message,
                   live_custom_message, mention_type, live_mention_type,
                   mention_role_ids, live_mention_role_ids, last_announced_video_id,
                   announced_video_history, added_at, uploads_playlist_id
            FROM youtube_channels
            WHERE guild_id = %s
            ORDER BY channel_id;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                rows = await cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    async def find_all_with_channel(self) -> List[YouTubeChannel]:
        query = """
            SELECT y.id, y.guild_id, y.channel_id, y.channel_name, y.custom_message,
                   y.live_custom_message, y.mention_type, y.live_mention_type,
                   y.mention_role_ids, y.live_mention_role_ids, y.last_announced_video_id,
                   y.announced_video_history, y.added_at, y.uploads_playlist_id
            FROM youtube_channels y
            INNER JOIN guild_configs g ON y.guild_id = g.guild_id
            WHERE g.announcement_channel_id IS NOT NULL
               OR g.youtube_channel_id IS NOT NULL
               OR g.youtube_live_channel_id IS NOT NULL;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    async def count_by_guild(self, guild_id: int) -> int:
        query = "SELECT COUNT(*) AS total FROM youtube_channels WHERE guild_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                row = await cur.fetchone()
                return row["total"] if row else 0

    async def update_video_history(self, channel_id: int, video_id: str) -> bool:
        select_q = "SELECT announced_video_history FROM youtube_channels WHERE id = %s;"
        update_q = "UPDATE youtube_channels SET announced_video_history = %s WHERE id = %s;"

        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(select_q, (channel_id,))
                row = await cur.fetchone()
                if not row:
                    return False

                raw = row.get("announced_video_history") or "[]"
                try:
                    history: list = json.loads(raw) if isinstance(raw, str) else raw
                except (json.JSONDecodeError, TypeError):
                    history = []

                if video_id not in history:
                    history.insert(0, video_id)
                    history = history[:5]

                await cur.execute(update_q, (json.dumps(history), channel_id))
                return cur.rowcount > 0

    async def update_uploads_playlist_id(self, channel_id: int, playlist_id: str) -> bool:
        query = "UPDATE youtube_channels SET uploads_playlist_id = %s WHERE id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (playlist_id, channel_id))
                return cur.rowcount > 0

    async def update(self, channel: YouTubeChannel) -> YouTubeChannel:
        query = """
            UPDATE youtube_channels
            SET channel_name = %s, custom_message = %s, mention_type = %s,
                mention_role_ids = %s
            WHERE guild_id = %s AND channel_id = %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    (
                        channel.channel_name,
                        channel.custom_message,
                        channel.mention_type,
                        json.dumps(channel.mention_role_ids or []),
                        channel.guild_id,
                        channel.channel_id,
                    ),
                )
        return channel

    async def update_live_settings(
        self, guild_id: int, channel_id: str,
        live_custom_message: Optional[str],
        live_mention_type: Optional[str],
        live_mention_role_ids: Optional[List[int]],
    ) -> bool:
        query = """
            UPDATE youtube_channels
            SET live_custom_message = %s, live_mention_type = %s,
                live_mention_role_ids = %s
            WHERE guild_id = %s AND channel_id = %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    (
                        live_custom_message,
                        live_mention_type,
                        json.dumps(live_mention_role_ids) if live_mention_role_ids is not None else None,
                        guild_id,
                        channel_id,
                    ),
                )
                return cur.rowcount > 0

    @staticmethod
    def _row_to_entity(row: dict) -> YouTubeChannel:
        role_ids = json.loads(row.get("mention_role_ids") or "[]")
        live_role_ids_raw = row.get("live_mention_role_ids")
        live_role_ids = json.loads(live_role_ids_raw) if live_role_ids_raw and live_role_ids_raw != "[]" else None

        raw_history = row.get("announced_video_history") or "[]"
        try:
            history = json.loads(raw_history) if isinstance(raw_history, str) else raw_history
        except (json.JSONDecodeError, TypeError):
            history = []

        return YouTubeChannel(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            channel_name=row.get("channel_name"),
            custom_message=row["custom_message"],
            live_custom_message=row.get("live_custom_message"),
            mention_type=row["mention_type"],
            live_mention_type=row.get("live_mention_type"),
            mention_role_ids=role_ids,
            live_mention_role_ids=live_role_ids,
            last_announced_video_id=row.get("last_announced_video_id"),
            added_at=row["added_at"],
            announced_video_history=[str(v) for v in history],
            uploads_playlist_id=row.get("uploads_playlist_id"),
        )