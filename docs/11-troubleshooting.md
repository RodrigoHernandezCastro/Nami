
---

## **📄 `docs/11-troubleshooting.md`**

# 🐛 Troubleshooting

Common errors and how to solve them.

---

## ❌ `ImportError: cannot import name 'X' from '...'`

**Cause:** The file is empty or the class doesn't exist.

**Solution:**
1. Verify the file exists and has content
2. Check that the class name matches
3. Make sure the folder has `__init__.py`

---

## ❌ `asyncpg.InvalidPasswordError` / `aiomysql.OperationalError`

**Cause:** Incorrect credentials in `.env`.

**Solution:**
```env
DB_HOST=panther.teramont.net
DB_PORT=3306
DB_USER=u4356_D25QQuuYC6
DB_PASSWORD=your_real_password   ← Verify this
DB_NAME=s4356_nami_bot
```

---

## ❌ Slash commands don't appear in Discord

**Cause:** They weren't synced or the bot doesn't have the `applications.commands` scope.

**Solution:**
1. Verify on startup you see: `bot_ready commands_synced=4`
2. If not, wait 1 hour (Discord caches global commands)
3. Or invite the bot with the correct scope

---

## ❌ `discord.errors.Forbidden`

**Cause:** The bot doesn't have permission to send messages in the channel.

**Solution:** Give the bot `Send Messages` and `Embed Links` permissions in the configured channel.

---

## ❌ `StreamerNotOnTwitchError` but the user does exist

**Cause:** Expired Twitch token or incorrect credentials.

**Solution:**
1. Verify `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET`
2. Restart the bot (generates a new token)

---

## ❌ The bot doesn't detect live streams

**Cause:** The background task is not running.

**Solution:**
1. Check the logs on startup: `stream_checker_started` should appear
2. Verify `CHECK_INTERVAL_SECONDS` in `.env` (default: 60)
3. Confirm there are streamers with a configured channel

---

## ❌ `Duplicate entry for key 'unique_streamer_per_guild'`

**Cause:** You tried to add a streamer that already exists.

**Solution:** This is expected behavior. The bot handles it with `StreamerAlreadyExistsError`.

---

## 🔍 How to Debug

### 1. Enable DEBUG logs

```env
LOG_LEVEL=DEBUG
```

### 2. Check the database

```sql
SELECT * FROM guild_configs;
SELECT * FROM streamers;
```

### 3. Use temporary `print()`

```python
print(f"🔍 DEBUG: streamers found = {streamers}")
```

### 4. Check connectivity

```bash
ping panther.teramont.net
```
