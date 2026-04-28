
---

## **📄 `docs/01-architecture.md`**

````markdown
# 🏛️ Arquitectura del Proyecto

## Clean Architecture Aplicada

Nami sigue los principios de **Clean Architecture** propuestos por Robert C. Martin (*Uncle Bob*). La idea central es que **la lógica de negocio no debe depender de detalles técnicos** como frameworks, bases de datos o librerías externas.

---

## 🎯 Las 4 Capas

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

## 📐 Regla de Oro: Dependencia hacia el Centro

**Las flechas de dependencia siempre apuntan hacia adentro.**

- ✅ `Infrastructure` conoce `Application` (para implementar interfaces)
- ✅ `Application` conoce `Domain` (usa entidades)
- ❌ `Domain` **NO** conoce a nadie (es el núcleo)
- ❌ `Application` **NO** conoce `Infrastructure`

---

## 🟣 Capa Domain (Núcleo)

**Ubicación:** `src/domain/`

Contiene el corazón del negocio. **Sin dependencias externas.**

### Componentes

- **Entidades** (`entities/`): Objetos con identidad (`Streamer`, `GuildConfig`)
- **Value Objects** (`value_objects/`): Objetos inmutables sin identidad (`TwitchUsername`)
- **Excepciones** (`exceptions/`): Errores del dominio (`StreamerAlreadyExistsError`)

### Ejemplo

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

**⚠️ Regla:** Aquí NO hay `import discord`, NO hay `import aiomysql`.

---

## 🟡 Capa Application (Lógica de Negocio)

**Ubicación:** `src/application/`

Contiene los **casos de uso** (reglas de negocio) y define las **interfaces** que la infraestructura debe implementar.

### Componentes

- **Use Cases** (`use_cases/`): Un archivo = un caso de uso (`AddStreamerUseCase`)
- **Interfaces** (`interfaces/`): Contratos abstractos (`IStreamerRepository`)
- **DTOs** (`dtos/`): Objetos de transferencia de datos

### Ejemplo

```python
# src/application/use_cases/add_streamer.py
class AddStreamerUseCase:
    def __init__(
        self,
        streamer_repo: IStreamerRepository,   # ← interfaz, no implementación
        twitch_service: ITwitchService,
        logger: ILogger,
    ):
        self._streamer_repo = streamer_repo
        # ...

    async def execute(self, command: AddStreamerCommand) -> Streamer:
        # Reglas de negocio puras
        if not await self._twitch.user_exists(command.username):
            raise StreamerNotOnTwitchError(...)
        # ...
```

**⚠️ Regla:** Aquí NO hay SQL, NO hay referencias a Discord.

---

## 🔵 Capa Infrastructure (Detalles Técnicos)

**Ubicación:** `src/infrastructure/`

Implementa las interfaces definidas en `Application`. Aquí vive todo lo "sucio": SQL, HTTP, Logging.

### Componentes

- **Persistence** (`persistence/mariadb/`): Implementaciones de repositorios
- **External APIs** (`external_apis/`): Clientes HTTP (Twitch)
- **Logging** (`logging/`): Implementación concreta de logs
- **Config** (`config/`): Carga de variables de entorno

### Ejemplo

```python
# src/infrastructure/persistence/mariadb/streamer_repository_mysql.py
class MariaDBStreamerRepository(IStreamerRepository):   # ← implementa interface
    def __init__(self, pool: aiomysql.Pool):
        self._pool = pool

    async def add(self, streamer: Streamer) -> Streamer:
        # SQL aquí
        query = "INSERT INTO streamers ..."
        # ...
```

---

## 🟢 Capa Presentation (Interfaz de Usuario)

**Ubicación:** `src/presentation/`

Traduce interacciones del usuario (comandos Discord) en llamadas a casos de uso.

### Componentes

- **Cogs** (`discord_bot/cogs/`): Controladores de comandos
- **Tasks** (`discord_bot/tasks/`): Jobs en segundo plano
- **Views** (`discord_bot/views/`): Constructores de embeds
- **Error Handler** (`error_handler.py`): Manejo global de errores

### Ejemplo

```python
# src/presentation/discord_bot/cogs/monitor_cog.py
@app_commands.command(name="añadir")
async def add_streamer(self, interaction, usuario: str):
    # Traduce Discord → Command
    cmd = AddStreamerCommand(guild_id=interaction.guild_id, username=usuario)
    # Ejecuta caso de uso
    streamer = await self._add_uc.execute(cmd)
    # Responde al usuario
    await interaction.followup.send(f"✅ Añadido: {streamer.username}")
```

---

## 🔌 Inyección de Dependencias

El **Composition Root** (`src/composition_root/container.py`) es el único lugar donde se "cablean" las dependencias concretas.

```python
# Aquí decidimos qué implementaciones usar
self.streamer_repo = MariaDBStreamerRepository(pool)
self.add_streamer_uc = AddStreamerUseCase(
    streamer_repo=self.streamer_repo,   # ← inyección
    # ...
)
```

**Ventaja:** Si mañana cambias MariaDB por PostgreSQL, **solo modificas el Container**.

---

## ✅ Beneficios de esta Arquitectura
