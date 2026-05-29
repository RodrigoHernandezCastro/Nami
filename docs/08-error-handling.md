
---

## **📄 `docs/08-error-handling.md`**

# ⚠️ Error Handling

Nami uses a **two-level** error system:

1. **Domain exceptions** (business logic)
2. **Global handler** (catches everything that goes wrong)

---

## 🏛️ Exception Hierarchy

```
Exception
  └── DomainError (base)
        ├── StreamerAlreadyExistsError
        ├── StreamerNotFoundError
        ├── StreamerLimitReachedError
        ├── StreamerNotOnTwitchError
        └── ChannelNotConfiguredError
```

**Location:** `src/domain/exceptions/domain_exceptions.py`

```python
class DomainError(Exception):
    """Base for all business errors."""
    pass


class StreamerAlreadyExistsError(DomainError):
    """When trying to add a streamer that already exists."""
    pass


class StreamerNotFoundError(DomainError):
    """When searching for a streamer that does not exist."""
    pass


class StreamerLimitReachedError(DomainError):
    """When the allowed limit is exceeded."""
    pass


class StreamerNotOnTwitchError(DomainError):
    """When the user does not exist on Twitch."""
    pass


class ChannelNotConfiguredError(DomainError):
    """When no announcement channel is configured."""
    pass
```

---

## 🎯 When to Throw Each Type

### In **Domain** → `DomainError`

When a **business rule** is violated:

```python
# src/application/use_cases/add_streamer.py
if current_count >= guild_config.streamer_limit:
    raise StreamerLimitReachedError(
        f"Limit reached: {guild_config.streamer_limit}"
    )
```

### In **Infrastructure** → Convert to `DomainError`

Technical exceptions (SQL, HTTP) should be **translated** to the domain:

```python
# ❌ BAD: expose technical exception
async def add(self, streamer):
    await cursor.execute(...)   # may raise IntegrityError

# ✅ GOOD: translate to domain exception
async def add(self, streamer):
    try:
        await cursor.execute(...)
    except aiomysql.IntegrityError as e:
        if e.args[0] == 1062:   # Duplicate entry
            raise StreamerAlreadyExistsError(
                f"'{streamer.username}' already exists."
            ) from e
        raise
```

---

## 🛡️ Global Handler

Catches **all** unhandled exceptions in slash commands.

**Location:** `src/presentation/discord_bot/error_handler.py`

```python
class GlobalErrorHandler:
    ERROR_MAP = {
        StreamerAlreadyExistsError: ("⚠️", "That streamer is already registered."),
        StreamerLimitReachedError:  ("📛", "You have reached the limit."),
        StreamerNotOnTwitchError:   ("❌", "That user does not exist on Twitch."),
        ChannelNotConfiguredError:  ("⚙️", "Configure the channel first."),
        StreamerNotFoundError:      ("🔍", "I couldn't find that streamer."),
    }

    async def _on_app_command_error(self, interaction, error):
        original = getattr(error, "original", error)

        # 1) Mapped errors
        for exc_type, (emoji, default_msg) in self.ERROR_MAP.items():
            if isinstance(original, exc_type):
                await interaction.followup.send(
                    f"{emoji} {original or default_msg}",
                    ephemeral=True,
                )
                return

        # 2) Any other DomainError
        if isinstance(original, DomainError):
            await interaction.followup.send(f"⚠️ {original}", ephemeral=True)
            return

        # 3) Unexpected errors → log + generic message
        self.logger.error("unexpected_error", error=str(original), exc_info=True)
        await interaction.followup.send(
            "💥 An unexpected error occurred.",
            ephemeral=True,
        )
```

---

## ➕ Creating a New Exception

### Step 1: Define the class

```python
# src/domain/exceptions/domain_exceptions.py

class InvalidTimezoneError(DomainError):
    """When the provided timezone is not valid."""
    pass
```

### Step 2: Throw it in the Use Case

```python
if timezone not in VALID_TIMEZONES:
    raise InvalidTimezoneError(f"Invalid timezone: {timezone}")
```

### Step 3: Map it in the Error Handler

```python
ERROR_MAP = {
    # ... existing
    InvalidTimezoneError: ("🌐", "Invalid timezone."),
}
```

---

## 🎨 Useful Patterns

### 1. Exception Chaining with `raise ... from ...`

Preserves the original stack trace:

```python
try:
    await cursor.execute(...)
except aiomysql.IntegrityError as e:
    raise StreamerAlreadyExistsError("Already exists") from e
                                                        # ^^^^^^
                                                        # preserves origin
```

### 2. Informative Responses

Pass the specific message, not just the generic one:

```python
# ❌ LESS INFO
raise StreamerLimitReachedError()

# ✅ MORE INFO
raise StreamerLimitReachedError(f"Your server allows a maximum of {limit} streamers")
```

### 3. Error Logging

The global handler **already logs**. Don't do it manually in every use case:

```python
# ❌ REDUNDANT
try:
    ...
except Exception as e:
    logger.error("failed", error=e)
    raise

# ✅ LET THE HANDLER DO IT
# The global handler will catch and log it
```

---

## 🧪 Testing Exceptions

```python
import pytest
from src.domain.exceptions.domain_exceptions import StreamerLimitReachedError


@pytest.mark.asyncio
async def test_raises_limit_error():
    # ... setup

    with pytest.raises(StreamerLimitReachedError, match="Limit reached"):
        await use_case.execute(command)
```

---

## 📋 Checklist

- [ ] Does the exception inherit from `DomainError`?
- [ ] Does it have an explanatory docstring?
- [ ] Is it mapped in `GlobalErrorHandler.ERROR_MAP`?
- [ ] Are technical exceptions (SQL, HTTP) converted to `DomainError`?
- [ ] Do you use `raise X from e` to preserve the stack trace?
