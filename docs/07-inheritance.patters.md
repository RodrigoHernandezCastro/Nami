# 🧬 Patterns and Inheritance

## Patterns Applied in Nami

---

## 1️⃣ Repository Pattern

**Problem:** Decouple business logic from data access.

**Solution:** One interface per entity, multiple possible implementations.

```python
# Interface (contract)
class IStreamerRepository(ABC):
    @abstractmethod
    async def add(self, streamer: Streamer) -> Streamer: ...

# MariaDB implementation
class MariaDBStreamerRepository(IStreamerRepository):
    async def add(self, streamer: Streamer) -> Streamer:
        # SQL here

# In-memory implementation (for tests)
class InMemoryStreamerRepository(IStreamerRepository):
    def __init__(self):
        self._data = []

    async def add(self, streamer: Streamer) -> Streamer:
        self._data.append(streamer)
        return streamer
```

---

## 2️⃣ Dependency Injection

**Problem:** Avoid direct coupling between classes.

**Solution:** Pass dependencies through the constructor (injection).

```python
# ❌ BAD: direct dependency
class AddStreamerUseCase:
    def __init__(self):
        self.repo = MariaDBStreamerRepository(...)   # coupled

# ✅ GOOD: injection
class AddStreamerUseCase:
    def __init__(self, repo: IStreamerRepository):
        self.repo = repo   # decoupled
```

---

## 3️⃣ Command Pattern

**Problem:** Passing many parameters to a method.

**Solution:** Encapsulate parameters in an object.

```python
# ❌ BAD
await use_case.execute(guild_id, username, message, mention_type, role_ids)

# ✅ GOOD
cmd = AddStreamerCommand(
    guild_id=123,
    username="shroud",
    custom_message="¡Live!",
    mention_type="rol",
    mention_role_ids=[456, 789],
)
await use_case.execute(cmd)
```

---

## 4️⃣ Factory Pattern (Composition Root)

**Problem:** Centralize creation of complex objects.

**Solution:** A class that "wires" everything at startup.

```python
class Container:
    async def startup(self):
        self._pool = await aiomysql.create_pool(...)
        self.streamer_repo = MariaDBStreamerRepository(self._pool)
        self.add_streamer_uc = AddStreamerUseCase(
            streamer_repo=self.streamer_repo,
            # ...
        )
```

---

## 🧬 When to Use Inheritance

### ✅ Valid Cases

**1. Implementing an interface**

```python
class MariaDBStreamerRepository(IStreamerRepository):
    # Implements all abstract methods
```

**2. Extending a discord.py Cog**

```python
class MonitorCog(commands.Cog):
    # ...
```

**3. Exception hierarchy**

```python
class DomainError(Exception): ...
class StreamerNotFoundError(DomainError): ...
class StreamerAlreadyExistsError(DomainError): ...
```

---

### ❌ Cases to Avoid

**1. Inheritance for code reuse**

```python
# ❌ BAD
class BaseUseCase:
    def log_something(self):
        print("...")

class AddStreamerUseCase(BaseUseCase):
    # inherited log_something "for free"
```

**Better:** **Composition**

```python
# ✅ GOOD
class AddStreamerUseCase:
    def __init__(self, logger: ILogger):
        self._logger = logger   # composition
```

**Golden rule:** *"Prefer composition over inheritance"*

---

## 🎨 Inheritance in Practice

### Creating a new exception

```python
# src/domain/exceptions/domain_exceptions.py

class DomainError(Exception):
    """Base for all business errors."""
    pass

# Your exceptions inherit from DomainError
class MyNewError(DomainError):
    """Description."""
    pass
```

### Creating a new Cog

```python
from discord.ext import commands

class MyNewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="my_command")
    async def my_command(self, interaction):
        await interaction.response.send_message("Hello!")
```

### Creating a new Repository

```python
from src.application.interfaces.my_repo import IMyRepo

class MariaDBMyRepo(IMyRepo):
    def __init__(self, pool):
        self._pool = pool

    # Implements ALL abstract methods
    async def method1(self): ...
    async def method2(self): ...
```

---

## 📋 Summary
### 🛠️ Architecture and Design Patterns

| Pattern | Where it's used | Purpose |
| :--- | :--- | :--- |
| **Repository** | `infrastructure/persistence/` | Data access and persistence. |
| **Dependency Injection** | Entire application | Decouple classes and facilitate testing. |
| **Command** | `use_cases/` | Encapsulate information for passing parameters. |
| **Factory** | `composition_root/` | Centralize object assembly logic. |
| **Inheritance** | Cogs, exceptions, repositories | Implement contracts and extend base functionality. |
| **Composition** | Use cases | Reuse functionality flexibly without rigid hierarchies. |
