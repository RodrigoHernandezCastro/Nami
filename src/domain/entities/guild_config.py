from dataclasses import dataclass
from typing import Optional
 
 
@dataclass
class GuildConfig:
    """
    Configuración por servidor Discord. Un registro por guild_id.
    announcement_channel_id y youtube_channel_id son None hasta que
    el administrador los configure con /configurar.
    """
    guild_id: int
    announcement_channel_id: Optional[int] = None
    youtube_channel_id: Optional[int] = None
    streamer_limit: int = 15
    default_mention_type: str = "ninguno"
    language: str = "es"
 