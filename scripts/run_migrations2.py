# scripts/run_migrations.py
import asyncio
import sys
from pathlib import Path

# Añadir el path raíz para las importaciones
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.config.settings import Settings

async def run_migrations():
    settings = Settings()

    # Ruta estricta al archivo de migración 010
    migration_file = Path(__file__).resolve().parent.parent / "src" / "infrastructure" / "persistence" / "migrations" / "010_youtube_live_channel.sql"
    sql_content = migration_file.read_text(encoding="utf-8")

    if "postgresql" in settings.database_url.lower():
        print("Conectando a PostgreSQL...")
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
        try:
            await conn.execute(sql_content)
            print("Migración 010 aplicada exitosamente en PostgreSQL.")
        finally:
            await conn.close()
    else:
        print("Conectando a la instancia MariaDB del bot...")
        import aiomysql
        conn = await aiomysql.connect(
            host=settings.DB_HOST, port=settings.DB_PORT,
            user=settings.DB_USER, password=settings.DB_PASSWORD,
            db=settings.DB_NAME, charset="utf8mb4"
        )
        try:
            async with conn.cursor() as cur:
                # aiomysql requiere separar las sentencias múltiples
                for statement in sql_content.split(';'):
                    if statement.strip():
                        await cur.execute(statement)
            await conn.commit()
            print("Migración 010 aplicada exitosamente en MariaDB embebido.")
        finally:
            conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())
