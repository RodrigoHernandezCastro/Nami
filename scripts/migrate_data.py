import sys
import sqlite3
import asyncio
import asyncpg
from pathlib import Path

# Asegurar que encuentre la carpeta src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.infrastructure.config.settings import Settings
async def migrate():
    settings = Settings()
    
    # 1. Conectar a ambos
    sqlite_conn = sqlite3.connect('datos_bot.db')
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = await asyncpg.connect(settings.DATABASE_URL)

    print("Iniciando transferencia de datos...")

    try:
        # 2. Migrar Guilds (Configuraciones)
        cursor = sqlite_conn.execute("SELECT * FROM guilds_config")
        guilds = cursor.fetchall()
        
        for g in guilds:
            await pg_conn.execute("""
                INSERT INTO guild_configs (guild_id, announcement_channel_id, streamer_limit)
                VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO NOTHING
            """, 
            g['guild_id'], 
            g['canal_anuncios'], # Antes era announcement_channel_id
            g['limite_streamers'] # Antes era streamer_limit
            )
        
        print(f"{len(guilds)} servidores migrados.")

        # 3. Migrar Streamers
        cursor = sqlite_conn.execute("SELECT * FROM streamers")
        streamers = cursor.fetchall()

        for s in streamers:
            await pg_conn.execute("""
                INSERT INTO streamers (guild_id, username, is_online, custom_message, mention_type)
                VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING
            """, 
            s['guild_id'], 
            s['nombre_streamer'], # Antes era username
            bool(s['esta_online']), # Antes era is_online
            s['mensaje_custom'],
            s['tipo_mencion']
            )
            
        print(f"{len(streamers)} streamers migrados.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())