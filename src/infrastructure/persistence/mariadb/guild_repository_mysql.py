# src/infrastructure/persistence/mariadb/guild_repository_mysql.py
import aiomysql
from typing import Optional
from src.domain.entities.guild_config import GuildConfig
from src.application.interfaces.guild_repository import IGuildRepository


class MariaDBGuildRepository(IGuildRepository):
    """Adaptador concreto para MariaDB/MySQL."""

    def __init__(self, pool: aiomysql.Pool) -> None:
        self._pool = pool

    async def get_by_id(self, guild_id: int) -> Optional[GuildConfig]:
        query = """
            SELECT guild_id, announcement_channel_id, youtube_channel_id,
                   streamer_limit, default_mention_type, language
            FROM guild_configs
            WHERE guild_id = %s;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                row = await cur.fetchone()
                if not row:
                    return None
                return self._row_to_entity(row)

    async def create_or_update(self, config: GuildConfig) -> GuildConfig:
        query = """
            INSERT INTO guild_configs
                (guild_id, announcement_channel_id, youtube_channel_id,
                 streamer_limit, default_mention_type, language)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                announcement_channel_id = VALUES(announcement_channel_id),
                youtube_channel_id      = VALUES(youtube_channel_id),
                streamer_limit          = VALUES(streamer_limit),
                default_mention_type    = VALUES(default_mention_type),
                language                = VALUES(language);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    (
                        config.guild_id,
                        config.announcement_channel_id,
                        config.youtube_channel_id,
                        config.streamer_limit,
                        config.default_mention_type,
                        config.language,
                    ),
                )
        return config

    async def set_announcement_channel(
        self, guild_id: int, channel_id: int
    ) -> None:
        query = """
            INSERT INTO guild_configs (guild_id, announcement_channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                announcement_channel_id = VALUES(announcement_channel_id);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (guild_id, channel_id))

    async def delete(self, guild_id: int) -> bool:
        query = "DELETE FROM guild_configs WHERE guild_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (guild_id,))
                return cur.rowcount > 0

    @staticmethod
    def _row_to_entity(row: dict) -> GuildConfig:
        return GuildConfig(
            guild_id=row["guild_id"],
            announcement_channel_id=row.get("announcement_channel_id"),
            youtube_channel_id=row.get("youtube_channel_id"),
            streamer_limit=row["streamer_limit"],
            default_mention_type=row["default_mention_type"],
            language=row["language"],
        )