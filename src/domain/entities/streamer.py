from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Streamer:
    """
    Representa un streamer de Twitch vinculado a un servidor Discord.
    mention_type controla a quién se menciona al detectar stream en vivo:
    'ninguno' | 'everyone' | 'here' | 'rol'.
    """
    guild_id: int
    username: str
    custom_message: str = "¡Ya está en vivo!"
    mention_type: str = "ninguno"  # ninguno | everyone | here | rol
    mention_role_ids: Optional[List[int]] = None
    is_online: bool = False
    id: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)

    def mark_online(self) -> None:
        """
        Marca el streamer como en vivo. Llamar tras confirmar
        la transición offline → online con Twitch y persistirla en BD.
        """
        self.is_online = True

    def mark_offline(self) -> None:
        """
        Marca el streamer como offline. Llamar tras confirmar
        la transición online → offline con Twitch y persistirla en BD.
        """
        self.is_online = False