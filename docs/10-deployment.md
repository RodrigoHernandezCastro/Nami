
---

## **📄 `docs/10-deployment.md`**

# 🚀 Deployment on Teramont

Step-by-step guide to deploy Nami Bot on the Teramont server with MariaDB.

---

## 📋 Preparation

### Requirements

- Active Teramont account
- SSH or web panel access
- Credentials for:
  - Discord Bot Token
  - Twitch API (Client ID + Secret)

---

## 🗄️ Step 1: Configure the Database

### 1.1. Connection credentials

| Parameter | Value |
|---|---|
| Host | `panther.teramont.net` |
| Port | `3306` |
| Database | `s4356_nami_bot` |
| User | `u4356_D25QQuuYC6` |
| Engine | MariaDB 10.8.8 |

---

### 1.2. Import the schema

**Option A — From phpMyAdmin:**

- Click **phpMyAdmin**
- Select `s4356_nami_bot`
- Go to the **SQL** tab
- Paste the contents of **`001_initial_schema.sql`** → **Go**

**Option B — From the "Import SQL into Database" button:**

- Click **Import SQL into Database**
- Upload the `001_initial_schema.sql` file
- Confirm

**Option C — From the Python script:**

```bash
python scripts/run_migrations.py
```

---

### 1.3. Verify the tables

```sql
SHOW TABLES;
```

You should see:

```
guild_configs
streamers
```

---

## 🤖 Step 2: Configure the Bot

### 2.1. Upload the code

**Option A — Git (recommended):**

```bash
ssh user@panther.teramont.net
cd ~
git clone https://github.com/your-user/nami-bot.git
cd nami-bot
```

**Option B — FTP/SFTP:**

Upload the entire project **except** the following paths:

- `venv/`
- `__pycache__/`
- `.env` (create it directly on the server)

---

### 2.2. Create virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4. Create the `.env` file

```bash
nano .env
```

Contents:

```env
# Discord
DISCORD_TOKEN=your_real_token

# Twitch
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

# MariaDB (Teramont)
DB_HOST=panther.teramont.net
DB_PORT=3306
DB_USER=u4356_D25QQuuYC6
DB_PASSWORD=your_real_password
DB_NAME=s4356_nami_bot

# Logging
LOG_LEVEL=INFO

# Business rules
DEFAULT_STREAMER_LIMIT=15
CHECK_INTERVAL_SECONDS=60
```

Save with `Ctrl+O` + `Enter`, exit with `Ctrl+X`.

> 🔒 **Security:** Restrict the file permissions immediately.
> ```bash
> chmod 600 .env
> ```

---

## ▶️ Step 3: Run the Bot

### 3.1. Manual test

```bash
python main.py
```

If the bot starts correctly, you'll see in the logs:

```json
{"event": "bot_ready", "commands_synced": 4, ...}
```

Press `Ctrl+C` to stop.

---

### 3.2. Keep it running 24/7

**Option A — systemd (recommended):**

Create the service file:

```bash
sudo nano /etc/systemd/system/nami-bot.service
```

Contents:

```ini
[Unit]
Description=Nami Discord Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/nami-bot
Environment="PATH=/home/your_user/nami-bot/venv/bin"
ExecStart=/home/your_user/nami-bot/venv/bin/python main.py
Restart=always
RestartSec=10

StandardOutput=append:/home/your_user/nami-bot/logs/output.log
StandardError=append:/home/your_user/nami-bot/logs/error.log

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nami-bot
sudo systemctl start nami-bot
```

Useful commands:

```bash
sudo systemctl status nami-bot       # Check status
sudo systemctl restart nami-bot      # Restart
sudo systemctl stop nami-bot         # Stop
journalctl -u nami-bot -f            # View live logs
```

---

**Option B — PM2** (if the plan doesn't support systemd):

```bash
npm install -g pm2
pm2 start main.py --name nami-bot --interpreter venv/bin/python
pm2 save
pm2 startup
```

Useful commands:

```bash
pm2 list                  # View processes
pm2 logs nami-bot         # View logs
pm2 restart nami-bot      # Restart
pm2 stop nami-bot         # Stop
```

---

**Option C — screen/tmux** (basic):

```bash
screen -S nami
source venv/bin/activate
python main.py

# Detach: Ctrl+A + D
# Reattach:  screen -r nami
```

---

## 🔁 Step 4: Update the Bot

```bash
cd ~/nami-bot
git pull                            # Download changes
source venv/bin/activate
pip install -r requirements.txt     # In case of new dependencies

# If there are new migrations:
python scripts/run_migrations.py

# Restart the bot
sudo systemctl restart nami-bot
```

---

## 📊 Step 5: Monitoring

### View logs in real-time

```bash
# systemd
journalctl -u nami-bot -f

# PM2
pm2 logs nami-bot
```

### Filter errors with `jq`

```bash
journalctl -u nami-bot -f -o cat | jq 'select(.level == "error")'
```

### Check DB status

```sql
SELECT COUNT(*) FROM streamers;
SELECT COUNT(*) FROM guild_configs;
SELECT * FROM streamers ORDER BY added_at DESC LIMIT 10;
```

---

## 🛡️ Step 6: Security

### Security checklist

- [ ] `.env` has `600` permissions
- [ ] `.env` is in `.gitignore`
- [ ] DB password is strong
- [ ] Discord token is not in the code
- [ ] Use HTTPS to download dependencies

### Recommended `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
venv/
.venv/

# Secrets
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

## 💾 Step 7: Backups

### Daily automatic backup

Create the script **`scripts/backup_db.sh`**:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
mysqldump -h panther.teramont.net -u u4356_D25QQuuYC6 -p'your_password' s4356_nami_bot \
    > /home/your_user/backups/nami_$DATE.sql

# Keep only the last 7 days
find /home/your_user/backups/ -name "nami_*.sql" -mtime +7 -delete
```

Schedule execution with cron:

```bash
chmod +x scripts/backup_db.sh
crontab -e
```

Add this line (daily backup at 3 AM):

```
0 3 * * * /home/your_user/nami-bot/scripts/backup_db.sh
```

> **Manual backup:** Teramont Panel → **Export Database to SQL**

---

## 🚨 Troubleshooting in Production

### The bot won't start

```bash
sudo systemctl status nami-bot
journalctl -u nami-bot -n 50
```

### The bot keeps restarting

```bash
journalctl -u nami-bot -f | grep -i error
```

Most common causes: misconfigured `.env`, unreachable DB, invalid Discord token.

### High memory usage

```bash
ps aux | grep python
```

If it consumes too much RAM, check DB connections or HTTP sessions that aren't being properly closed.

---

## ✅ Final Checklist

- [ ] DB created and migrated
- [ ] Code uploaded to the server
- [ ] `.env` configured with real credentials
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Manual test successful (`python main.py`)
- [ ] systemd/PM2 service configured
- [ ] Bot invited to the Discord server
- [ ] `/configure` command tested
- [ ] `/add` command tested
- [ ] Logs verified
- [ ] Automatic backup configured
