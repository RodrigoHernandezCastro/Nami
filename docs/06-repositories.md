# 🗃️ Repositorios

## ¿Qué es un Repositorio?

Un **repositorio** es una clase que encapsula el acceso a datos. Su trabajo es **traducir entre entidades de dominio y registros de base de datos**.

**Regla clave:** Los casos de uso NUNCA hablan directamente con la BD. Siempre lo hacen a través de un repositorio.

---

## 🏛️ Estructura del Patrón

```
┌────────────────────────────┐
│     Use Case               │
│  (lógica de negocio)       │
└────────────┬───────────────┘
             │ usa
             ▼
┌────────────────────────────┐
│  IStreamerRepository       │  ← Interface (contrato)
│  (abstract)                │
└────────────┬───────────────┘
             │ implementa
             ▼
┌────────────────────────────┐
│  MariaDBStreamerRepository │  ← Implementación concreta
│  (SQL aquí)                │
└────────────────────────────┘
```

---

## 📐 Anatomía de un Repositorio

### 1. La Interface (contrato)

**Ubicación:** `src/application/interfaces/`

```python
# src/application/interfaces/streamer_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.streamer import Streamer


class IStreamerRepository(ABC):
    @abstractmethod
    async def add(self, streamer: Streamer) -> Streamer: ...

    @abstractmethod
    async def remove(self, guild_id: int, username: str) -> bool: ...

    @abstractmethod
    async def find_by_guild(self, guild_id: int) -> List[Streamer]: ...

    @abstractmethod
    async def count_by_guild(self, guild_id: int) -> int: ...

    @abstractmethod
    async def update_status(self, streamer_id: int, is_online: bool) -> None: ...
```

### 2. La Implementación

**Ubicación:** `src/infrastructure/persistence/mariadb/`

```python
# src/infrastructure/persistence/mariadb/streamer_repository_mysql.py
import aiomysql
import json
from typing import List
from src.domain.entities.streamer import Streamer
from src.application.interfaces.streamer_repository import IStreamerRepository


class MariaDBStreamerRepository(IStreamerRepository):
    def __init__(self, pool: aiomysql.Pool) -> None:
        self._pool = pool

    async def add(self, streamer: Streamer) -> Streamer:
        query = "INSERT INTO streamers (...) VALUES (%s, %s, ...);"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (...))
                streamer.id = cur.lastrowid
                return streamer
```

---

## ✅ Buenas Prácticas

### 1. Un repositorio por entidad raíz

```
streamers        → StreamerRepository
guild_configs    → GuildRepository
blacklist        → BlacklistRepository
```

### 2. Nombres de métodos expresivos
# Guía de Repositorios: Convenciones, Implementación y Testing

## ✅ Convenciones de Nomenclatura

Usa nombres descriptivos y consistentes en todos los métodos del repositorio:

| ❌ Mal | ✅ Bien |
|---|---|
| `get(id)` | `find_by_id(id)` |
| `getAll()` | `find_all()` |
| `getByGuild()` | `find_by_guild()` |
| `save()` | `add()` / `update()` |

---

## 📐 Buenas Prácticas Generales

### 1. Siempre usa el pool de conexiones

```python
# ❌ MAL: conexión nueva cada vez
conn = await aiomysql.connect(...)

# ✅ BIEN: pool compartido
async with self._pool.acquire() as conn:
    ...
```

### 2. Convierte entre Entity ↔ DB Row

Implementa siempre un método estático `_row_to_entity` para desacoplar la capa de datos:

```python
@staticmethod
def _row_to_entity(row: dict) -> Streamer:
    return Streamer(
        id=row["id"],
        guild_id=row["guild_id"],
        username=row["username"],
        # ...
    )
```

---

## 🛠️ Crear un Repositorio Nuevo

> **Caso de ejemplo:** crear `FavoritesRepository` para guardar streamers favoritos.

### Paso 1: Migración SQL

Crea el archivo en **`src/infrastructure/persistence/migrations/003_favorites.sql`**:

```sql
-- 003_favorites.sql

CREATE TABLE IF NOT EXISTS favorite_streamers (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    username    VARCHAR(50) NOT NULL,
    added_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, username)
);
```

---

### Paso 2: Entidad

Crea **`src/domain/entities/favorite.py`**:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Favorite:
    user_id: int
    username: str
    id: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)
```

---

### Paso 3: Interface

Crea **`src/application/interfaces/favorite_repository.py`**:

```python
from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.favorite import Favorite


class IFavoriteRepository(ABC):
    @abstractmethod
    async def add(self, favorite: Favorite) -> Favorite: ...

    @abstractmethod
    async def remove(self, user_id: int, username: str) -> bool: ...

    @abstractmethod
    async def find_by_user(self, user_id: int) -> List[Favorite]: ...
```

---

### Paso 4: Implementación

Crea **`src/infrastructure/persistence/mariadb/favorite_repository_mysql.py`**:

```python
import aiomysql
from typing import List
from src.domain.entities.favorite import Favorite
from src.application.interfaces.favorite_repository import IFavoriteRepository


class MariaDBFavoriteRepository(IFavoriteRepository):
    def __init__(self, pool: aiomysql.Pool) -> None:
        self._pool = pool

    async def add(self, favorite: Favorite) -> Favorite:
        query = """
            INSERT INTO favorite_streamers (user_id, username)
            VALUES (%s, %s);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (favorite.user_id, favorite.username))
                favorite.id = cur.lastrowid
                return favorite

    async def remove(self, user_id: int, username: str) -> bool:
        query = "DELETE FROM favorite_streamers WHERE user_id = %s AND username = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id, username.lower()))
                return cur.rowcount > 0

    async def find_by_user(self, user_id: int) -> List[Favorite]:
        query = "SELECT * FROM favorite_streamers WHERE user_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id,))
                rows = await cur.fetchall()
                return [self._row_to_entity(r) for r in rows]

    @staticmethod
    def _row_to_entity(row: dict) -> Favorite:
        return Favorite(
            id=row["id"],
            user_id=row["user_id"],
            username=row["username"],
            added_at=row["added_at"],
        )
```

---

### Paso 5: Registrar en el Container

Edita **`src/composition_root/container.py`**:

```python
from src.infrastructure.persistence.mariadb.favorite_repository_mysql import (
    MariaDBFavoriteRepository,
)

# Dentro de startup():
self.favorite_repo = MariaDBFavoriteRepository(self._pool)
```

---

## 🔄 Manejo de Transacciones

Cuando necesitas ejecutar varias queries como un bloque atómico, usa `begin` / `commit` / `rollback` explícitamente:

```python
async def transferir_streamers(self, from_guild: int, to_guild: int) -> None:
    async with self._pool.acquire() as conn:
        await conn.begin()   # ← inicia transacción
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE streamers SET guild_id = %s WHERE guild_id = %s;",
                    (to_guild, from_guild)
                )
                await cur.execute(
                    "DELETE FROM guild_configs WHERE guild_id = %s;",
                    (from_guild,)
                )
            await conn.commit()   # ← confirma
        except Exception:
            await conn.rollback()   # ← revierte si falla
            raise
```

---

## 🧪 Testear un Repositorio

### Tests de integración (BD real)

Idealmente con un contenedor Docker efímero:

```python
# tests/integration/test_streamer_repository.py
import pytest
import aiomysql
from src.infrastructure.persistence.mariadb.streamer_repository_mysql import (
    MariaDBStreamerRepository,
)
from src.domain.entities.streamer import Streamer


@pytest.mark.asyncio
async def test_add_and_find():
    pool = await aiomysql.create_pool(host="localhost", ...)
    repo = MariaDBStreamerRepository(pool)

    streamer = Streamer(guild_id=123, username="test_user")
    created = await repo.add(streamer)

    assert created.id is not None

    found = await repo.find_by_guild(123)
    assert len(found) == 1
    assert found[0].username == "test_user"

    pool.close()
    await pool.wait_closed()
```

### Tests unitarios de Use Cases (mock)

Para aislar la lógica de negocio sin tocar la BD:

```python
from unittest.mock import AsyncMock

streamer_repo = AsyncMock(spec=IStreamerRepository)
streamer_repo.find_by_guild.return_value = [Streamer(...)]
```