import asyncpg
from typing import Optional
from src.domain.entities.guild_config import GuildConfig
from src.application.interfaces.guild_repository import IGuildRepository


class PostgresGuildRepository(IGuildRepository):
    """
    Adaptador concreto para PostgreSQL.
    Traduce entre la entidad GuildConfig y el esquema de BD.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_by_id(self, guild_id: int) -> Optional[GuildConfig]:
        query = """
            SELECT guild_id, announcement_channel_id, youtube_channel_id,
                   youtube_live_channel_id, streamer_limit,
                   default_mention_type, language
            FROM guild_configs
            WHERE guild_id = $1;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, guild_id)
            if not row:
                return None
            return self._row_to_entity(row)

    async def create_or_update(self, config: GuildConfig) -> GuildConfig:
        query = """
            INSERT INTO guild_configs
                (guild_id, announcement_channel_id, youtube_channel_id,
                 youtube_live_channel_id, streamer_limit,
                 default_mention_type, language)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (guild_id) DO UPDATE SET
                announcement_channel_id = EXCLUDED.announcement_channel_id,
                youtube_channel_id = EXCLUDED.youtube_channel_id,
                youtube_live_channel_id = EXCLUDED.youtube_live_channel_id,
                streamer_limit = EXCLUDED.streamer_limit,
                default_mention_type = EXCLUDED.default_mention_type,
                language = EXCLUDED.language
            RETURNING guild_id, announcement_channel_id, youtube_channel_id,
                      youtube_live_channel_id, streamer_limit,
                      default_mention_type, language;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                config.guild_id,
                config.announcement_channel_id,
                config.youtube_channel_id,
                config.youtube_live_channel_id,
                config.streamer_limit,
                config.default_mention_type,
                config.language,
            )
            return self._row_to_entity(row)

    async def set_announcement_channel(
        self, guild_id: int, channel_id: int
    ) -> None:
        query = """
            INSERT INTO guild_configs (guild_id, announcement_channel_id)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO UPDATE SET
                announcement_channel_id = EXCLUDED.announcement_channel_id;
        """
        async with self._pool.acquire() as conn:
            await conn.execute(query, guild_id, channel_id)

    async def delete(self, guild_id: int) -> bool:
        query = "DELETE FROM guild_configs WHERE guild_id = $1 RETURNING guild_id;"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, guild_id)
            return row is not None

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> GuildConfig:
        return GuildConfig(
            guild_id=row["guild_id"],
            announcement_channel_id=row["announcement_channel_id"],
            youtube_channel_id=row.get("youtube_channel_id"),
            youtube_live_channel_id=row.get("youtube_live_channel_id"),
            streamer_limit=row["streamer_limit"],
            default_mention_type=row["default_mention_type"],
            language=row["language"],
        )