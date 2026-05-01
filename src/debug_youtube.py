# debug_youtube.py — VERSIÓN CORREGIDA
import asyncio
import sys
sys.path.insert(0, ".")

from src.infrastructure.config.settings import Settings
from src.composition_root.container import Container

async def debug():
    settings = Settings()
    container = Container(settings)
    await container.startup()

    print("🔍 === DEBUG YOUTUBE ===")
    
    # 1. Ver todos los canales
    channels = await container.youtube_repo.find_by_guild(1071924718556430529)  # CAMBIA POR TU GUILD_ID
    print(f"Canales encontrados: {len(channels)}")
    
    if not channels:
        print("NO HAY CANALES — Añade con /añadir-youtube")
        await container.shutdown()
        return

    for i, c in enumerate(channels):
        print(f"  {i+1}. {c.channel_id} | Last: {c.last_announced_video_id}")

    # 2. Test update en PRIMER canal
    first_channel = channels[0]
    success = await container.youtube_repo.update_last_video(
        first_channel.id, "TEST123"
    )
    print(f"Update {first_channel.channel_id}: {'OK' if success else 'FAILED'}")

    # 3. Verificar se guardó
    updated = await container.youtube_repo.find_by_guild(1071924718556430529)
    print(f"🔄 Verificación: {updated[0].last_announced_video_id}")

    await container.shutdown()

if __name__ == "__main__":
    asyncio.run(debug())