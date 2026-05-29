# 🗃️ Repositories

## What is a Repository?

A **repository** is a class that encapsulates data access. Its job is to **translate between domain entities and database records**.

**Key rule:** Use cases NEVER talk directly to the database. They always do so through a repository.

---

## 🏛️ Pattern Structure

```
┌────────────────────────────┐
│     Use Case               │
│  (business logic)          │
└────────────┬───────────────┘
             │ uses
             ▼
┌────────────────────────────┐
│  IStreamerRepository       │  ← Interface (contract)
│  (abstract)                │
└────────────┬───────────────┘
             │ implements
             ▼
┌────────────────────────────┐
│  MariaDBStreamerRepository │  ← Concrete implementation
│  (SQL here)                │
└────────────────────────────┘
```

---

## 📐 Anatomy of a Repository

### 1. The Interface (contract)

**Location:** `src/application/interfaces/`

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

### 2. The Implementation

**Location:** `src/infrastructure/persistence/mariadb/`

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

## ✅ Best Practices

### 1. One repository per root entity

```
streamers        → StreamerRepository
guild_configs    → GuildRepository
blacklist        → BlacklistRepository
```

### 2. Expressive method names

## ✅ Naming Conventions

Use descriptive and consistent names across all repository methods:

| ❌ Bad | ✅ Good |
|---|---|
| `get(id)` | `find_by_id(id)` |
| `getAll()` | `find_all()` |
| `getByGuild()` | `find_by_guild()` |
| `save()` | `add()` / `update()` |

---

## 📐 General Best Practices

### 1. Always use the connection pool

```python
# ❌ BAD: new connection every time
conn = await aiomysql.connect(...)

# ✅ GOOD: shared pool
async with self._pool.acquire() as conn:
    ...
```

### 2. Convert between Entity ↔ DB Row

Always implement a static `_row_to_entity` method to decouple the data layer:

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

## 🛠️ Creating a New Repository

> **Example case:** Create `FavoritesRepository` to save favorite streamers.

### Step 1: SQL Migration

Create the file in **`src/infrastructure/persistence/migrations/003_favorites.sql`**:

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

### Step 2: Entity

Create **`src/domain/entities/favorite.py`**:

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

### Step 3: Interface

Create **`src/application/interfaces/favorite_repository.py`**:

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

### Step 4: Implementation

Create **`src/infrastructure/persistence/mariadb/favorite_repository_mysql.py`**:

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

### Step 5: Register in the Container

Edit **`src/composition_root/container.py`**:

```python
from src.infrastructure.persistence.mariadb.favorite_repository_mysql import (
    MariaDBFavoriteRepository,
)

# Inside startup():
self.favorite_repo = MariaDBFavoriteRepository(self._pool)
```

---

## 🔄 Transaction Handling

When you need to run multiple queries as an atomic block, use explicit `begin` / `commit` / `rollback`:

```python
async def transfer_streamers(self, from_guild: int, to_guild: int) -> None:
    async with self._pool.acquire() as conn:
        await conn.begin()   # ← start transaction
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
            await conn.commit()   # ← commit
        except Exception:
            await conn.rollback()   # ← rollback on failure
            raise
```

---

## 🧪 Testing a Repository

### Integration tests (real DB)

Ideally with an ephemeral Docker container:

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

### Unit tests for Use Cases (mock)

To isolate business logic without touching the DB:

```python
from unittest.mock import AsyncMock

streamer_repo = AsyncMock(spec=IStreamerRepository)
streamer_repo.find_by_guild.return_value = [Streamer(...)]
```
