# 🗄️ Database

## Engine: MariaDB 10.8.8 (Teramont)
Nami uses **MariaDB** as its database engine, hosted on Teramont.

### 🌐 Connection

| Parameter | Value |
| :--- | :--- |
| **Host** | `panther.teramont.net` |
| **Port** | `3306` |
| **Database** | `s4356_nami_bot` |
| **User** | `u4356_D25QQuuYC6` |
| **Charset** | `utf8mb4` |

> [!IMPORTANT]
> **Credentials:** Passwords and sensitive data are managed exclusively through the `.env` file.

---

## 📊 Current Schema

### Table: `guild_configs`
Stores configuration specific to each Discord server.

| Column | Type | Description |
| :--- | :--- | :--- |
| `guild_id` | `BIGINT` (PK) | Unique Discord server ID. |
| `announcement_channel_id` | `BIGINT` | Announcement channel ID. |
| `streamer_limit` | `INTEGER` | Maximum allowed streamers (Default: 15). |
| `default_mention_type` | `VARCHAR(20)` | Default mention type. |
| `language` | `VARCHAR(5)` | Language code (Default: 'es'). |
| `created_at` | `TIMESTAMP` | Creation timestamp. |
| `updated_at` | `TIMESTAMP` | Last update timestamp. |

### Table: `streamers`
Stores Twitch channels monitored per server.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INT AUTO_INCREMENT` (PK) | Sequential internal ID. |
| `guild_id` | `BIGINT` (FK) | Relation to the associated server. |
| `username` | `VARCHAR(50)` | Twitch username. |
| `custom_message` | `TEXT` | Custom message for the announcement. |
| `mention_type` | `VARCHAR(20)` | `ninguno`, `everyone`, `here`, `rol`. |
| `mention_role_ids` | `LONGTEXT` | Role IDs in JSON format. |
| `is_online` | `BOOLEAN` | Current online status. |
| `added_at` | `TIMESTAMP` | Registration date. |

**Indexes and Constraints:**
* **Indexes:** `idx_streamers_guild_id`, `idx_streamers_username`, `idx_streamers_is_online`.
* **Unique Constraint:** `(guild_id, username)` — Prevents duplicate streamers within the same server.

---

# Schema and Database Management Guide

## 🛠️ Modifying the Schema

### Step 1: Create a new migration

Create the file with the corresponding sequential number inside:

```
src/infrastructure/persistence/migrations/
├── 001_initial_schema.sql
└── 002_add_nueva_feature.sql   ← NEW
```

---

### Step 2: Write the SQL

Example: adding the `notification_sound` column to the `guild_configs` table:

```sql
-- 002_add_notification_sound.sql

ALTER TABLE guild_configs
ADD COLUMN notification_sound VARCHAR(100) DEFAULT NULL;
```

---

### Step 3: Run migrations

**Option A — Automatic script:**

```bash
python scripts/run_migrations.py
```

**Option B — Manual import via phpMyAdmin on Teramont:**

- Log in to the Teramont panel
- Click **phpMyAdmin**
- Select the `s4356_nami_bot` database
- Go to the **SQL** tab → paste the script → **Go**

---

### Step 4: Update the entity

Edit **`src/domain/entities/guild_config.py`** to reflect the new field:

```python
# src/domain/entities/guild_config.py

@dataclass
class GuildConfig:
    guild_id: int
    announcement_channel_id: Optional[int] = None
    streamer_limit: int = 15
    default_mention_type: str = "ninguno"
    language: str = "es"
    notification_sound: Optional[str] = None   # ← NEW
```

---

### Step 5: Update the repository

Edit **`guild_repository_mysql.py`** to include the new field in all `SELECT`, `INSERT`, and `UPDATE` statements.

---

## 🔄 Backup and Restore

### Export from Teramont

- Teramont Panel → **Export Database to SQL**
- A `.sql` file will be downloaded

### Import to Teramont

- Panel → **Import SQL into Database**
- Select the file → **Upload**

---

## 💾 Switching Database Engines

Thanks to **Clean Architecture**, migrating from MariaDB to PostgreSQL only requires two steps:

**1.** Create `src/infrastructure/persistence/postgres/` with the new repositories.

**2.** Update **`container.py`** to point to the new implementation:

```python
# Before:
from src.infrastructure.persistence.mariadb.streamer_repository_mysql import (
    MariaDBStreamerRepository,
)
self.streamer_repo = MariaDBStreamerRepository(pool)

# After:
from src.infrastructure.persistence.postgres.streamer_repository_pg import (
    PostgresStreamerRepository,
)
self.streamer_repo = PostgresStreamerRepository(pool)
```
