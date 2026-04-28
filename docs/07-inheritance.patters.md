# 🧬 Patrones y Herencia

## Patrones Aplicados en Nami

---

## 1️⃣ Repository Pattern

**Problema:** Desacoplar la lógica de negocio del acceso a datos.

**Solución:** Una interfaz por entidad, múltiples implementaciones posibles.

```python
# Interface (contrato)
class IStreamerRepository(ABC):
    @abstractmethod
    async def add(self, streamer: Streamer) -> Streamer: ...

# Implementación MariaDB
class MariaDBStreamerRepository(IStreamerRepository):
    async def add(self, streamer: Streamer) -> Streamer:
        # SQL aquí

# Implementación en memoria (para tests)
class InMemoryStreamerRepository(IStreamerRepository):
    def __init__(self):
        self._data = []

    async def add(self, streamer: Streamer) -> Streamer:
        self._data.append(streamer)
        return streamer
```

---

## 2️⃣ Dependency Injection

**Problema:** Evitar acoplamiento directo entre clases.

**Solución:** Pasar dependencias por el constructor (inyección).

```python
# ❌ MAL: dependencia directa
class AddStreamerUseCase:
    def __init__(self):
        self.repo = MariaDBStreamerRepository(...)   # acoplado

# ✅ BIEN: inyección
class AddStreamerUseCase:
    def __init__(self, repo: IStreamerRepository):
        self.repo = repo   # desacoplado
```

---

## 3️⃣ Command Pattern

**Problema:** Pasar muchos parámetros a un método.

**Solución:** Encapsular los parámetros en un objeto.

```python
# ❌ MAL
await use_case.execute(guild_id, username, message, mention_type, role_ids)

# ✅ BIEN
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

**Problema:** Centralizar la creación de objetos complejos.

**Solución:** Una clase que "arma" todo al iniciar.

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

## 🧬 Cuándo Usar Herencia

### ✅ Casos Válidos

**1. Implementar una interfaz**

```python
class MariaDBStreamerRepository(IStreamerRepository):
    # Implementa todos los métodos abstractos
```

**2. Extender un Cog de discord.py**

```python
class MonitorCog(commands.Cog):
    # ...
```

**3. Jerarquía de excepciones**

```python
class DomainError(Exception): ...
class StreamerNotFoundError(DomainError): ...
class StreamerAlreadyExistsError(DomainError): ...
```

---

### ❌ Casos a Evitar

**1. Herencia para reutilizar código**

```python
# ❌ MAL
class BaseUseCase:
    def log_something(self):
        print("...")

class AddStreamerUseCase(BaseUseCase):
    # heredó log_something "gratis"
```

**Mejor:** **Composición**

```python
# ✅ BIEN
class AddStreamerUseCase:
    def __init__(self, logger: ILogger):
        self._logger = logger   # composición
```

**Regla de oro:** *"Prefiere composición sobre herencia"*

---

## 🎨 Herencia en la Práctica

### Crear una nueva excepción

```python
# src/domain/exceptions/domain_exceptions.py

class DomainError(Exception):
    """Base para todos los errores de negocio."""
    pass

# Tus excepciones heredan de DomainError
class MiNuevoError(DomainError):
    """Descripción."""
    pass
```

### Crear un nuevo Cog

```python
from discord.ext import commands

class MiNuevoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mi_comando")
    async def mi_comando(self, interaction):
        await interaction.response.send_message("Hola!")
```

### Crear un nuevo Repositorio

```python
from src.application.interfaces.mi_repo import IMiRepo

class MariaDBMiRepo(IMiRepo):
    def __init__(self, pool):
        self._pool = pool

    # Implementa TODOS los métodos abstractos
    async def metodo1(self): ...
    async def metodo2(self): ...
```

---

## 📋 Resumen
### 🛠️ Arquitectura y Patrones de Diseño

| Patrón | Dónde se usa | Para qué |
| :--- | :--- | :--- |
| **Repository** | `infrastructure/persistence/` | Acceso a datos y persistencia. |
| **Dependency Injection** | Toda la aplicación | Desacoplar las clases y facilitar las pruebas. |
| **Command** | `use_cases/` | Encapsular la información para pasar parámetros. |
| **Factory** | `composition_root/` | Centralizar la lógica de ensamblado de objetos. |
| **Herencia** | Cogs, excepciones, repositorios | Implementar contratos y extender funcionalidades base. |
| **Composición** | Use cases | Reutilizar funcionalidad de forma flexible sin jerarquías rígidas. |
