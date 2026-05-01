# scripts/run_migrations.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrastructure.config.settings import Settings


async def run_migrations():
    settings = Settings()
    
    if "postgresql" in settings.database_url.lower():
        print("PostgreSQL detectado")
        import asyncpg
        conn = await asyncpg.connect(settings.database_url)
    else:
        print("MariaDB detectado")
        import aiomysql
        conn = await aiomysql.connect(
            host=settings.DB_HOST, port=settings.DB_PORT,
            user=settings.DB_USER, password=settings.DB_PASSWORD,
            db=settings.DB_NAME, charset="utf8mb4"
        )

    try:
        # Tu lógica de migraciones aquí
        print("Migraciones ejecutadas")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())