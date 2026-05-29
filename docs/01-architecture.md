
---

## **📄 `docs/01-architecture.md`**

# 🏛️ Project Architecture

## Clean Architecture Applied

Nami follows the **Clean Architecture** principles proposed by Robert C. Martin (*Uncle Bob*). The core idea is that **business logic should not depend on technical details** such as frameworks, databases, or external libraries.

---

## 🎯 The 4 Layers

```
┌──────────────────────────────────────────────────────┐
│                  🟢 PRESENTATION                     │
│          (Discord Cogs, Tasks, Embeds)               │
│                       ↓                              │
├──────────────────────────────────────────────────────┤
│                  🟡 APPLICATION                      │
│        (Use Cases, DTOs, Interfaces/Ports)           │
│                       ↓                              │
├──────────────────────────────────────────────────────┤
│                  🟣 DOMAIN                           │
│      (Entities, Value Objects, Exceptions)           │
│                       ↑                              │
├──────────────────────────────────────────────────────┤
│                  🔵 INFRASTRUCTURE                   │
│    (MariaDB, Twitch API, Logger, Config)             │
└──────────────────────────────────────────────────────┘
```

---

## 📐 Golden Rule: Dependencies Point Inward

**Dependency arrows always point inward.**

- ✅ `Infrastructure` knows `Application` (to implement interfaces)
- ✅ `Application` knows `Domain` (uses entities)
- ❌ `Domain` does **NOT** know anyone (it's the core)
- ❌ `Application` does **NOT** know `Infrastructure`

---

## 🟣 Domain Layer (Core)

**Location:** `src/domain/`

Contains the heart of the business. **No external dependencies.**

### Components

- **Entities** (`entities/`): Objects with identity (`Streamer`, `GuildConfig`)
- **Value Objects** (`value_objects/`): Immutable objects without identity (`TwitchUsername`)
- **Exceptions** (`exceptions/`): Domain errors (`StreamerAlreadyExistsError`)

### Example

```python
# src/domain/entities/streamer.py
@dataclass
class Streamer:
    guild_id: int
    username: str
    custom_message: str = "¡Ya está en vivo!"
    # ...

    def mark_online(self) -> None:
        self.is_online = True
```

**⚠️ Rule:** No `import discord`, no `import aiomysql` here.

---

## 🟡 Application Layer (Business Logic)

**Location:** `src/application/`

Contains **use cases** (business rules) and defines the **interfaces** that infrastructure must implement.

### Components

- **Use Cases** (`use_cases/`): One file = one use case (`AddStreamerUseCase`)
- **Interfaces** (`interfaces/`): Abstract contracts (`IStreamerRepository`)
- **DTOs** (`dtos/`): Data Transfer Objects

### Example

```python
# src/application/use_cases/add_streamer.py
class AddStreamerUseCase:
    def __init__(
        self,
        streamer_repo: IStreamerRepository,   # ← interface, not implementation
        twitch_service: ITwitchService,
        logger: ILogger,
    ):
        self._streamer_repo = streamer_repo
        # ...

    async def execute(self, command: AddStreamerCommand) -> Streamer:
        # Pure business rules
        if not await self._twitch.user_exists(command.username):
            raise StreamerNotOnTwitchError(...)
        # ...
```

**⚠️ Rule:** No SQL, no Discord references here.

---

## 🔵 Infrastructure Layer (Technical Details)

**Location:** `src/infrastructure/`

Implements the interfaces defined in `Application`. This is where all the "dirty" work lives: SQL, HTTP, Logging.

### Components

- **Persistence** (`persistence/mariadb/`): Repository implementations
- **External APIs** (`external_apis/`): HTTP clients (Twitch)
- **Logging** (`logging/`): Concrete logging implementation
- **Config** (`config/`): Environment variable loading

### Example

```python
# src/infrastructure/persistence/mariadb/streamer_repository_mysql.py
class MariaDBStreamerRepository(IStreamerRepository):   # ← implements interface
    def __init__(self, pool: aiomysql.Pool):
        self._pool = pool

    async def add(self, streamer: Streamer) -> Streamer:
        # SQL here
        query = "INSERT INTO streamers ..."
        # ...
```

---

## 🟢 Presentation Layer (User Interface)

**Location:** `src/presentation/`

Translates user interactions (Discord commands) into use case calls.

### Components

- **Cogs** (`discord_bot/cogs/`): Command controllers
- **Tasks** (`discord_bot/tasks/`): Background jobs
- **Views** (`discord_bot/views/`): Embed builders
- **Error Handler** (`error_handler.py`): Global error handling

### Example

```python
# src/presentation/discord_bot/cogs/monitor_cog.py
@app_commands.command(name="add", description="Add a Twitch streamer to monitor")
async def add_streamer(self, interaction, user: str):
    # Translate Discord → Command
    cmd = AddStreamerCommand(guild_id=interaction.guild_id, username=user)
    # Execute use case
    streamer = await self._add_uc.execute(cmd)
    # Respond to user
    await interaction.followup.send(f"✅ Added: {streamer.username}")
```

---

## 🔌 Dependency Injection

The **Composition Root** (`src/composition_root/container.py`) is the only place where concrete dependencies are wired together.

```python
# Here we decide which implementations to use
self.streamer_repo = MariaDBStreamerRepository(pool)
self.add_streamer_uc = AddStreamerUseCase(
    streamer_repo=self.streamer_repo,   # ← injection
    # ...
)
```

**Advantage:** If you switch MariaDB for PostgreSQL tomorrow, **you only modify the Container**.

---

## ✅ Benefits of this Architecture
