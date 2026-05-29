
---

## **📄 `docs/02-project-structure.md`**

# 📁 Project Structure

## Directory Tree

```
nami_bot/
│
├── docs/                              # 📚 Documentation
│
├── scripts/                           # 🔧 Utility scripts
│   └── run_migrations.py              # Applies SQL migrations
│
├── src/                               # 💻 Source code
│   │
│   ├── domain/                        # 🟣 CORE (no dependencies)
│   │   ├── entities/                  # Objects with identity
│   │   │   ├── streamer.py
│   │   │   └── guild_config.py
│   │   ├── value_objects/             # Immutable objects
│   │   │   └── twitch_username.py
│   │   └── exceptions/                # Business errors
│   │       └── domain_exceptions.py
│   │
│   ├── application/                   # 🟡 BUSINESS LOGIC
│   │   ├── use_cases/                 # One use case per file
│   │   │   ├── add_streamer.py
│   │   │   ├── remove_streamer.py
│   │   │   ├── list_streamers.py
│   │   │   ├── configure_channel.py
│   │   │   └── check_live_streams.py
│   │   ├── interfaces/                # Contracts (ports)
│   │   │   ├── streamer_repository.py
│   │   │   ├── guild_repository.py
│   │   │   ├── twitch_service.py
│   │   │   └── logger.py
│   │   └── dtos/                      # Data Transfer Objects
│   │
│   ├── infrastructure/                # 🔵 IMPLEMENTATIONS
│   │   ├── persistence/
│   │   │   ├── mariadb/               # MariaDB repositories
│   │   │   │   ├── streamer_repository_mysql.py
│   │   │   │   └── guild_repository_mysql.py
│   │   │   └── migrations/            # SQL migrations
│   │   │       └── 001_initial_schema.sql
│   │   ├── external_apis/
│   │   │   └── twitch_api_client.py
│   │   ├── logging/
│   │   │   └── structured_logger.py
│   │   └── config/
│   │       └── settings.py
│   │
│   ├── presentation/                  # 🟢 DISCORD INTERFACE
│   │   └── discord_bot/
│   │       ├── bot.py                 # Main bot class
│   │       ├── cogs/                  # Slash commands
│   │       │   └── monitor_cog.py
│   │       ├── tasks/                 # Background tasks
│   │       │   └── stream_checker.py
│   │       ├── views/                 # Embeds and UI components
│   │       │   └── stream_embed.py
│   │       └── error_handler.py       # Global error handling
│   │
│   └── composition_root/              # 🔴 DEPENDENCY INJECTION
│       └── container.py               # Wires everything together
│
├── tests/                             # 🧪 Tests
│   ├── unit/
│   └── integration/
│
├── .env                               # 🔐 Environment variables (DO NOT commit)
├── .env.example                       # Variables template
├── .gitignore
├── main.py                            # 🚀 Entry point
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Development dependencies
└── README.md
```

---

## 🎯 Key Rule: Where to Put Things

### I want to model a business concept?
→ `src/domain/entities/` or `src/domain/value_objects/`

### I want to add business logic?
→ `src/application/use_cases/`

### I want to add a Discord command?
→ `src/presentation/discord_bot/cogs/`

### I want to integrate a new external API?
→ `src/infrastructure/external_apis/`

### I want to change how data is stored?
→ `src/infrastructure/persistence/`

### I want to add a periodic task?
→ `src/presentation/discord_bot/tasks/`

---

## 📦 `__init__.py` Files

Every folder under `src/` must have an `__init__.py` (can be empty). This tells Python it is a package.
