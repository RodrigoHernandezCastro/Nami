# 📝 Sistema de Logging

Nami usa **structlog** para logs estructurados en **formato JSON**. Ideal para observabilidad (Loki, Datadog, ELK, Grafana).

---

## 🎯 ¿Por qué JSON?

### ❌ Log Tradicional (texto plano)

```
2025-01-15 12:34:56 INFO Streamer added: shroud in guild 123456
```

Problema: difícil de filtrar/buscar programáticamente.

### ✅ Log Estructurado (JSON)

```json
{
  "event": "streamer_added",
  "level": "info",
  "timestamp": "2025-01-15T12:34:56Z",
  "guild_id": 123456,
  "username": "shroud",
  "streamer_id": 42
}
```

Ventajas:
- 🔍 Filtrable por campo (`guild_id=123456`)
- 📊 Agregable (conteo de eventos)
- 🌐 Consumible por herramientas de monitoreo

---

## 🏗️ Arquitectura del Logger

```
┌────────────────────────────┐
│     Use Case               │
│  self._logger.info(...)    │
└────────────┬───────────────┘
             │ usa
             ▼
┌────────────────────────────┐
│  ILogger (interface)       │  ← Dominio no conoce structlog
└────────────┬───────────────┘
             │ implementa
             ▼
┌────────────────────────────┐
│  StructuredLogger          │  ← Implementación con structlog
│  (infrastructure)          │
└────────────────────────────┘
```

---

## 📐 Interface `ILogger`

**Ubicación:** `src/application/interfaces/logger.py`

```python
from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def info(self, event: str, **kwargs) -> None: ...

    @abstractmethod
    def warning(self, event: str, **kwargs) -> None: ...

    @abstractmethod
    def error(self, event: str, **kwargs) -> None: ...

    @abstractmethod
    def debug(self, event: str, **kwargs) -> None: ...
```

---

## 🎨 Convenciones

### Eventos en `snake_case`

```python
# ❌ MAL
logger.info("Streamer Added Successfully")

# ✅ BIEN
logger.info("streamer_added")
```

### Datos como kwargs

```python
# ❌ MAL: interpolación en el mensaje
logger.info(f"Streamer {username} added to guild {guild_id}")

# ✅ BIEN: datos estructurados
logger.info("streamer_added", username=username, guild_id=guild_id)
```

### Niveles apropiados
# Guía de Logging: Niveles, Eventos y Configuración

## 📊 Niveles de Log

| Nivel | Cuándo usarlo | Ejemplo |
|---|---|---|
| `debug` | Información de desarrollo | `"query_executed"` |
| `info` | Eventos normales del sistema | `"streamer_added"` |
| `warning` | Algo raro pero no crítico | `"twitch_rate_limit"` |
| `error` | Fallos que requieren atención | `"db_connection_lost"` |

---

## 💡 Ejemplos de Uso

### Evento de negocio

```python
self._logger.info(
    "streamer_added",
    guild_id=command.guild_id,
    username=username.value,
    streamer_id=created.id,
)
```

**Salida esperada:**

```json
{
  "event": "streamer_added",
  "level": "info",
  "timestamp": "2025-01-15T12:34:56Z",
  "guild_id": 123456789,
  "username": "shroud",
  "streamer_id": 42
}
```

---

### Warning con contexto

```python
self._logger.warning(
    "announcement_channel_not_found",
    guild_id=streamer.guild_id,
    channel_id=config.announcement_channel_id,
)
```

---

### Error con stack trace

```python
self._logger.error(
    "unexpected_error",
    error=str(e),
    error_type=type(e).__name__,
    user_id=interaction.user.id,
    exc_info=True,   # ← incluye el stack trace
)
```

---

## ⚙️ Configuración

### Nivel de log por entorno

Configura el nivel en **`.env`** según el entorno:

```env
LOG_LEVEL=INFO       # producción
# LOG_LEVEL=DEBUG    # desarrollo
```

---

## 📋 Eventos Estándar de Nami

| Evento | Cuándo se emite | Datos clave |
|---|---|---|
| `postgres_pool_created` | Al crear pool de BD | — |
| `twitch_client_initialized` | Al iniciar cliente Twitch | — |
| `bot_ready` | Bot listo | — |
| `commands_synced` | Comandos sincronizados | — |
| `streamer_added` | Nuevo streamer registrado | `guild_id`, `username`, `streamer_id` |
| `streamer_removed` | Streamer eliminado | `guild_id`, `username` |
| `streamer_went_live` | Detectado en vivo | `streamer_id`, `username` |
| `streamer_went_offline` | Detectado offline | `streamer_id`, `username` |
| `stream_announced` | Anuncio publicado | `guild_id`, `username` |
| `channel_configured` | Canal configurado | `guild_id`, `channel_id` |
| `domain_error` | Error de negocio | `type`, `user_id`, `guild_id` |
| `unexpected_error` | Error no esperado | `error`, `error_type`, `exc_info` |

---

## 🔍 Cómo Buscar Logs

### Pretty-print en terminal

```bash
python main.py | jq '.'
```

### Filtrar por evento

```bash
python main.py | jq 'select(.event == "streamer_added")'
```

### Filtrar por `guild_id`

```bash
python main.py | jq 'select(.guild_id == 123456789)'
```

### Guardar a archivo

```bash
python main.py > logs.jsonl 2>&1
```

---

## 🛠️ Añadir un Logger Custom

Si necesitas logs en archivo rotativo, crea **`src/infrastructure/logging/file_logger.py`**:

```python
import logging
from logging.handlers import RotatingFileHandler
from src.application.interfaces.logger import ILogger


class FileLogger(ILogger):
    def __init__(self, filename: str = "nami.log") -> None:
        handler = RotatingFileHandler(
            filename,
            maxBytes=10 * 1024 * 1024,   # 10 MB
            backupCount=5,
        )
        self._logger = logging.getLogger("nami")
        self._logger.addHandler(handler)

    def info(self, event: str, **kwargs):
        self._logger.info(f"{event} {kwargs}")

    # ... resto de métodos
```

Luego actualiza **`container.py`** para usar el nuevo logger:

```python
# Reemplazar StructuredLogger por:
self._logger = FileLogger("nami.log")
```

---

## ✅ Checklist

- [ ] ¿Usas `snake_case` para nombres de eventos?
- [ ] ¿Pasas los datos como `kwargs` (no dentro del mensaje)?
- [ ] ¿El nivel es apropiado (`info` / `warning` / `error`)?
- [ ] ¿Incluyes `exc_info=True` en errores inesperados?
- [ ] ¿El use case inyecta `ILogger` (no `structlog` directamente)?