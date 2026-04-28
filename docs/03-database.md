# 🗄️ Base de Datos

## Motor: MariaDB 10.8.8 (Teramont)
Nami usa **MariaDB** como motor de base de datos, alojado en Teramont.

### 🌐 Conexión

| Parámetro | Valor |
| :--- | :--- |
| **Host** | `panther.teramont.net` |
| **Puerto** | `3306` |
| **Base de datos** | `s4356_nami_bot` |
| **Usuario** | `u4356_D25QQuuYC6` |
| **Charset** | `utf8mb4` |

> [!IMPORTANT]
> **Credenciales:** Las contraseñas y datos sensibles se gestionan exclusivamente a través del archivo `.env`.

---

## 📊 Esquema Actual

### Tabla: `guild_configs`
Almacena la configuración específica de cada servidor de Discord.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `guild_id` | `BIGINT` (PK) | ID único del servidor Discord. |
| `announcement_channel_id` | `BIGINT` | ID del canal de anuncios. |
| `streamer_limit` | `INTEGER` | Máximo de streamers permitidos (Default: 15). |
| `default_mention_type` | `VARCHAR(20)` | Tipo de mención predeterminada. |
| `language` | `VARCHAR(5)` | Código de idioma (Default: 'es'). |
| `created_at` | `TIMESTAMP` | Marca de tiempo de creación. |
| `updated_at` | `TIMESTAMP` | Marca de tiempo de última actualización. |

### Tabla: `streamers`
Almacena los canales de Twitch monitoreados por servidor.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` (PK) | ID interno secuencial. |
| `guild_id` | `BIGINT` (FK) | Relación con el servidor asociado. |
| `username` | `VARCHAR(50)` | Nombre de usuario en Twitch. |
| `custom_message` | `TEXT` | Mensaje personalizado para el anuncio. |
| `mention_type` | `VARCHAR(20)` | `ninguno`, `everyone`, `here`, `rol`. |
| `mention_role_ids` | `LONGTEXT` | IDs de roles en formato JSON. |
| `is_online` | `BOOLEAN` | Estado de conexión actual. |
| `added_at` | `TIMESTAMP` | Fecha de registro. |

**Índices y Restricciones:**
* **Índices:** `idx_streamers_guild_id`, `idx_streamers_username`, `idx_streamers_is_online`.
* **Constraint Único:** `(guild_id, username)` — Impide duplicar un mismo streamer dentro de un mismo servidor.

---

# Guía de Gestión del Esquema y Base de Datos

## 🛠️ Modificar el Esquema

### Paso 1: Crear una nueva migración

Crea el archivo con el número secuencial correspondiente dentro de:

```
src/infrastructure/persistence/migrations/
├── 001_initial_schema.sql
└── 002_add_nueva_feature.sql   ← NUEVA
```

---

### Paso 2: Escribir el SQL

Ejemplo: añadir la columna `notification_sound` a la tabla `guild_configs`:

```sql
-- 002_add_notification_sound.sql

ALTER TABLE guild_configs
ADD COLUMN notification_sound VARCHAR(100) DEFAULT NULL;
```

---

### Paso 3: Ejecutar las migraciones

**Opción A — Script automático:**

```bash
python scripts/run_migrations.py
```

**Opción B — Importación manual desde phpMyAdmin en Teramont:**

- Entrar al panel de Teramont
- Hacer clic en **phpMyAdmin**
- Seleccionar la base de datos `s4356_nami_bot`
- Ir a la pestaña **SQL** → pegar el script → **Ejecutar**

---

### Paso 4: Actualizar la entidad

Edita **`src/domain/entities/guild_config.py`** para reflejar el nuevo campo:

```python
# src/domain/entities/guild_config.py

@dataclass
class GuildConfig:
    guild_id: int
    announcement_channel_id: Optional[int] = None
    streamer_limit: int = 15
    default_mention_type: str = "ninguno"
    language: str = "es"
    notification_sound: Optional[str] = None   # ← NUEVO
```

---

### Paso 5: Actualizar el repositorio

Edita **`guild_repository_mysql.py`** para incluir el nuevo campo en todas las sentencias `SELECT`, `INSERT` y `UPDATE`.

---

## 🔄 Backup y Restore

### Exportar desde Teramont

- Panel de Teramont → **Export Database to SQL**
- Se descarga un archivo `.sql`

### Importar a Teramont

- Panel → **Import SQL into Database**
- Seleccionar el archivo → **Upload**

---

## 💾 Cambiar de Motor de Base de Datos

Gracias a la **Clean Architecture**, migrar de MariaDB a PostgreSQL solo requiere dos pasos:

**1.** Crear `src/infrastructure/persistence/postgres/` con los nuevos repositorios.

**2.** Actualizar **`container.py`** para apuntar a la nueva implementación:

```python
# Antes:
from src.infrastructure.persistence.mariadb.streamer_repository_mysql import (
    MariaDBStreamerRepository,
)
self.streamer_repo = MariaDBStreamerRepository(pool)

# Después:
from src.infrastructure.persistence.postgres.streamer_repository_pg import (
    PostgresStreamerRepository,
)
self.streamer_repo = PostgresStreamerRepository(pool)
```