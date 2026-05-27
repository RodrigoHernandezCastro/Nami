# src/domain/entities/youtube_channel.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class YouTubeChannel:
    """
    Canal de YouTube vinculado a un servidor Discord.
    uploads_playlist_id se cachea tras la primera llamada a channels.list
    para reducir el coste de cuota de 2 → 1 unidad por ciclo de chequeo.
    announced_video_history mantiene los últimos 5 video_id anunciados
    como protección contra re-anuncios en caso de fallo de BD.
    """
    guild_id: int
    channel_id: str
    channel_name: Optional[str] = None
    custom_message: str = "¡Nuevo video en YouTube!"
    mention_type: str = "ninguno"
    mention_role_ids: Optional[List[int]] = None
    last_announced_video_id: Optional[str] = None
    id: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)
    announced_video_history: List[str] = field(default_factory=list)
    uploads_playlist_id: Optional[str] = None

    @property
    def display_name(self) -> str:
        """@nombre o channel_id."""
        return f"@{self.channel_name}" if self.channel_name else self.channel_id

    def add_announced_video(self, video_id: str) -> None:
        """Añade al historial (mantiene últimos 5)."""
        self.announced_video_history.insert(0, video_id)
        self.announced_video_history = self.announced_video_history[:5]

    def has_announced_video(self, video_id: str) -> bool:
        """Verifica si ya fue anunciado."""
        return video_id in self.announced_video_history
