<div align="center">

# 🌊 Nami Bot
### *Tu navegante de streams en Discord*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.4-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Twitch](https://img.shields.io/badge/Twitch_API-9146FF?style=for-the-badge&logo=twitch&logoColor=white)](https://dev.twitch.tv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-blueviolet?style=flat-square)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](https://github.com/RodrigoHernandezCastro/Nami)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen?style=flat-square)](https://github.com/RodrigoHernandezCastro/Nami)

**Nami** es un bot de Discord profesional que monitorea streamers de Twitch en tiempo real y anuncia automáticamente cuando están en vivo, con soporte para múltiples servidores, menciones personalizadas y arquitectura escalable.

[🚀 Instalación](#-instalación) • [⚙️ Configuración](#️-configuración) • [📖 Comandos](#-comandos) • [🏗️ Arquitectura](#️-arquitectura) • [🤝 Contribuir](#-contribuir)

</div>

---

## ✨ Características

- 🔴 **Monitoreo en Tiempo Real** — Detecta automáticamente cuándo tus streamers favoritos pasan a estar en vivo.
- 🎨 **Anuncios Personalizables** — Mensajes únicos por streamer con embeds enriquecidos.
- 👥 **Menciones Flexibles** — `@everyone`, `@here` o hasta **3 roles específicos** por streamer.
- 🌐 **Multi-Servidor** — Un solo bot puede servir a múltiples comunidades simultáneamente.
- ⚡ **Alta Disponibilidad** — Arquitectura asíncrona con pool de conexiones PostgreSQL.
- 🔐 **Seguro por Diseño** — Validación a nivel de dominio y manejo robusto de errores.
- 📊 **Logging Estructurado** — Logs en JSON listos para observabilidad (Loki, Datadog, ELK).
- 🏛️ **Clean Architecture** — Código mantenible, testeable y extensible.

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
| **Arquitectura** | Clean Architecture / Hexagonal |

---

## 🚀 Instalación

### 📦 Requisitos Previos
- Python 3.12 o superior.
- PostgreSQL 15 o superior.
- Una aplicación en el [Discord Developer Portal](https://discord.com/developers/applications).
- Credenciales en el [Twitch Developer Console](https://dev.twitch.tv/console).

### 🔧 Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone [https://github.com/RodrigoHernandezCastro/Nami.git](https://github.com/RodrigoHernandezCastro/Nami.git)
   cd nami-bot
