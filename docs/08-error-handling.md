
---

## **📄 `docs/08-error-handling.md`**

````markdown
# ⚠️ Manejo de Errores

Nami usa un sistema de errores en **dos niveles**:

1. **Excepciones de dominio** (lógica de negocio)
2. **Handler global** (captura todo lo que sale mal)

---

## 🏛️ Jerarquía de Excepciones

```
Exception
  └── DomainError (base)
        ├── StreamerAlreadyExistsError
        ├── StreamerNotFoundError
        ├── StreamerLimitReachedError
        ├── StreamerNotOnTwitchError
        └── ChannelNotConfiguredError
```

**Ubicación:** `src/domain/exceptions/domain_exceptions.py`

```python
class DomainError(Exception):
    """Base para todos los errores de negocio."""
    pass


class StreamerAlreadyExistsError(DomainError):
    """Cuando se intenta añadir un streamer que ya existe."""
    pass


class StreamerNotFoundError(DomainError):
    """Cuando se busca un streamer que no existe."""
    pass


class StreamerLimitReachedError(DomainError):
    """Cuando se excede el límite permitido."""
    pass


class StreamerNotOnTwitchError(DomainError):
    """Cuando el usuario no existe en Twitch."""
    pass


class ChannelNotConfiguredError(DomainError):
    """Cuando no hay canal de anuncios configurado."""
    pass
```

---

## 🎯 Cuándo Lanzar Cada Tipo

### En el **Dominio** → `DomainError`

Cuando se viola una **regla de negocio**:

```python
# src/application/use_cases/add_streamer.py
if current_count >= guild_config.streamer_limit:
    raise StreamerLimitReachedError(
        f"Límite alcanzado: {guild_config.streamer_limit}"
    )
```

### En la **Infraestructura** → Convertir a `DomainError`

Las excepciones técnicas (SQL, HTTP) deben **traducirse** al dominio:

```python
# ❌ MAL: exponer excepción técnica
async def add(self, streamer):
    await cursor.execute(...)   # puede lanzar IntegrityError

# ✅ BIEN: traducir a excepción de dominio
async def add(self, streamer):
    try:
        await cursor.execute(...)
    except aiomysql.IntegrityError as e:
        if e.args[0] == 1062:   # Duplicate entry
            raise StreamerAlreadyExistsError(
                f"'{streamer.username}' ya existe."
            ) from e
        raise
```

---

## 🛡️ Handler Global

Captura **todas** las excepciones no manejadas en comandos slash.

**Ubicación:** `src/presentation/discord_bot/error_handler.py`

```python
class GlobalErrorHandler:
    ERROR_MAP = {
        StreamerAlreadyExistsError: ("⚠️", "Ese streamer ya está registrado."),
        StreamerLimitReachedError:  ("📛", "Has alcanzado el límite."),
        StreamerNotOnTwitchError:   ("❌", "Ese usuario no existe en Twitch."),
        ChannelNotConfiguredError:  ("⚙️", "Configura primero el canal."),
        StreamerNotFoundError:      ("🔍", "No encontré ese streamer."),
    }

    async def _on_app_command_error(self, interaction, error):
        original = getattr(error, "original", error)

        # 1) Errores mapeados
        for exc_type, (emoji, default_msg) in self.ERROR_MAP.items():
            if isinstance(original, exc_type):
                await interaction.followup.send(
                    f"{emoji} {original or default_msg}",
                    ephemeral=True,
                )
                return

        # 2) Cualquier otro DomainError
        if isinstance(original, DomainError):
            await interaction.followup.send(f"⚠️ {original}", ephemeral=True)
            return

        # 3) Errores inesperados → log + mensaje genérico
        self.logger.error("unexpected_error", error=str(original), exc_info=True)
        await interaction.followup.send(
            "💥 Ocurrió un error inesperado.",
            ephemeral=True,
        )
```

---

## ➕ Crear una Nueva Excepción

### Paso 1: Definir la clase

```python
# src/domain/exceptions/domain_exceptions.py

class InvalidTimezoneError(DomainError):
    """Cuando la zona horaria proporcionada no es válida."""
    pass
```

### Paso 2: Lanzarla en el Use Case

```python
if timezone not in VALID_TIMEZONES:
    raise InvalidTimezoneError(f"Zona horaria inválida: {timezone}")
```

### Paso 3: Mapearla en el Error Handler

```python
ERROR_MAP = {
    # ... existentes
    InvalidTimezoneError: ("🌐", "Zona horaria no válida."),
}
```

---

## 🎨 Patrones Útiles

### 1. Exception Chaining con `raise ... from ...`

Preserva el stack trace original:

```python
try:
    await cursor.execute(...)
except aiomysql.IntegrityError as e:
    raise StreamerAlreadyExistsError("Ya existe") from e
                                                   # ^^^^^^
                                                   # preserva origen
```

### 2. Respuestas Informativas

Pasa el mensaje específico, no solo el genérico:

```python
# ❌ MENOS INFO
raise StreamerLimitReachedError()

# ✅ MÁS INFO
raise StreamerLimitReachedError(f"Tu servidor permite máximo {limit} streamers")
```

### 3. Logging de Errores

El handler global **ya loggea**. No lo hagas manualmente en cada use case:

```python
# ❌ REDUNDANTE
try:
    ...
except Exception as e:
    logger.error("failed", error=e)
    raise

# ✅ DEJA QUE EL HANDLER LO HAGA
# El handler global lo capturará y loggeará
```

---

## 🧪 Testeando Excepciones

```python
import pytest
from src.domain.exceptions.domain_exceptions import StreamerLimitReachedError


@pytest.mark.asyncio
async def test_raises_limit_error():
    # ... setup

    with pytest.raises(StreamerLimitReachedError, match="Límite alcanzado"):
        await use_case.execute(command)
```

---

## 📋 Checklist

- [ ] ¿La excepción hereda de `DomainError`?
- [ ] ¿Tiene un docstring explicativo?
- [ ] ¿Está mapeada en `GlobalErrorHandler.ERROR_MAP`?
- [ ] ¿Las excepciones técnicas (SQL, HTTP) se convierten a `DomainError`?
- [ ] ¿Usas `raise X from e` para preservar el stack trace?