
---

## **📄 `docs/11-troubleshooting.md`**

# 🐛 Troubleshooting

Errores comunes y cómo resolverlos.

---

## ❌ `ImportError: cannot import name 'X' from '...'`

**Causa:** El archivo está vacío o la clase no existe.

**Solución:**
1. Verifica que el archivo exista y tenga contenido
2. Revisa que el nombre de la clase coincida
3. Asegúrate de que la carpeta tenga `__init__.py`

---

## ❌ `asyncpg.InvalidPasswordError` / `aiomysql.OperationalError`

**Causa:** Credenciales incorrectas en `.env`.

**Solución:**
```env
DB_HOST=panther.teramont.net
DB_PORT=3306
DB_USER=u4356_D25QQuuYC6
DB_PASSWORD=tu_password_real   ← Verifica esto
DB_NAME=s4356_nami_bot
```

---

## ❌ Los comandos slash no aparecen en Discord

**Causa:** No se sincronizaron o el bot no tiene el scope `applications.commands`.

**Solución:**
1. Verifica que al iniciar veas: `bot_ready commands_synced=4`
2. Si no, espera 1 hora (Discord cachea comandos globales)
3. O invita el bot con el scope correcto

---

## ❌ `discord.errors.Forbidden`

**Causa:** El bot no tiene permisos para enviar mensajes en el canal.

**Solución:** Dale al bot los permisos `Send Messages` y `Embed Links` en el canal configurado.

---

## ❌ `StreamerNotOnTwitchError` pero el usuario sí existe

**Causa:** Token de Twitch expirado o credenciales incorrectas.

**Solución:**
1. Verifica `TWITCH_CLIENT_ID` y `TWITCH_CLIENT_SECRET`
2. Reinicia el bot (genera token nuevo)

---

## ❌ El bot no detecta streams en vivo

**Causa:** La tarea en background no está corriendo.

**Solución:**
1. Revisa los logs al iniciar: debe aparecer `stream_checker_started`
2. Verifica `CHECK_INTERVAL_SECONDS` en `.env` (default: 60)
3. Confirma que hay streamers con canal configurado

---

## ❌ `Duplicate entry for key 'unique_streamer_per_guild'`

**Causa:** Intentaste añadir un streamer que ya existe.

**Solución:** Esto es un comportamiento esperado. El bot lo maneja con `StreamerAlreadyExistsError`.

---

## 🔍 Cómo Debuggear

### 1. Activa logs DEBUG

```env
LOG_LEVEL=DEBUG
```

### 2. Revisa la base de datos

```sql
SELECT * FROM guild_configs;
SELECT * FROM streamers;
```

### 3. Usa `print()` temporales

```python
print(f"🔍 DEBUG: streamers encontrados = {streamers}")
```

### 4. Verifica conectividad

```bash
ping panther.teramont.net
```
