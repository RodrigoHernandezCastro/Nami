
---

## **📄 `docs/04-adding-commands.md`**

````markdown
# ➕ Cómo Añadir un Comando Nuevo

Esta guía te lleva paso a paso para añadir un comando `/ping` que responde con la latencia del bot. Después lo extrapolas a cualquier comando.

---

## 🎯 Caso 1: Comando Simple (sin BD ni APIs)

### Paso 1: Añadir el comando en un Cog

Abre `src/presentation/discord_bot/cogs/monitor_cog.py` y añade el método:

```python
@app_commands.command(name="ping", description="Muestra la latencia del bot")
async def ping(self, interaction: discord.Interaction) -> None:
    latency_ms = round(self.bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latencia: **{latency_ms}ms**",
        ephemeral=True,
    )
```

### Paso 2: Reiniciar el bot

```bash
python main.py
```

El comando `/ping` aparecerá automáticamente (hay sync automático al iniciar).

---

## 🎯 Caso 2: Comando con Lógica de Negocio

Supongamos que queremos `/stats` que muestre cuántos streamers tiene el servidor.

### Paso 1: Crear el Caso de Uso

**Archivo:** `src/application/use_cases/get_guild_stats.py`

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

### Paso 2: Registrar en el Container

**Archivo:** `src/composition_root/container.py`

```python
from src.application.use_cases.get_guild_stats import GetGuildStatsUseCase

# Dentro de startup(), en la sección de Use Cases:
self.get_stats_uc = GetGuildStatsUseCase(
    streamer_repo=self.streamer_repo,
)
```

### Paso 3: Inyectar en el Cog

**Archivo:** `src/presentation/discord_bot/bot.py`

```python
await self.add_cog(
    MonitorCog(
        bot=self,
        add_streamer_uc=self.container.add_streamer_uc,
        remove_streamer_uc=self.container.remove_streamer_uc,
        list_streamers_uc=self.container.list_streamers_uc,
        configure_channel_uc=self.container.configure_channel_uc,
        get_stats_uc=self.container.get_stats_uc,   # ← NUEVO
    )
)
```

### Paso 4: Modificar el Cog

**Archivo:** `src/presentation/discord_bot/cogs/monitor_cog.py`

```python
from src.application.use_cases.get_guild_stats import (
    GetGuildStatsUseCase, GuildStatsQuery,
)

class MonitorCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        # ... otros use cases ...
        get_stats_uc: GetGuildStatsUseCase,   # ← NUEVO
    ):
        # ...
        self._stats_uc = get_stats_uc

    @app_commands.command(name="stats", description="Estadísticas del servidor")
    async def stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        result = await self._stats_uc.execute(
            GuildStatsQuery(guild_id=interaction.guild_id)
        )

        embed = discord.Embed(title="📊 Estadísticas", color=discord.Color.purple())
        embed.add_field(name="Total", value=str(result.total_streamers))
        embed.add_field(name="🔴 En vivo", value=str(result.online_count))
        embed.add_field(name="⚫ Offline", value=str(result.offline_count))

        await interaction.followup.send(embed=embed, ephemeral=True)
```

### Paso 5: Probar

```bash
python main.py
```

En Discord: `/stats`

---

## 🎯 Caso 3: Comando con Nueva Tabla en BD

Supongamos que queremos un sistema de **blacklist** de streamers prohibidos.

### Paso 1: Crear migración SQL

**Archivo:** `src/infrastructure/persistence/migrations/002_blacklist.sql`

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

### Paso 2: Crear entidad

**Archivo:** `src/domain/entities/blacklisted_streamer.py`

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

### Paso 3: Crear interface

**Archivo:** `src/application/interfaces/blacklist_repository.py`

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

### Paso 4: Crear implementación

**Archivo:** `src/infrastructure/persistence/mariadb/blacklist_repository_mysql.py`

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

### Paso 5: Crear caso de uso y comando

Sigue el patrón del Caso 2.

---

## ✅ Checklist al Añadir un Comando

- [ ] ¿Usa lógica de negocio? → Crea un **UseCase**
- [ ] ¿Necesita persistencia? → Crea/amplía un **Repositorio**
- [ ] ¿Necesita nueva tabla? → Crea **migración SQL**
- [ ] Registra el UseCase en el **Container**
- [ ] Inyecta el UseCase en el **Cog** (vía `bot.py`)
- [ ] Añade el comando en el **Cog**
- [ ] Prueba con `/comando` en Discord