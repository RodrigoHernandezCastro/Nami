"""
Script legacy: ejecuta UNA migración SQL específica.

Uso:
    python scripts/run_migrations2.py <archivo.sql>

Ejemplo:
    python scripts/run_migrations2.py 011_youtube_channel_live_settings.sql

Ahora es un wrapper alrededor de run_migrations.py para mantener compatibilidad.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Redirigir al script principal que ya maneja argumentos
from scripts.run_migrations import run_migrations

if __name__ == "__main__":
    # Si no se pasó argumento, asumir migration 010 (comportamiento original)
    if len(sys.argv) < 2:
        sys.argv.append("010_youtube_live_channel.sql")

    import asyncio
    asyncio.run(run_migrations())
