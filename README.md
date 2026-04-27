<div align="center">

# 🌊 Nami Bot
### *Tu navegante de streams en Discord*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.4-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Twitch](https://img.shields.io/badge/Twitch_API-9146FF?style=for-the-badge&logo=twitch&logoColor=white)](https://dev.twitch.tv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-blueviolet?style=flat-square)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](https://github.com/RodrigoHernandezCastro/Nami)

**Nami** es un bot de Discord profesional que monitorea streamers de Twitch en tiempo real y anuncia automáticamente cuando están en vivo, con soporte para múltiples servidores, menciones personalizadas y arquitectura escalable.

[🚀 Instalación](#-instalación) • [⚙️ Configuración](#️-configuración) • [📖 Comandos](#-comandos) • [🏗️ Arquitectura](#️-arquitectura) • [🤝 Contribuir](#-contribuir)

</div>

---

## 📋 Tabla de Contenidos

- [✨ Características](#-características)
- [🎯 Demo](#-demo)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [🚀 Instalación](#-instalación)
- [⚙️ Configuración](#️-configuración)
- [📖 Comandos](#-comandos)
- [🏗️ Arquitectura](#️-arquitectura)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🧪 Testing](#-testing)
- [🐳 Docker](#-docker)
- [🛣️ Roadmap](#️-roadmap)
- [🤝 Contribuir](#-contribuir)
- [📜 Licencia](#-licencia)

---

## ✨ Características

- 🔴 **Monitoreo en Tiempo Real** — Detecta automáticamente cuándo tus streamers favoritos pasan a estar en vivo.
- 🎨 **Anuncios Personalizables** — Mensajes únicos por streamer, con embeds enriquecidos.
- 👥 **Menciones Flexibles** — `@everyone`, `@here` o hasta **3 roles específicos** por streamer.
- 🌐 **Multi-Servidor** — Un solo bot puede servir a múltiples comunidades simultáneamente.
- ⚡ **Alta Disponibilidad** — Arquitectura asíncrona con pool de conexiones PostgreSQL.
- 🔐 **Seguro por Diseño** — Validación a nivel de dominio, manejo robusto de errores.
- 📊 **Logging Estructurado** — Logs en JSON listos para observabilidad (Loki, Datadog, ELK).
- 🏛️ **Clean Architecture** — Código mantenible, testeable y extensible.
- 🔌 **Extensible** — Añade nuevas features sin tocar el núcleo (Open/Closed Principle).

---

## 🎯 Demo

<div align="center">

### Anuncio de Stream en Vivo

> 🔴 **shroud está EN VIVO**
>
> **Ranked Valorant — Road to Radiant**
>
> 🎮 **Jugando:** VALORANT
> 👥 **Espectadores:** 42,531
> 🔗 **[Ver stream](https://twitch.tv/shroud)**

</div>

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología |
| :--- | :--- |
| **Lenguaje** | Python 3.12+ |
| **Framework Bot** | discord.py 2.4 |
| **Base de Datos** | PostgreSQL 15 + asyncpg |
| **API Externa** | Twitch Helix API |
| **Configuración** | Pydantic Settings |
| **Logging** | structlog (JSON) |
| **Testing** | pytest + pytest-asyncio |
| **Linting** | ruff + black + mypy |
| **Arquitectura** | Clean Architecture / Hexagonal |

---

## 🚀 Instalación

### 📦 Requisitos Previos

- Python 3.12 o superior.
- PostgreSQL 15 o superior.
- Una aplicación de [Discord Developer Portal](https://discord.com/developers/applications).
- Credenciales de [Twitch Developer Console](https://dev.twitch.tv/console).

### 🔧 Pasos de Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/RodrigoHernandezCastro/Nami.git
   cd Nami
   ```

2. **Crear entorno virtual:**
   ```bash
   # Windows
   python -m venv env
   .\env\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   ```
   *Edita el archivo `.env` con tus credenciales reales.*

5. **Crear la base de datos:**
   ```bash
   psql -U postgres
   CREATE DATABASE nami_bot;
   \q
   ```

6. **Ejecutar migraciones:**
   ```bash
   python scripts/run_migrations.py
   ```

7. **Iniciar el bot:**
   ```bash
   python main.py
   ```

---

## ⚙️ Configuración

### 🔑 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto basándote en lo siguiente:

```env
# 🤖 Discord
DISCORD_TOKEN=tu_token_de_discord_bot

# 📺 Twitch API
TWITCH_CLIENT_ID=tu_twitch_client_id
TWITCH_CLIENT_SECRET=tu_twitch_client_secret

# 🗄️ PostgreSQL
DATABASE_URL=postgresql://usuario:password@127.0.0.1:5432/nami_bot

# 📝 Logging
LOG_LEVEL=INFO

# ⚙️ Reglas de negocio
DEFAULT_STREAMER_LIMIT=15
CHECK_INTERVAL_SECONDS=60
```

### 🔗 Obtener Credenciales

<details> <summary><b>📘 Cómo obtener el token de Discord</b></summary>

1. Ve a [Discord Developer Portal](https://discord.com/developers/applications).
2. Crea una **New Application**.
3. En la pestaña **Bot**, haz clic en **Reset Token** para obtener tu clave secreta.
4. Bajo la sección "Privileged Gateway Intents", activa **Server Members Intent** y **Message Content Intent**.
5. Invita al bot usando la pestaña **OAuth2 -> URL Generator** con los scopes `bot` y `applications.commands`.
</details> 

<details> <summary><b>📺 Cómo obtener credenciales de Twitch</b></summary>

1. Entra en [Twitch Developer Console](https://dev.twitch.tv/console).
2. Registra una nueva aplicación.
3. Configura el **OAuth Redirect URL** como `http://localhost`.
4. Selecciona la categoría **Chat Bot** o **Application Integration**.
5. Copia el **Client ID** y genera un **Client Secret**.
</details>

---

## 📖 Comandos

Nami utiliza **Slash Commands** (`/`) para una integración nativa y moderna.

| Comando | Parámetros | Descripción | Permisos |
| :--- | :--- | :--- | :--- |
| `/configurar` | `canal` | Establece el canal donde se enviarán las alertas. | Administrador |
| `/añadir` | `usuario`, `mensaje`, `mencion` | Añade un streamer al monitoreo. | Administrador |
| `/eliminar` | `usuario` | Remueve un streamer de la base de datos. | Administrador |
| `/listar` | - | Muestra todos los streamers seguidos en el servidor. | Todos |

---

## 🏗️ Arquitectura

El bot sigue los principios de **Clean Architecture** (Arquitectura Hexagonal), separando la lógica de negocio de los detalles técnicos.

```text
┌─────────────────────────────────────────────────────────────┐
│                    🟢 PRESENTATION                          │
│          (Discord Cogs, Tareas Background)                  │
├─────────────────────────────────────────────────────────────┤
│                    🟡 APPLICATION                           │
│        (Use Cases — Lógica de Negocio Pura)                 │
├─────────────────────────────────────────────────────────────┤
│                    🟣 DOMAIN                                │
│       (Entidades, Value Objects, Excepciones)               │
├─────────────────────────────────────────────────────────────┤
│                    🔵 INFRASTRUCTURE                        │
│    (PostgreSQL, Twitch API, Logging, Config)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```text
nami_bot/
├── src/
│   ├── domain/              # Entidades y reglas fundamentales
│   ├── application/         # Casos de uso e interfaces (Puertos)
│   ├── infrastructure/      # Adaptadores (DB, APIs, Logging)
│   ├── presentation/        # Entrada de Discord (Cogs, Tasks)
│   └── composition_root/    # Inyección de dependencias
├── scripts/                 # Scripts de migración y mantenimiento
├── tests/                   # Pruebas unitarias
├── main.py                  # Punto de entrada
└── .env.example             # Ejemplo de variables de entorno
```

---

## 🧪 Testing

```bash
# Ejecutar tests con pytest
pytest
```

---

## 🐳 Docker

```bash
# Despliegue rápido con Docker Compose
docker-compose up -d
```

---

## 🛣️ Roadmap

- [x] Refactorización a Clean Architecture.
- [x] Soporte para PostgreSQL.
- [ ] Implementación de Twitch EventSub (Webhooks).
- [ ] Dashboard Web de gestión.
- [ ] Soporte para Kick y YouTube Live.

---

## 🤝 Contribuir

1. Haz un **Fork** del proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`).
3. Haz un **Commit** de tus cambios (`git commit -m 'Add AmazingFeature'`).
4. Haz un **Push** a la rama (`git push origin feature/AmazingFeature`).
5. Abre un **Pull Request**.

---

## 📜 Licencia

Distribuido bajo la Licencia **MIT**. Ver `LICENSE` para más información.

---

<div align="center">
Desarrollado por <a href="https://github.com/RodrigoHernandezCastro">Rodrigo Hernández Castro</a>
</div>
