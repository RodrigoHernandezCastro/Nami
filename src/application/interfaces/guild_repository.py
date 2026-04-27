from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.guild_config import GuildConfig


class IGuildRepository(ABC):
    @abstractmethod
    async def get_by_id(self, guild_id: int) -> Optional[GuildConfig]: ...

    @abstractmethod
    async def create_or_update(self, config: GuildConfig) -> GuildConfig: ...

    @abstractmethod
    async def set_announcement_channel(
        self, guild_id: int, channel_id: int
    ) -> None: ...

    @abstractmethod
    async def delete(self, guild_id: int) -> bool: ...