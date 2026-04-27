from abc import ABC, abstractmethod
from typing import Dict, List, Set

class ITwitchService(ABC):
    @abstractmethod
    async def user_exists(self, username: str) -> bool: ...

    @abstractmethod
    async def get_live_streams_details(
        self, usernames: List[str]
    ) -> Dict[str, dict]: ...