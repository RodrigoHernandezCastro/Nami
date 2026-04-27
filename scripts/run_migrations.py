"""
Script para ejecutar las migraciones SQL contra PostgreSQL.
Uso: python scripts/run_migrations.py
"""
import asyncio
import sys
from pathlib import Path

# Permite importar desde src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from src.infrastructure.config.settings import Settings


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "src" / "infrastructure" / "persistence" / "migrations"


async def run_migrations() -> None:
    settings = Settings()
    print(f"Conectando a: {settings.DATABASE_URL.split('@')[-1]}")

    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        if not sql_files:
            print("No se encontraron archivos SQL de migración.")
            return

        for sql_file in sql_files:
            print(f"▶Ejecutando: {sql_file.name}")
            sql = sql_file.read_text(encoding="utf-8")
            await conn.execute(sql)
            print(f"{sql_file.name} aplicado correctamente")

        print("\nTodas las migraciones se aplicaron con éxito.")

    except Exception as e:
        print(f"Error ejecutando migraciones: {e}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())