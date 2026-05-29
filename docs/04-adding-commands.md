
---

## **📄 `docs/04-adding-commands.md`**

# ➕ How to Add a New Command

This guide walks you step by step to add a `/ping` command that responds with the bot's latency. Then you can extrapolate to any command.

---

## 🎯 Case 1: Simple Command (no DB or APIs)

### Step 1: Add the command to a Cog

Open `src/presentation/discord_bot/cogs/monitor_cog.py` and add the method:

```python
@app_commands.command(name="ping", description="Shows the bot's latency")
async def ping(self, interaction: discord.Interaction) -> None:
    latency_ms = round(self.bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latency: **{latency_ms}ms**",
        ephemeral=True,
    )
```

### Step 2: Restart the bot

```bash
python main.py
```

The `/ping` command will appear automatically (auto-sync on startup).

---

## 🎯 Case 2: Command with Business Logic

Suppose we want `/stats` to show how many streamers the server has.

### Step 1: Create the Use Case

**File:** `src/application/use_cases/get_guild_stats.py`

```python
from dataclasses import dataclass
from src.application.interfaces.streamer_repository import IStreamerRepository


@dataclass
class GuildStatsQuery:
    guild_id: int


@dataclass
class GuildStatsResult:
    total_streamers: int
    online_count: int
    offline_count: int


class GetGuildStatsUseCase:
    def __init__(self, streamer_repo: IStreamerRepository) -> None:
        self._streamer_repo = streamer_repo

    async def execute(self, query: GuildStatsQuery) -> GuildStatsResult:
        streamers = await self._streamer_repo.find_by_guild(query.guild_id)
        online = sum(1 for s in streamers if s.is_online)
        return GuildStatsResult(
            total_streamers=len(streamers),
            online_count=online,
            offline_count=len(streamers) - online,
        )
```

### Step 2: Register in the Container

**File:** `src/composition_root/container.py`

```python
from src.application.use_cases.get_guild_stats import GetGuildStatsUseCase

# Inside startup(), in the Use Cases section:
self.get_stats_uc = GetGuildStatsUseCase(
    streamer_repo=self.streamer_repo,
)
```

### Step 3: Inject into the Cog

**File:** `src/presentation/discord_bot/bot.py`

```python
await self.add_cog(
    MonitorCog(
        bot=self,
        add_streamer_uc=self.container.add_streamer_uc,
        remove_streamer_uc=self.container.remove_streamer_uc,
        list_streamers_uc=self.container.list_streamers_uc,
        configure_channel_uc=self.container.configure_channel_uc,
        get_stats_uc=self.container.get_stats_uc,   # ← NEW
    )
)
```

### Step 4: Modify the Cog

**File:** `src/presentation/discord_bot/cogs/monitor_cog.py`

```python
from src.application.use_cases.get_guild_stats import (
    GetGuildStatsUseCase, GuildStatsQuery,
)

class MonitorCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        # ... other use cases ...
        get_stats_uc: GetGuildStatsUseCase,   # ← NEW
    ):
        # ...
        self._stats_uc = get_stats_uc

    @app_commands.command(name="stats", description="Server statistics")
    async def stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        result = await self._stats_uc.execute(
            GuildStatsQuery(guild_id=interaction.guild_id)
        )

        embed = discord.Embed(title="📊 Statistics", color=discord.Color.purple())
        embed.add_field(name="Total", value=str(result.total_streamers))
        embed.add_field(name="🔴 Live", value=str(result.online_count))
        embed.add_field(name="⚫ Offline", value=str(result.offline_count))

        await interaction.followup.send(embed=embed, ephemeral=True)
```

### Step 5: Test

```bash
python main.py
```

In Discord: `/stats`

---

## 🎯 Case 3: Command with a New DB Table

Suppose we want a **blacklist** system for banned streamers.

### Step 1: Create SQL migration

**File:** `src/infrastructure/persistence/migrations/002_blacklist.sql`

```sql
CREATE TABLE IF NOT EXISTS blacklisted_streamers (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    username    VARCHAR(50) NOT NULL,
    reason      TEXT,
    added_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (guild_id, username)
);
```

### Step 2: Create entity

**File:** `src/domain/entities/blacklisted_streamer.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class BlacklistedStreamer:
    guild_id: int
    username: str
    reason: Optional[str] = None
    id: Optional[int] = None
    added_at: datetime = field(default_factory=datetime.utcnow)
```

### Step 3: Create interface

**File:** `src/application/interfaces/blacklist_repository.py`

```python
from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.blacklisted_streamer import BlacklistedStreamer

class IBlacklistRepository(ABC):
    @abstractmethod
    async def add(self, entry: BlacklistedStreamer) -> BlacklistedStreamer: ...

    @abstractmethod
    async def find_by_guild(self, guild_id: int) -> List[BlacklistedStreamer]: ...

    @abstractmethod
    async def is_blacklisted(self, guild_id: int, username: str) -> bool: ...
```

### Step 4: Create implementation

**File:** `src/infrastructure/persistence/mariadb/blacklist_repository_mysql.py`

```python
import aiomysql
from typing import List
from src.domain.entities.blacklisted_streamer import BlacklistedStreamer
from src.application.interfaces.blacklist_repository import IBlacklistRepository


class MariaDBBlacklistRepository(IBlacklistRepository):
    def __init__(self, pool: aiomysql.Pool):
        self._pool = pool

    async def add(self, entry: BlacklistedStreamer) -> BlacklistedStreamer:
        query = """
            INSERT INTO blacklisted_streamers (guild_id, username, reason)
            VALUES (%s, %s, %s);
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (entry.guild_id, entry.username, entry.reason))
                entry.id = cur.lastrowid
                return entry

    async def find_by_guild(self, guild_id: int) -> List[BlacklistedStreamer]:
        query = "SELECT * FROM blacklisted_streamers WHERE guild_id = %s;"
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (guild_id,))
                rows = await cur.fetchall()
                return [
                    BlacklistedStreamer(
                        id=r["id"],
                        guild_id=r["guild_id"],
                        username=r["username"],
                        reason=r["reason"],
                        added_at=r["added_at"],
                    )
                    for r in rows
                ]

    async def is_blacklisted(self, guild_id: int, username: str) -> bool:
        query = """
            SELECT 1 FROM blacklisted_streamers
            WHERE guild_id = %s AND username = %s LIMIT 1;
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (guild_id, username.lower()))
                return await cur.fetchone() is not None
```

### Step 5: Create use case and command

Follow the pattern from Case 2.

---

## ✅ Checklist for Adding a Command

- [ ] Does it use business logic? → Create a **UseCase**
- [ ] Does it need persistence? → Create/extend a **Repository**
- [ ] Does it need a new table? → Create **SQL migration**
- [ ] Register the UseCase in the **Container**
- [ ] Inject the UseCase into the **Cog** (via `bot.py`)
- [ ] Add the command in the **Cog**
- [ ] Test with `/comando` in Discord
