# 🎯 Use Cases

## What is a Use Case?

A **use case** represents **a system action**: "Add a streamer", "Configure channel", "Check live streams".

It is a **class with a single public method**: `execute()`.

---

## 🏗️ Standard Structure

```python
from dataclasses import dataclass
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.logger import ILogger


# 1) Input: what the use case needs
@dataclass
class MyUseCaseCommand:
    guild_id: int
    some_param: str


# 2) Output (optional): what it returns
@dataclass
class MyUseCaseResult:
    success: bool
    data: str


# 3) The use case
class MyUseCase:
    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._logger = logger

    async def execute(self, command: MyUseCaseCommand) -> MyUseCaseResult:
        # 1. Domain validations
        # 2. Business rules
        # 3. Persistence
        # 4. Logging
        # 5. Return
        ...
```

---

## 📏 Golden Rules

### ✅ MUST do

- Receive dependencies **only through interfaces** (`IStreamerRepository`, not `MariaDBStreamerRepository`)
- Throw domain exceptions (`StreamerNotFoundError`)
- Log important events
- Validate business rules

### ❌ MUST NOT do

- Import `discord.py`
- Import `aiomysql` or `aiohttp`
- Have SQL
- Format embeds
- Know that Discord exists

---

## 🔄 Command vs Query

### Commands (modify state)

```python
@dataclass
class AddStreamerCommand:
    guild_id: int
    username: str
```

### Queries (read only)

```python
@dataclass
class ListStreamersQuery:
    guild_id: int
```

This distinction comes from the **CQRS** pattern (Command Query Responsibility Segregation).

---

## 💡 Annotated Full Example

```python
# src/application/use_cases/add_streamer.py

from dataclasses import dataclass
from typing import Optional, List
from src.domain.entities.streamer import Streamer
from src.domain.value_objects.twitch_username import TwitchUsername
from src.domain.exceptions.domain_exceptions import (
    StreamerLimitReachedError,
    StreamerNotOnTwitchError,
    ChannelNotConfiguredError,
)
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.twitch_service import ITwitchService
from src.application.interfaces.logger import ILogger


@dataclass
class AddStreamerCommand:
    guild_id: int
    username: str
    custom_message: str
    mention_type: str
    mention_role_ids: Optional[List[int]] = None


class AddStreamerUseCase:
    """
    Use case: Add a streamer to monitoring.

    Business rules:
    1. The announcement channel must be configured.
    2. The streamer limit per server cannot be exceeded.
    3. The user must exist on Twitch.
    4. The username must be valid (TwitchUsername).
    """

    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        guild_repo: IGuildRepository,
        twitch_service: ITwitchService,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._guild_repo = guild_repo
        self._twitch = twitch_service
        self._logger = logger

    async def execute(self, command: AddStreamerCommand) -> Streamer:
        # ═══ 1. DOMAIN VALIDATION ═══
        username = TwitchUsername(command.username)

        # ═══ 2. BUSINESS RULES ═══
        guild_config = await self._guild_repo.get_by_id(command.guild_id)
        if not guild_config or not guild_config.announcement_channel_id:
            raise ChannelNotConfiguredError(
                "The announcement channel is not configured."
            )

        current_count = await self._streamer_repo.count_by_guild(command.guild_id)
        if current_count >= guild_config.streamer_limit:
            raise StreamerLimitReachedError(
                f"Limit reached: {guild_config.streamer_limit}"
            )

        # ═══ 3. EXTERNAL VALIDATION ═══
        if not await self._twitch.user_exists(username.value):
            raise StreamerNotOnTwitchError(
                f"'{username.value}' does not exist on Twitch."
            )

        # ═══ 4. PERSISTENCE ═══
        streamer = Streamer(
            guild_id=command.guild_id,
            username=username.value,
            custom_message=command.custom_message,
            mention_type=command.mention_type,
            mention_role_ids=command.mention_role_ids,
        )
        created = await self._streamer_repo.add(streamer)

        # ═══ 5. LOGGING ═══
        self._logger.info(
            "streamer_added",
            guild_id=command.guild_id,
            username=username.value,
            streamer_id=created.id,
        )

        return created
```

---

## 🧪 Testing a Use Case

```python
# tests/unit/application/test_add_streamer.py
import pytest
from unittest.mock import AsyncMock
from src.application.use_cases.add_streamer import (
    AddStreamerUseCase, AddStreamerCommand,
)
from src.domain.exceptions.domain_exceptions import ChannelNotConfiguredError


@pytest.mark.asyncio
async def test_add_streamer_fails_if_no_channel():
    # Arrange
    streamer_repo = AsyncMock()
    guild_repo = AsyncMock()
    twitch = AsyncMock()
    logger = AsyncMock()

    guild_repo.get_by_id.return_value = None   # No config

    use_case = AddStreamerUseCase(streamer_repo, guild_repo, twitch, logger)

    # Act & Assert
    with pytest.raises(ChannelNotConfiguredError):
        await use_case.execute(AddStreamerCommand(
            guild_id=123,
            username="shroud",
            custom_message="test",
            mention_type="ninguno",
        ))
```
