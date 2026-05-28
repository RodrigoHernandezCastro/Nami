from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.streamer import Streamer

class IStreamerRepository(ABC):
    @abstractmethod
    async def add(self, streamer: Streamer) -> Streamer: ...

    @abstractmethod
    async def update(self, streamer: Streamer) -> Streamer: ...

    @abstractmethod
    async def remove(self, guild_id: int, username: str) -> bool: ...

    @abstractmethod
    async def find_by_guild(self, guild_id: int) -> List[Streamer]: ...

    @abstractmethod
    async def find_all_with_channel(self) -> List[Streamer]: ...

    @abstractmethod
    async def count_by_guild(self, guild_id: int) -> int: ...

    @abstractmethod
    async def update_status(self, streamer_id: int, is_online: bool) -> None: ...