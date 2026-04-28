# 🎯 Casos de Uso

## ¿Qué es un Caso de Uso?

Un **caso de uso** representa **una acción del sistema**: "Añadir un streamer", "Configurar canal", "Verificar streams en vivo".

Es una **clase con un único método público**: `execute()`.

---

## 🏗️ Estructura Estándar

```python
from dataclasses import dataclass
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.logger import ILogger


# 1) Input: qué necesita el caso de uso
@dataclass
class MyUseCaseCommand:
    guild_id: int
    some_param: str


# 2) Output (opcional): qué devuelve
@dataclass
class MyUseCaseResult:
    success: bool
    data: str


# 3) El caso de uso
class MyUseCase:
    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._logger = logger

    async def execute(self, command: MyUseCaseCommand) -> MyUseCaseResult:
        # 1. Validaciones de dominio
        # 2. Reglas de negocio
        # 3. Persistencia
        # 4. Logging
        # 5. Return
        ...
```

---

## 📏 Reglas de Oro

### ✅ SÍ debe hacer

- Recibir dependencias **solo por interfaces** (`IStreamerRepository`, no `MariaDBStreamerRepository`)
- Lanzar excepciones del dominio (`StreamerNotFoundError`)
- Loggear eventos importantes
- Validar reglas de negocio

### ❌ NO debe hacer

- Importar `discord.py`
- Importar `aiomysql` o `aiohttp`
- Tener SQL
- Formatear embeds
- Saber que existe Discord

---

## 🔄 Command vs Query

### Commands (modifican estado)

```python
@dataclass
class AddStreamerCommand:
    guild_id: int
    username: str
```

### Queries (solo leen)

```python
@dataclass
class ListStreamersQuery:
    guild_id: int
```

Esta distinción viene del patrón **CQRS** (Command Query Responsibility Segregation).

---

## 💡 Ejemplo Completo Comentado

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
    Caso de uso: Añadir un streamer al monitoreo.

    Reglas de negocio:
    1. El canal de anuncios debe estar configurado.
    2. No se puede exceder el límite de streamers por servidor.
    3. El usuario debe existir en Twitch.
    4. El nombre de usuario debe ser válido (TwitchUsername).
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
        # ═══ 1. VALIDACIÓN DE DOMINIO ═══
        username = TwitchUsername(command.username)

        # ═══ 2. REGLAS DE NEGOCIO ═══
        guild_config = await self._guild_repo.get_by_id(command.guild_id)
        if not guild_config or not guild_config.announcement_channel_id:
            raise ChannelNotConfiguredError(
                "El canal de anuncios no está configurado."
            )

        current_count = await self._streamer_repo.count_by_guild(command.guild_id)
        if current_count >= guild_config.streamer_limit:
            raise StreamerLimitReachedError(
                f"Límite alcanzado: {guild_config.streamer_limit}"
            )

        # ═══ 3. VALIDACIÓN EXTERNA ═══
        if not await self._twitch.user_exists(username.value):
            raise StreamerNotOnTwitchError(
                f"'{username.value}' no existe en Twitch."
            )

        # ═══ 4. PERSISTENCIA ═══
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

## 🧪 Testeando un Caso de Uso

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

    guild_repo.get_by_id.return_value = None   # Sin config

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