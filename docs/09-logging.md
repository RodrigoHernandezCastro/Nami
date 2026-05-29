# 📝 Logging System

Nami uses **structlog** for structured logs in **JSON format**. Ideal for observability (Loki, Datadog, ELK, Grafana).

---

## 🎯 Why JSON?

### ❌ Traditional Logging (plain text)

```
2025-01-15 12:34:56 INFO Streamer added: shroud in guild 123456
```

Problem: difficult to filter/search programmatically.

### ✅ Structured Logging (JSON)

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

Advantages:
- 🔍 Filterable by field (`guild_id=123456`)
- 📊 Aggregable (event counting)
- 🌐 Consumable by monitoring tools

---

## 🏗️ Logger Architecture

```
┌────────────────────────────┐
│     Use Case               │
│  self._logger.info(...)    │
└────────────┬───────────────┘
             │ uses
             ▼
┌────────────────────────────┐
│  ILogger (interface)        │  ← Domain doesn't know structlog
└────────────┬───────────────┘
             │ implements
             ▼
┌────────────────────────────┐
│  StructuredLogger          │  ← Implementation with structlog
│  (infrastructure)          │
└────────────────────────────┘
```

---

## 📐 `ILogger` Interface

**Location:** `src/application/interfaces/logger.py`

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

## 🎨 Conventions

### Events in `snake_case`

```python
# ❌ BAD
logger.info("Streamer Added Successfully")

# ✅ GOOD
logger.info("streamer_added")
```

### Data as kwargs

```python
# ❌ BAD: interpolation in the message
logger.info(f"Streamer {username} added to guild {guild_id}")

# ✅ GOOD: structured data
logger.info("streamer_added", username=username, guild_id=guild_id)
```

### Appropriate levels
# Logging Guide: Levels, Events, and Configuration

## 📊 Log Levels

| Level | When to use | Example |
|---|---|---|
| `debug` | Development information | `"query_executed"` |
| `info` | Normal system events | `"streamer_added"` |
| `warning` | Something odd but not critical | `"twitch_rate_limit"` |
| `error` | Failures requiring attention | `"db_connection_lost"` |

---

## 💡 Usage Examples

### Business event

```python
self._logger.info(
    "streamer_added",
    guild_id=command.guild_id,
    username=username.value,
    streamer_id=created.id,
)
```

**Expected output:**

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

### Warning with context

```python
self._logger.warning(
    "announcement_channel_not_found",
    guild_id=streamer.guild_id,
    channel_id=config.announcement_channel_id,
)
```

---

### Error with stack trace

```python
self._logger.error(
    "unexpected_error",
    error=str(e),
    error_type=type(e).__name__,
    user_id=interaction.user.id,
    exc_info=True,   # ← includes stack trace
)
```

---

## ⚙️ Configuration

### Log level by environment

Set the level in **`.env`** according to the environment:

```env
LOG_LEVEL=INFO       # production
# LOG_LEVEL=DEBUG    # development
```

---

## 📋 Standard Nami Events

| Event | When emitted | Key data |
|---|---|---|
| `postgres_pool_created` | On DB pool creation | — |
| `twitch_client_initialized` | On Twitch client startup | — |
| `bot_ready` | Bot ready | — |
| `commands_synced` | Commands synced | — |
| `streamer_added` | New streamer registered | `guild_id`, `username`, `streamer_id` |
| `streamer_removed` | Streamer removed | `guild_id`, `username` |
| `streamer_went_live` | Detected live | `streamer_id`, `username` |
| `streamer_went_offline` | Detected offline | `streamer_id`, `username` |
| `stream_announced` | Announcement published | `guild_id`, `username` |
| `channel_configured` | Channel configured | `guild_id`, `channel_id` |
| `domain_error` | Business error | `type`, `user_id`, `guild_id` |
| `unexpected_error` | Unexpected error | `error`, `error_type`, `exc_info` |

---

## 🔍 How to Search Logs

### Pretty-print in terminal

```bash
python main.py | jq '.'
```

### Filter by event

```bash
python main.py | jq 'select(.event == "streamer_added")'
```

### Filter by `guild_id`

```bash
python main.py | jq 'select(.guild_id == 123456789)'
```

### Save to file

```bash
python main.py > logs.jsonl 2>&1
```

---

## 🛠️ Adding a Custom Logger

If you need logs in rotating files, create **`src/infrastructure/logging/file_logger.py`**:

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

    # ... remaining methods
```

Then update **`container.py`** to use the new logger:

```python
# Replace StructuredLogger with:
self._logger = FileLogger("nami.log")
```

---

## ✅ Checklist

- [ ] Do you use `snake_case` for event names?
- [ ] Do you pass data as `kwargs` (not inside the message)?
- [ ] Is the level appropriate (`info` / `warning` / `error`)?
- [ ] Do you include `exc_info=True` in unexpected errors?
- [ ] Does the use case inject `ILogger` (not `structlog` directly)?
