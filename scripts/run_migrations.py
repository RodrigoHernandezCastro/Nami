"""Script para ejecutar migraciones SQL contra MariaDB."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiomysql
from src.infrastructure.config.settings import Settings


MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent
    / "src" / "infrastructure" / "persistence" / "migrations"
)


async def run_migrations() -> None:
    settings = Settings()
    print(f"🔌 Conectando a: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    conn = await aiomysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not sql_files:
            print("  No se encontraron archivos SQL.")
            return

        async with conn.cursor() as cur:
            for sql_file in sql_files:
                print(f"▶️  Ejecutando: {sql_file.name}")
                sql = sql_file.read_text(encoding="utf-8")

                # MariaDB requiere ejecutar sentencias una por una
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                for stmt in statements:
                    await cur.execute(stmt)

                print(f" {sql_file.name} aplicado correctamente")

        print("\n🎉 Todas las migraciones se aplicaron con éxito.")

    except Exception as e:
        print(f" Error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())