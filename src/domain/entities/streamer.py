from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Streamer:
    guild_id: int
    username: str
    custom_message: str = "¡Ya está en vivo!"
    mention_type: str = "ninguno"  # ninguno | everyone | here | rol
    mention_role_ids: Optional[List[int]] = None
    is_online: bool = False
    id: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)

    def mark_online(self) -> None:
        self.is_online = True

    def mark_offline(self) -> None:
        self.is_online = False