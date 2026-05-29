<div align="center">

# 🌊 Nami Bot
### *Your stream navigator on Discord*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.4-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![MariaDB](https://img.shields.io/badge/MariaDB-11-003545?style=for-the-badge&logo=mariadb&logoColor=white)](https://mariadb.org/)
[![Twitch](https://img.shields.io/badge/Twitch_API-9146FF?style=for-the-badge&logo=twitch&logoColor=white)](https://dev.twitch.tv/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/gpl-3.0)

[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-blueviolet?style=flat-square)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](https://github.com/RodrigoHernandezCastro/Nami)

**Nami** is a professional Discord bot that monitors Twitch streamers in real-time and automatically announces when they go live, with multi-server support, customizable mentions, and a scalable architecture.

[🚀 Installation](#-installation) • [⚙️ Configuration](#️-configuration) • [📖 Commands](#-commands) • [🏗️ Architecture](#️-architecture) • [🤝 Contribute](#-contribute)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🎯 Demo](#-demo)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [📖 Commands](#-commands)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [🧪 Testing](#-testing)
- [🐳 Docker](#-docker)
- [🛣️ Roadmap](#️-roadmap)
- [🤝 Contribute](#-contribute)
- [📜 License](#-license)

---

## ✨ Features

- 🔴 **Real-Time Monitoring** — Automatically detects when your favorite streamers go live.
- 🎨 **Customizable Announcements** — Unique messages per streamer with rich embeds.
- 👥 **Flexible Mentions** — `@everyone`, `@here` or up to **3 specific roles** per streamer.
- 🌐 **Multi-Server** — A single bot can serve multiple communities simultaneously.
- ⚡ **High Availability** — Async architecture with MariaDB connection pooling.
- 🔐 **Secure by Design** — Domain-level validation, robust error handling.
- 📊 **Structured Logging** — JSON logs ready for observability (Loki, Datadog, ELK).
- 🏛️ **Clean Architecture** — Maintainable, testable, and extensible code.
- 🔌 **Extensible** — Add new features without touching the core (Open/Closed Principle).

---

## 🎯 Demo

<div align="center">

### Live Stream Announcement

> 🔴 **shroud is LIVE**
>
> **Ranked Valorant — Road to Radiant**
>
> 🎮 **Playing:** VALORANT
> 👥 **Viewers:** 42,531
> 🔗 **[Watch stream](https://twitch.tv/shroud)**

</div>

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.12+ |
| **Bot Framework** | discord.py 2.4 |
| **Database** | MariaDB 11 + aiomysql |
| **External API** | Twitch Helix API |
| **Configuration** | Pydantic Settings |
| **Logging** | structlog (JSON) |
| **Testing** | pytest + pytest-asyncio |
| **Linting** | ruff + black + mypy |
| **Architecture** | Clean Architecture / Hexagonal |

---

## 🚀 Installation

### 📦 Prerequisites

- Python 3.12 or higher.
- MariaDB 11 or higher.
- An application from [Discord Developer Portal](https://discord.com/developers/applications).
- Credentials from [Twitch Developer Console](https://dev.twitch.tv/console).

### 🔧 Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RodrigoHernandezCastro/Nami.git
   cd Nami
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv env
   .\env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *Edit the `.env` file with your actual credentials.*

5. **Create the database:**
   ```bash
   mysql -u root -p
   CREATE DATABASE nami_bot;
   \q
   ```

6. **Run migrations:**
   ```bash
   python scripts/run_migrations.py
   ```

7. **Start the bot:**
   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

### 🔑 Environment Variables

Create a `.env` file in the project root based on the following:

```env
# Discord
DISCORD_TOKEN=<DISCORD_TOKEN>

# Twitch API
TWITCH_CLIENT_ID=<TWITCH_CLIENT_ID>
TWITCH_CLIENT_SECRET=<TWITCH_CLIENT_SECRET>

# Database (MariaDB)
DB_HOST=<DB_HOST>
DB_PORT=<DB_PORT>
DB_USER=<DB_USER>
DB_PASSWORD=<DB_PASSWORD>
DB_NAME=<DB_NAME>

# Logging
LOG_LEVEL=INFO

# Business rules
DEFAULT_STREAMER_LIMIT=15
CHECK_INTERVAL_SECONDS=60
```

### 🔗 Obtaining Credentials

<details> <summary><b>How to get your Discord token</b></summary>

1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a **New Application**.
3. In the **Bot** tab, click **Reset Token** to get your secret key.
4. Under "Privileged Gateway Intents", enable **Server Members Intent** and **Message Content Intent**.
5. Invite the bot using the **OAuth2 -> URL Generator** tab with the `bot` and `applications.commands` scopes.
</details>

<details> <summary><b>How to get Twitch credentials</b></summary>

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console).
2. Register a new application.
3. Set the **OAuth Redirect URL** to `http://localhost`.
4. Select the **Chat Bot** or **Application Integration** category.
5. Copy the **Client ID** and generate a **Client Secret**.
</details>

---

## 📖 Commands

Nami uses **Slash Commands** (`/`) for native and modern integration.

| Command | Parameters | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `/configure` | `channel` | Set the Twitch announcement channel. | Administrator |
| `/configure-youtube` | `channel` | Set the YouTube video announcement channel. | Administrator |
| `/configure-youtube-live` | `channel` | Set the YouTube live announcement channel. | Administrator |
| `/add` | `user`, `message`, `mention` | Add a Twitch streamer to monitor. | Administrator |
| `/remove` | `user` | Stop monitoring a Twitch streamer. | Administrator |
| `/list` | - | Show all monitored Twitch streamers. | Administrator |
| `/edit-twitch` | `user`, `message`, `mention` | Edit a monitored Twitch streamer's settings. | Administrator |
| `/add-youtube` | `user`, `message`, `mention` | Add a YouTube channel to monitor. | Administrator |
| `/edit-youtube` | `user`, `message`, `mention` | Edit a monitored YouTube channel. | Administrator |
| `/add-youtube-live` | `user`, `live_message`, `live_mention` | Configure YouTube live stream settings. | Administrator |
| `/list-youtube` | - | Show all monitored YouTube channels. | Administrator |
| `/remove-youtube` | `user` | Stop monitoring a YouTube channel. | Administrator |
| `/language` | `language` | Change the bot's language for this server. | Administrator |
| `/help all\|twitch\|youtube\|admin` | - | Show available commands by category. | Administrator |

---

## 🏗️ Architecture

The bot follows **Clean Architecture** (Hexagonal Architecture) principles, separating business logic from technical details.

```text
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION                            │
│          (Discord Cogs, Background Tasks)                   │
├─────────────────────────────────────────────────────────────┤
│                    APPLICATION                              │
│        (Use Cases — Pure Business Logic)                    │
├─────────────────────────────────────────────────────────────┤
│                    DOMAIN                                   │
│       (Entities, Value Objects, Exceptions)                 │
├─────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                           │
│    (MariaDB, Twitch API, Logging, Config)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```text
nami_bot/
├── src/
│   ├── domain/              # Entities and core business rules
│   ├── application/         # Use cases and interfaces (Ports)
│   ├── infrastructure/      # Adapters (DB, APIs, Logging)
│   ├── presentation/        # Discord entry points (Cogs, Tasks)
│   └── composition_root/    # Dependency injection
├── scripts/                 # Migration and maintenance scripts
├── tests/                   # Unit tests
├── main.py                  # Entry point
└── .env.example             # Example environment variables
```

---

## 🧪 Testing

```bash
# Run tests with pytest
pytest
```

---

## 🐳 Docker

```bash
# Quick deployment with Docker Compose
docker-compose up -d
```

---

## 🛣️ Roadmap

- [x] Refactored to Clean Architecture.
- [x] MariaDB support.
- [ ] Twitch EventSub (Webhooks) implementation.
- [ ] Web management dashboard.
- [ ] Kick and YouTube Live support.

---

## 🤝 Contribute

1. **Fork** the project.
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`).
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`).
4. **Push** to the branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request**.

---

## 📜 License

Distributed under the **GNU General Public License v3**. See `LICENSE` for more information.

---

<div align="center">
Built by <a href="https://github.com/RodrigoHernandezCastro">Rodrigo Hernández Castro</a>
</div>
