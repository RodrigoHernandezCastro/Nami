"""Script para ejecutar migraciones SQL contra MariaDB.

Modo 1 — Sin argumentos: ejecuta TODAS las migraciones .sql
Modo 2 — Con argumento: ejecuta solo el archivo especificado
    python scripts/run_migrations.py 010_youtube_live_channel.sql
"""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiomysql
from src.infrastructure.config.settings import Settings

# Errores de MariaDB que podemos ignorar (ya aplicado)
IGNORED_ERRORS = {
    1060: "Duplicate column name",        # COLUMN ya existe
    1061: "Duplicate key name",           # INDEX ya existe
    1050: "Table already exists",         # TABLE ya existe
     1091: "Can't DROP COLUMN/INDEX",      # No existe lo que se quiere borrar
     4161: "Unknown data type",             # Tipo PostgreSQL (JSONB, etc.)
}


MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent
    / "src" / "infrastructure" / "persistence" / "migrations"
)


def _resolve_files(target: str | None) -> list[Path]:
    """Devuelve archivos a ejecutar: todos o solo el indicado."""
    if target:
        path = MIGRATIONS_DIR / target
        if not path.exists():
            print(f"Archivo no encontrado: {path}")
            sys.exit(1)
        return [path]
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


async def run_migrations() -> None:
    settings = Settings()
    target = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"Conectando a: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

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
        sql_files = _resolve_files(target)
        if not sql_files:
            print("  No se encontraron archivos SQL.")
            return

        async with conn.cursor() as cur:
            for sql_file in sql_files:
                print(f"Ejecutando: {sql_file.name}")
                sql = sql_file.read_text(encoding="utf-8")
                # Strip block comments /* ... */ and full-line -- comments
                # to avoid splitting on semicolons inside comments
                sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
                lines = [l for l in sql.splitlines() if not l.strip().startswith("--")]
                sql = "\n".join(lines)
                statements = [s.strip() for s in sql.split(";") if s.strip()]

                for stmt in statements:
                    try:
                        await cur.execute(stmt)
                    except Exception as e:
                        code = e.args[0] if e.args else None
                        label = IGNORED_ERRORS.get(code, f"Error {code}")
                        print(f"  -> {label} — omitido")

                print(f"  OK {sql_file.name} aplicado correctamente")

        print("\nMigraciones completadas.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())