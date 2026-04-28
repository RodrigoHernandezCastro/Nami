
---

## **📄 `docs/10-deployment.md`**

# 🚀 Despliegue en Teramont

Guía paso a paso para desplegar Nami Bot en el servidor de Teramont con MariaDB.

---

## 📋 Preparación

### Requisitos

- Cuenta activa en Teramont
- Acceso SSH o panel web
- Credenciales de:
  - Discord Bot Token
  - Twitch API (Client ID + Secret)

---

## 🗄️ Paso 1: Configurar la Base de Datos

### 1.1. Verificar MariaDB en Teramont

En el panel de Teramont → **Manage Databases**:
# Guía de Despliegue en Producción (Teramont)

## 🗄️ Paso 1: Configurar la Base de Datos

### 1.1. Credenciales de conexión

| Parámetro | Valor |
|---|---|
| Host | `panther.teramont.net` |
| Puerto | `3306` |
| Database | `s4356_nami_bot` |
| Usuario | `u4356_D25QQuuYC6` |
| Motor | MariaDB 10.8.8 |

---

### 1.2. Importar el esquema

**Opción A — Desde phpMyAdmin:**

- Hacer clic en **phpMyAdmin**
- Seleccionar `s4356_nami_bot`
- Ir a la pestaña **SQL**
- Pegar el contenido de **`001_initial_schema.sql`** → **Go**

**Opción B — Desde el botón "Import SQL into Database":**

- Clic en **Import SQL into Database**
- Subir el archivo `001_initial_schema.sql`
- Confirmar

**Opción C — Desde el script Python:**

```bash
python scripts/run_migrations.py
```

---

### 1.3. Verificar las tablas

```sql
SHOW TABLES;
```

Deberías ver:

```
guild_configs
streamers
```

---

## 🤖 Paso 2: Configurar el Bot

### 2.1. Subir el código

**Opción A — Git (recomendado):**

```bash
ssh usuario@panther.teramont.net
cd ~
git clone https://github.com/tu-usuario/nami-bot.git
cd nami-bot
```

**Opción B — FTP/SFTP:**

Sube todo el proyecto **excepto** las siguientes rutas:

- `venv/`
- `__pycache__/`
- `.env` (créalo directamente en el servidor)

---

### 2.2. Crear entorno virtual

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4. Crear el archivo `.env`

```bash
nano .env
```

Contenido:

```env
# Discord
DISCORD_TOKEN=tu_token_real

# Twitch
TWITCH_CLIENT_ID=tu_client_id
TWITCH_CLIENT_SECRET=tu_client_secret

# MariaDB (Teramont)
DB_HOST=panther.teramont.net
DB_PORT=3306
DB_USER=u4356_D25QQuuYC6
DB_PASSWORD=tu_password_real
DB_NAME=s4356_nami_bot

# Logging
LOG_LEVEL=INFO

# Reglas de negocio
DEFAULT_STREAMER_LIMIT=15
CHECK_INTERVAL_SECONDS=60
```

Guardar con `Ctrl+O` + `Enter`, salir con `Ctrl+X`.

> 🔒 **Seguridad:** Restringe los permisos del archivo inmediatamente.
> ```bash
> chmod 600 .env
> ```

---

## ▶️ Paso 3: Ejecutar el Bot

### 3.1. Prueba manual

```bash
python main.py
```

Si el bot arrancó correctamente, verás en los logs:

```json
{"event": "bot_ready", "commands_synced": 4, ...}
```

Presiona `Ctrl+C` para detener.

---

### 3.2. Mantenerlo corriendo 24/7

**Opción A — systemd (recomendado):**

Crea el archivo de servicio:

```bash
sudo nano /etc/systemd/system/nami-bot.service
```

Contenido:

```ini
[Unit]
Description=Nami Discord Bot
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/home/tu_usuario/nami-bot
Environment="PATH=/home/tu_usuario/nami-bot/venv/bin"
ExecStart=/home/tu_usuario/nami-bot/venv/bin/python main.py
Restart=always
RestartSec=10

StandardOutput=append:/home/tu_usuario/nami-bot/logs/output.log
StandardError=append:/home/tu_usuario/nami-bot/logs/error.log

[Install]
WantedBy=multi-user.target
```

Activa el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nami-bot
sudo systemctl start nami-bot
```

Comandos útiles:

```bash
sudo systemctl status nami-bot       # Ver estado
sudo systemctl restart nami-bot      # Reiniciar
sudo systemctl stop nami-bot         # Detener
journalctl -u nami-bot -f            # Ver logs en vivo
```

---

**Opción B — PM2** (si el plan no permite systemd):

```bash
npm install -g pm2
pm2 start main.py --name nami-bot --interpreter venv/bin/python
pm2 save
pm2 startup
```

Comandos útiles:

```bash
pm2 list                  # Ver procesos
pm2 logs nami-bot         # Ver logs
pm2 restart nami-bot      # Reiniciar
pm2 stop nami-bot         # Detener
```

---

**Opción C — screen/tmux** (básico):

```bash
screen -S nami
source venv/bin/activate
python main.py

# Desconectar: Ctrl+A + D
# Reconectar:  screen -r nami
```

---

## 🔁 Paso 4: Actualizar el Bot

```bash
cd ~/nami-bot
git pull                            # Descargar cambios
source venv/bin/activate
pip install -r requirements.txt     # Por si hay nuevas dependencias

# Si hay migraciones nuevas:
python scripts/run_migrations.py

# Reiniciar el bot
sudo systemctl restart nami-bot
```

---

## 📊 Paso 5: Monitoreo

### Ver logs en tiempo real

```bash
# systemd
journalctl -u nami-bot -f

# PM2
pm2 logs nami-bot
```

### Filtrar errores con `jq`

```bash
journalctl -u nami-bot -f -o cat | jq 'select(.level == "error")'
```

### Verificar estado de la BD

```sql
SELECT COUNT(*) FROM streamers;
SELECT COUNT(*) FROM guild_configs;
SELECT * FROM streamers ORDER BY added_at DESC LIMIT 10;
```

---

## 🛡️ Paso 6: Seguridad

### Checklist de seguridad

- [ ] `.env` tiene permisos `600`
- [ ] `.env` está en `.gitignore`
- [ ] Password de BD es fuerte
- [ ] Token de Discord no está en el código
- [ ] Usar HTTPS para descargar dependencias

### `.gitignore` recomendado

```gitignore
# Python
__pycache__/
*.pyc
venv/
.venv/

# Secretos
.env
.env.local

# Logs
*.log
logs/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## 💾 Paso 7: Backups

### Backup automático diario

Crea el script **`scripts/backup_db.sh`**:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
mysqldump -h panther.teramont.net -u u4356_D25QQuuYC6 -p'tu_password' s4356_nami_bot \
    > /home/tu_usuario/backups/nami_$DATE.sql

# Mantener solo los últimos 7 días
find /home/tu_usuario/backups/ -name "nami_*.sql" -mtime +7 -delete
```

Programa la ejecución con cron:

```bash
chmod +x scripts/backup_db.sh
crontab -e
```

Añade esta línea (backup diario a las 3 AM):

```
0 3 * * * /home/tu_usuario/nami-bot/scripts/backup_db.sh
```

> **Backup manual:** Panel de Teramont → **Export Database to SQL**

---

## 🚨 Solución de Problemas en Producción

### El bot no arranca

```bash
sudo systemctl status nami-bot
journalctl -u nami-bot -n 50
```

### El bot se reinicia constantemente

```bash
journalctl -u nami-bot -f | grep -i error
```

Causas más comunes: `.env` mal configurado, BD inalcanzable, token de Discord inválido.

### Memoria alta

```bash
ps aux | grep python
```

Si consume demasiada RAM, revisa conexiones de BD o sesiones HTTP que no se estén cerrando correctamente.

---

## ✅ Checklist Final

- [ ] BD creada y migrada
- [ ] Código subido al servidor
- [ ] `.env` configurado con credenciales reales
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Prueba manual exitosa (`python main.py`)
- [ ] Servicio systemd/PM2 configurado
- [ ] Bot invitado al servidor Discord
- [ ] Comando `/configurar` probado
- [ ] Comando `/añadir` probado
- [ ] Logs verificados
- [ ] Backup automático configurado
