from dataclasses import dataclass
from typing import Callable, Awaitable, Dict, List, Type
import asyncio


@dataclass
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    pass


@dataclass
class StreamerWentLiveEvent(DomainEvent):
    streamer_id: int
    guild_id: int
    username: str
    stream_title: str
    game_name: str
    thumbnail_url: str


@dataclass
class StreamerAddedEvent(DomainEvent):
    streamer_id: int
    guild_id: int
    username: str


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """
    Bus de eventos asíncrono en memoria.
    Permite que múltiples consumidores reaccionen
    a un mismo evento sin acoplamiento.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        # Ejecutamos en paralelo; fallos aislados.
        await asyncio.gather(
            *(self._safe_handle(h, event) for h in handlers),
            return_exceptions=False,
        )

    @staticmethod
    async def _safe_handle(handler: EventHandler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception as e:
            # Aquí puedes inyectar el logger si lo prefieres
            print(f"[EventBus] Handler {handler.__name__} falló: {e}")