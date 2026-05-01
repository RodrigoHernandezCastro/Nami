
---

## **📄 `docs/02-project-structure.md`**

# 📁 Estructura del Proyecto

## Árbol de Directorios

```
nami_bot/
│
├── docs/                              # 📚 Documentación
│
├── scripts/                           # 🔧 Scripts de utilidad
│   └── run_migrations.py              # Aplica migraciones SQL
│
├── src/                               # 💻 Código fuente
│   │
│   ├── domain/                        # 🟣 NÚCLEO (sin dependencias)
│   │   ├── entities/                  # Objetos con identidad
│   │   │   ├── streamer.py
│   │   │   └── guild_config.py
│   │   ├── value_objects/             # Objetos inmutables
│   │   │   └── twitch_username.py
│   │   └── exceptions/                # Errores de negocio
│   │       └── domain_exceptions.py
│   │
│   ├── application/                   # 🟡 LÓGICA DE NEGOCIO
│   │   ├── use_cases/                 # Un caso de uso por archivo
│   │   │   ├── add_streamer.py
│   │   │   ├── remove_streamer.py
│   │   │   ├── list_streamers.py
│   │   │   ├── configure_channel.py
│   │   │   └── check_live_streams.py
│   │   ├── interfaces/                # Contratos (puertos)
│   │   │   ├── streamer_repository.py
│   │   │   ├── guild_repository.py
│   │   │   ├── twitch_service.py
│   │   │   └── logger.py
│   │   └── dtos/                      # Data Transfer Objects
│   │
│   ├── infrastructure/                # 🔵 IMPLEMENTACIONES
│   │   ├── persistence/
│   │   │   ├── mariadb/               # Repositorios MariaDB
│   │   │   │   ├── streamer_repository_mysql.py
│   │   │   │   └── guild_repository_mysql.py
│   │   │   └── migrations/            # SQL de migraciones
│   │   │       └── 001_initial_schema.sql
│   │   ├── external_apis/
│   │   │   └── twitch_api_client.py
│   │   ├── logging/
│   │   │   └── structured_logger.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── presentation/                  # 🟢 INTERFAZ DISCORD
│   │   └── discord_bot/
│   │       ├── bot.py                 # Clase principal del bot
│   │       ├── cogs/                  # Comandos slash
│   │       │   └── monitor_cog.py
│   │       ├── tasks/                 # Tareas en background
│   │       │   └── stream_checker.py
│   │       ├── views/                 # Embeds y componentes UI
│   │       │   └── stream_embed.py
│   │       └── error_handler.py       # Manejo global de errores
│   │
│   └── composition_root/              # 🔴 INYECCIÓN DE DEPENDENCIAS
│       └── container.py               # Ensambla todo
│
├── tests/                             # 🧪 Tests
│   ├── unit/
│   └── integration/
│
├── .env                               # 🔐 Variables de entorno (NO subir a git)
├── .env.example                       # Plantilla de variables
├── .gitignore
├── main.py                            # 🚀 Punto de entrada
├── requirements.txt                   # Dependencias de producción
├── requirements-dev.txt               # Dependencias de desarrollo
└── README.md
```

---

## 🎯 Regla Clave: Dónde Poner Cada Cosa

### ¿Quiero modelar un concepto del negocio?
→ `src/domain/entities/` o `src/domain/value_objects/`

### ¿Quiero añadir lógica de negocio?
→ `src/application/use_cases/`

### ¿Quiero añadir un comando de Discord?
→ `src/presentation/discord_bot/cogs/`

### ¿Quiero integrar una nueva API externa?
→ `src/infrastructure/external_apis/`

### ¿Quiero cambiar cómo se guardan los datos?
→ `src/infrastructure/persistence/`

### ¿Quiero añadir una tarea periódica?
→ `src/presentation/discord_bot/tasks/`

---

## 📦 Archivos `__init__.py`

Cada carpeta bajo `src/` debe tener un `__init__.py` (puede estar vacío). Esto le dice a Python que es un paquete.
