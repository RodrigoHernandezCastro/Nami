#!/usr/bin/env python3
"""
scripts/pg_to_mariadb.py
========================
Migra TODOS los datos de PostgreSQL → MariaDB.

Uso:
    python scripts/pg_to_mariadb.py

Variables de entorno necesarias (.env):
    DATABASE_URL  → postgresql://user:pass@host:5432/dbname
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME  → MariaDB destino
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
import aiomysql
from src.infrastructure.config.settings import Settings


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def safe_json(value, fallback="[]") -> str:
    """Convierte cualquier valor JSON de PG a string JSON válido para MariaDB."""
    if value is None:
        return fallback
    if isinstance(value, str):
        try:
            json.loads(value)   # ya es JSON válido
            return value
        except json.JSONDecodeError:
            return fallback
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return fallback


def progress(current: int, total: int, label: str) -> None:
    pct = int(current / total * 100) if total else 100
    bar = "" * (pct // 5) + "" * (20 - pct // 5)
    print(f"\r  [{bar}] {pct:>3}%  {current}/{total} {label}", end="", flush=True)


# ──────────────────────────────────────────────────────────────────────────────
# Migración
# ──────────────────────────────────────────────────────────────────────────────

async def migrate_guild_configs(pg, my_conn) -> int:
    print("\nMigrando guild_configs...")
    rows = await pg.fetch("SELECT * FROM guild_configs ORDER BY guild_id;")
    if not rows:
        print("    Sin registros.")
        return 0

    query = """
        INSERT INTO guild_configs
            (guild_id, announcement_channel_id, streamer_limit,
             default_mention_type, language, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            announcement_channel_id = VALUES(announcement_channel_id),
            streamer_limit          = VALUES(streamer_limit),
            default_mention_type    = VALUES(default_mention_type),
            language                = VALUES(language),
            updated_at              = VALUES(updated_at);
    """
    async with my_conn.cursor() as cur:
        for i, r in enumerate(rows, 1):
            await cur.execute(query, (
                r["guild_id"],
                r["announcement_channel_id"],
                r["streamer_limit"],
                r["default_mention_type"],
                r["language"],
                r["created_at"],
                r["updated_at"],
            ))
            progress(i, len(rows), "guilds")
    print(f"\n  {len(rows)} guild_configs migradas.")
    return len(rows)


async def migrate_streamers(pg, my_conn) -> int:
    print("\n🎮 Migrando streamers...")
    rows = await pg.fetch("SELECT * FROM streamers ORDER BY id;")
    if not rows:
        print("    Sin registros.")
        return 0

    query = """
        INSERT INTO streamers
            (guild_id, username, custom_message, mention_type,
             mention_role_ids, is_online, added_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            custom_message   = VALUES(custom_message),
            mention_type     = VALUES(mention_type),
            mention_role_ids = VALUES(mention_role_ids),
            is_online        = VALUES(is_online);
    """
    async with my_conn.cursor() as cur:
        for i, r in enumerate(rows, 1):
            await cur.execute(query, (
                r["guild_id"],
                r["username"],
                r["custom_message"],
                r["mention_type"],
                safe_json(r["mention_role_ids"]),
                bool(r["is_online"]),
                r["added_at"],
            ))
            progress(i, len(rows), "streamers")
    print(f"\n  {len(rows)} streamers migrados.")
    return len(rows)


async def migrate_youtube_channels(pg, my_conn) -> int:
    print("\n📺 Migrando youtube_channels...")
    rows = await pg.fetch("SELECT * FROM youtube_channels ORDER BY id;")
    if not rows:
        print("    Sin registros.")
        return 0

    query = """
        INSERT INTO youtube_channels
            (guild_id, channel_id, channel_name, custom_message, mention_type,
             mention_role_ids, last_announced_video_id, announced_video_history, added_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            channel_name                = VALUES(channel_name),
            custom_message              = VALUES(custom_message),
            mention_type                = VALUES(mention_type),
            mention_role_ids            = VALUES(mention_role_ids),
            last_announced_video_id     = VALUES(last_announced_video_id),
            announced_video_history     = VALUES(announced_video_history);
    """
    async with my_conn.cursor() as cur:
        for i, r in enumerate(rows, 1):
            # announced_video_history puede no existir si la migración 007
            # no se aplicó en PG todavía → manejamos KeyError con get seguro
            raw_history = r.get("announced_video_history", None) if hasattr(r, "get") else None
            try:
                raw_history = dict(r).get("announced_video_history", None)
            except Exception:
                raw_history = None

            await cur.execute(query, (
                r["guild_id"],
                r["channel_id"],
                r["channel_name"],
                r["custom_message"],
                r["mention_type"],
                safe_json(r["mention_role_ids"]),
                r["last_announced_video_id"],
                safe_json(raw_history),
                r["added_at"],
            ))
            progress(i, len(rows), "canales YT")
    print(f"\n   {len(rows)} youtube_channels migrados.")
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Verificación post-migración
# ──────────────────────────────────────────────────────────────────────────────

async def verify(pg, my_conn) -> None:
    print("\nVerificando conteos...")

    tables = ["guild_configs", "streamers", "youtube_channels"]
    all_ok = True

    for table in tables:
        pg_count  = await pg.fetchval(f"SELECT COUNT(*) FROM {table};")
        async with my_conn.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) FROM {table};")
            row = await cur.fetchone()
            my_count = row[0] if row else 0

        status = "ok" if pg_count == my_count else "ERROR"
        if pg_count != my_count:
            all_ok = False
        print(f"  {status} {table}: PG={pg_count}  MariaDB={my_count}")

    if all_ok:
        print("\n🎉 Migración completada. Todos los conteos coinciden.")
    else:
        print("\n  Hay diferencias. Revisa los errores anteriores.")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    settings = Settings()

    print("=" * 60)
    print("  Migración PostgreSQL → MariaDB")
    print("=" * 60)

    # ── Conectar a PostgreSQL ──────────────────────────────────────
    if not settings.DATABASE_URL:
        print(" DATABASE_URL no configurada en .env")
        sys.exit(1)

    print(f"\n🔌 Conectando a PostgreSQL: {settings.DATABASE_URL[:40]}...")
    pg = await asyncpg.connect(settings.DATABASE_URL)

    # ── Conectar a MariaDB ────────────────────────────────────────
    if not all([settings.DB_HOST, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME]):
        print(" Variables MariaDB incompletas (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)")
        await pg.close()
        sys.exit(1)

    print(f"🔌 Conectando a MariaDB: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}...")
    my_conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        charset="utf8mb4",
        autocommit=True,
    )

    try:
        await migrate_guild_configs(pg, my_conn)
        await migrate_streamers(pg, my_conn)
        await migrate_youtube_channels(pg, my_conn)
        await verify(pg, my_conn)

    except Exception as e:
        print(f"\n Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await pg.close()
        my_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
