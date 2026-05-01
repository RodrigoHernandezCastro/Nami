from dataclasses import dataclass
from typing import Optional
 
 
@dataclass
class GuildConfig:
    guild_id: int
    announcement_channel_id: Optional[int] = None
    youtube_channel_id: Optional[int] = None
    streamer_limit: int = 15
    default_mention_type: str = "ninguno"
    language: str = "es"
 