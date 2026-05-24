# Academy IVR

Academy IVR is an in-house Interactive Voice Response (IVR) system built for the **Call for Life** project. It handles outbound call campaigns, VXML-driven call flows, scheduled reporting, and a Vue.js web dashboard for monitoring and management.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [What Each Component Does](#what-each-component-does)
- [Prerequisites](#prerequisites)
- [Installation on a Bare Ubuntu Server](#installation-on-a-bare-ubuntu-server)
  - [Step 1 — Update the system](#step-1--update-the-system)
  - [Step 2 — Install system dependencies](#step-2--install-system-dependencies)
  - [Step 3 — Install MySQL 8](#step-3--install-mysql-8)
  - [Step 4 — Install Redis](#step-4--install-redis)
  - [Step 5 — Install Asterisk](#step-5--install-asterisk)
  - [Step 6 — Install Node.js](#step-6--install-nodejs)
  - [Step 7 — Clone the repository](#step-7--clone-the-repository)
  - [Step 8 — Create a Python virtual environment](#step-8--create-a-python-virtual-environment)
  - [Step 9 — Install Python dependencies](#step-9--install-python-dependencies)
  - [Step 10 — Create and edit config.json](#step-10--create-and-edit-configjson)
  - [Step 11 — Run database migrations](#step-11--run-database-migrations)
  - [Step 12 — Configure Asterisk](#step-12--configure-asterisk)
  - [Step 13 — Create the first admin user](#step-13--create-the-first-admin-user)
  - [Step 14 — Set up the IVR API as a systemd service](#step-14--set-up-the-ivr-api-as-a-systemd-service)
  - [Step 15 — Set up the Asterisk events listener as a systemd service](#step-15--set-up-the-asterisk-events-listener-as-a-systemd-service)
  - [Step 16 — Set up cron jobs](#step-16--set-up-cron-jobs)
  - [Step 17 — Build and serve the Vue dashboard with nginx](#step-17--build-and-serve-the-vue-dashboard-with-nginx)
  - [Step 18 — Verify everything is running](#step-18--verify-everything-is-running)
- [SIP Phone Setup](#sip-phone-setup)
- [Updating the Application](#updating-the-application)
- [Environment Variables Reference](#environment-variables-reference)
- [Running the Test Suite](#running-the-test-suite)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Code Style](#code-style)
- [Docker Alternative](#docker-alternative)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Architecture Overview

```
External App / SIP Phone
        │
        ▼
  Asterisk PBX ──────────────── SIP (port 5060)
        │
        ├── AMI (port 5038) ──► Events Listener ──► Flask API
        ├── ARI (port 8088) ──► Flask API
        └── AGI ─────────────► agi.py ──► VXMLParser ──► External VXML Server
                                               │
                                        Asterisk plays audio,
                                        captures DTMF input
        │
        ▼
  Flask API (port 5000, via nginx)
        │
        ├── MySQL 8 (port 3306)   — users, apps, CDR, reports
        ├── Redis  (port 6379)    — call queue, CDR cache, JWT sessions
        └── Gunicorn workers
        │
        ▼
  Vue Dashboard (port 8000, served by nginx)
```

---

## What Each Component Does

| Component | Role |
|---|---|
| **Asterisk** | The telephony engine. Answers and originates SIP calls, runs `agi.py` on each call, fires AMI events on call state changes |
| **agi.py** | Called by Asterisk on every call. Reads the VXML app URL from config, fetches and parses VXML, plays audio, captures DTMF input |
| **Flask API** | REST API for the dashboard. Also receives AMI event callbacks from the events listener and processes the call queue |
| **Events Listener** | Long-running Python script that connects to the Asterisk AMI and forwards `OriginateResponse` and `Hangup` events to the Flask API |
| **MySQL** | Stores users, IVR applications, call detail records (CDR), scheduled reports |
| **Redis** | Short-lived call state cache (CDR data during a call), call queue for when all channels are busy |
| **Vue Dashboard** | Web UI for admins — manage IVR apps, view CDR charts, manage users, download reports |
| **nginx** | Serves the built Vue dashboard as static files on port 8000 |

---

## Prerequisites

**Server requirements (minimum)**

| Resource | Minimum |
|---|---|
| OS | Ubuntu 22.04 LTS or 24.04 LTS |
| CPU | 2 cores |
| RAM | 2 GB |
| Disk | 20 GB |

**Your machine needs:**
- Root or sudo access
- A working internet connection during installation
- A SIP phone or softphone to test calls (see [SIP Phone Setup](#sip-phone-setup))

---

## Installation on a Bare Ubuntu Server

All commands assume you are logged in as **root**, or you prefix each with `sudo`. The application is installed to `/root/ivr`. If you use a different path, replace `/root/ivr` everywhere below.

---

### Step 1 — Update the system

```bash
apt update && apt upgrade -y
reboot
```

After the reboot, log back in before continuing.

---

### Step 2 — Install system dependencies

```bash
apt install -y \
    git curl wget gnupg2 lsb-release ca-certificates \
    python3 python3-pip python3-venv python3-dev \
    build-essential libssl-dev libffi-dev \
    default-libmysqlclient-dev pkg-config \
    libxml2-dev libxslt1-dev \
    sox libsox-fmt-all \
    nginx cron
```

---

### Step 3 — Install MySQL 8

```bash
apt install -y mysql-server
systemctl enable --now mysql
```

Run the security wizard. When prompted, set a root password and answer **Y** to all questions:

```bash
mysql_secure_installation
```

Now create the IVR database and a dedicated user. Open a MySQL shell:

```bash
mysql -u root -p
```

Inside the shell, run (replace `your_db_password` with a strong password you choose):

```sql
CREATE DATABASE ivr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ivr_user'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON ivr.* TO 'ivr_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> Write down `your_db_password` — you will need it in Step 10.

---

### Step 4 — Install Redis

```bash
apt install -y redis-server
```

Bind Redis to localhost only and enable it:

```bash
sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf
sed -i 's/^supervised .*/supervised systemd/' /etc/redis/redis.conf
systemctl enable --now redis-server
```

Test it:

```bash
redis-cli ping
# Expected: PONG
```

---

### Step 5 — Install Asterisk

Ubuntu 22/24 package repositories contain Asterisk 20. Install it directly:

```bash
apt install -y asterisk
systemctl enable asterisk
```

Verify the version:

```bash
asterisk -V
# Expected: Asterisk 20.x.x or similar
```

> If your Ubuntu version only provides Asterisk 18, that also works. Asterisk 20 is preferred but not strictly required.

---

### Step 6 — Install Node.js

The Vue dashboard requires Node.js 20 LTS:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
node --version   # should be v20.x.x
npm --version
```

---

### Step 7 — Clone the repository

```bash
cd /root
git clone https://github.com/Vinald/ivr-demo.git ivr
cd /root/ivr
```

Your project is now at `/root/ivr`.

---

### Step 8 — Create a Python virtual environment

```bash
cd /root/ivr
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

> To avoid having to run `source venv/bin/activate` every time, add it to your shell profile:
> ```bash
> echo "source /root/ivr/venv/bin/activate" >> ~/.bashrc
> source ~/.bashrc
> ```

---

### Step 9 — Install Python dependencies

With the venv active:

```bash
pip install -r /root/ivr/requirements.txt
```

This installs Flask, Gunicorn, SQLAlchemy, Alembic, Asterisk libraries, marshmallow, and all other dependencies listed in `requirements.txt`.

---

### Step 10 — Create and edit config.json

Copy the example config:

```bash
cp /root/ivr/config.dev.json /root/ivr/config.json
```

Open it for editing:

```bash
nano /root/ivr/config.json
```

**Fill in every value below. Do not leave any as the placeholder.**

```json
{
  "core": {
    "log-level": "info",
    "log-vxml": "false",
    "audio-path": "/var/lib/asterisk/sounds/ivr",
    "dates-audio-path": "https://idi-audio.s3-us-west-2.amazonaws.com/academy-ivr/dates",
    "max-channels": "10",
    "use-sip-trunks": "false",
    "max-call-time-in-seconds": "300",
    "secret-key": "REPLACE_THIS_WITH_A_RANDOM_64_CHAR_STRING"
  },
  "database": {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "ivr_user",
    "pass": "your_db_password",
    "database": "ivr"
  },
  "redis": {
    "host": "127.0.0.1",
    "port": "6379"
  },
  "asterisk-ami": {
    "host": "127.0.0.1",
    "port": "5038",
    "user": "ivr",
    "pass": "REPLACE_WITH_STRONG_AMI_PASSWORD"
  },
  "asterisk-ari": {
    "host": "127.0.0.1",
    "port": "8088",
    "user": "ivr",
    "pass": "REPLACE_WITH_STRONG_ARI_PASSWORD"
  },
  "email-server": {
    "host": "smtp.office365.com",
    "port": "587",
    "user": "your_email@example.com",
    "pass": "your_email_password"
  },
  "sip-trunks": [],
  "routed-numbers": [],
  "email-recipients": {
    "to": "",
    "cc": ""
  },
  "roles": [
    {"value": "admin", "text": "Administrator"},
    {"value": "user",  "text": "Normal User"}
  ]
}
```

**Generate the `secret-key`** — copy the output and paste it into the `secret-key` field:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Create the audio directory:

```bash
mkdir -p /var/lib/asterisk/sounds/ivr
chown asterisk:asterisk /var/lib/asterisk/sounds/ivr
```

Set permissions on the project directory so the API can write logs:

```bash
chown -R root:asterisk /root/ivr
chmod -R 775 /root/ivr
mkdir -p /root/ivr/logs
```

---

### Step 11 — Run database migrations

With the venv active, run Alembic to create all tables:

```bash
cd /root/ivr
source venv/bin/activate
alembic upgrade head
```

You should see output like:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 430998fabc17, ...
INFO  [alembic.runtime.migration] Running upgrade 430998fabc17 -> bfb81da8b93b, ...
```

Verify the tables exist:

```bash
mysql -u ivr_user -p ivr -e "SHOW TABLES;"
# Expected: apps, cdr, report_types, reports, users
```

---

### Step 12 — Configure Asterisk

Copy the IVR Asterisk configuration files:

```bash
# Back up the originals first
cp /etc/asterisk/sip.conf        /etc/asterisk/sip.conf.orig
cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.orig
cp /etc/asterisk/manager.conf    /etc/asterisk/manager.conf.orig

# Copy the IVR configs
cp /root/ivr/asterisk/sip.conf        /etc/asterisk/sip.conf
cp /root/ivr/asterisk/extensions.conf /etc/asterisk/extensions.conf
cp /root/ivr/asterisk/manager.conf    /etc/asterisk/manager.conf
cp /root/ivr/asterisk/ari.conf        /etc/asterisk/ari.conf
cp /root/ivr/asterisk/http.conf       /etc/asterisk/http.conf
cp /root/ivr/asterisk/cdr.conf        /etc/asterisk/cdr.conf
```

Set the AMI password in `manager.conf` to match the `asterisk-ami.pass` you put in `config.json`:

```bash
# Replace YOUR_AMI_PASSWORD with the value from config.json
sed -i 's/^secret=.*/secret=YOUR_AMI_PASSWORD/' /etc/asterisk/manager.conf
```

Set the ARI password in `ari.conf` to match the `asterisk-ari.pass` you put in `config.json`:

```bash
# Replace YOUR_ARI_PASSWORD with the value from config.json
sed -i 's/^password = .*/password = YOUR_ARI_PASSWORD/' /etc/asterisk/ari.conf
```

Point `extensions.conf` at the actual `agi.py` path with the venv Python:

```bash
sed -i 's|AGI(.*agi.py)|AGI(/root/ivr/venv/bin/python3 /root/ivr/agi.py)|' \
    /etc/asterisk/extensions.conf
```

Verify the AGI line looks correct:

```bash
grep AGI /etc/asterisk/extensions.conf
# Should show: same = n,AGI(/root/ivr/venv/bin/python3 /root/ivr/agi.py)
```

Set ownership and restart Asterisk:

```bash
chown -R asterisk:asterisk /etc/asterisk
systemctl restart asterisk
systemctl status asterisk
```

Confirm Asterisk started cleanly:

```bash
asterisk -rx "core show version"
# Expected: Asterisk 20.x.x ...
```

---

### Step 13 — Create the first admin user

The database starts empty. Create an admin user directly in MySQL:

```bash
mysql -u ivr_user -p ivr
```

Inside the MySQL shell (replace the email and password hash — generate the hash with the Python command below):

```bash
# First, generate a bcrypt hash for your chosen password
python3 -c "
import bcrypt
pw = b'YourChosenPassword'
print(bcrypt.hashpw(pw, bcrypt.gensalt()).decode())
"
```

Then in the MySQL shell:

```sql
INSERT INTO users (email, password, role, creation_date)
VALUES (
  'admin@example.com',
  'PASTE_THE_BCRYPT_HASH_HERE',
  'admin',
  NOW()
);
EXIT;
```

> Use this email and password to log in to the dashboard in Step 18. Change the password after first login via the Profile page.

---

### Step 14 — Set up the IVR API as a systemd service

Create the service file:

```bash
cat > /etc/systemd/system/ivr-api.service << 'EOF'
[Unit]
Description=Academy IVR API Service
After=network.target mysql.service redis.service

[Service]
WorkingDirectory=/root/ivr
ExecStart=/root/ivr/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
Restart=on-failure
RestartSec=5
Environment=FRONTEND_ORIGIN=http://YOUR_SERVER_IP:8000

[Install]
WantedBy=multi-user.target
EOF
```

Replace `YOUR_SERVER_IP` with your actual server IP address:

```bash
# Find your server IP
ip a | grep 'inet ' | grep -v '127.0.0.1'

# Then replace it in the service file
sed -i 's/YOUR_SERVER_IP/THE_IP_YOU_FOUND/' /etc/systemd/system/ivr-api.service
```

Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable --now ivr-api
systemctl status ivr-api
```

Test it:

```bash
curl http://localhost:5000/health
# Expected: {"status":"ok"}
```

---

### Step 15 — Set up the Asterisk events listener as a systemd service

```bash
cat > /etc/systemd/system/ivr-events.service << 'EOF'
[Unit]
Description=Academy IVR Asterisk Events Listener
After=network.target asterisk.service ivr-api.service

[Service]
WorkingDirectory=/root/ivr/bin
ExecStart=/root/ivr/venv/bin/python3 asterisk-events-listener.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

```bash
systemctl daemon-reload
systemctl enable --now ivr-events
systemctl status ivr-events
```

---

### Step 16 — Set up cron jobs

The IVR uses three cron jobs:

| Job | Script | Schedule | Purpose |
|---|---|---|---|
| Call queue | `call-request-queue.py` | Every 3 min | Dispatches queued calls when channels are free |
| SIP peer monitor | `sip-peer-monitor.py` | Every 50 min | Checks SIP trunk availability |
| Log rotation | `log-rotation.py` | Daily at 23:59 | Rotates and compresses application logs |

Create the cron file:

```bash
cat > /etc/cron.d/ivr-system-cron << 'EOF'
*/3  * * * * root cd /root/ivr/bin && /root/ivr/venv/bin/python3 call-request-queue.py >> /root/ivr/logs/queue.log 2>&1
*/50 * * * * root cd /root/ivr/bin && /root/ivr/venv/bin/python3 sip-peer-monitor.py >> /root/ivr/logs/monitor.log 2>&1
59   23 * * * root cd /root/ivr/bin && /root/ivr/venv/bin/python3 log-rotation.py >> /root/ivr/logs/rotation.log 2>&1
EOF

chown root:root /etc/cron.d/ivr-system-cron
chmod 600 /etc/cron.d/ivr-system-cron
systemctl restart cron
```

---

### Step 17 — Build and serve the Vue dashboard with nginx

**Set the API URL for the frontend:**

```bash
SERVER_IP=$(hostname -I | awk '{print $1}')

cat > /root/ivr/web/.env << EOF
VUE_APP_ROOT_API=http://${SERVER_IP}:5000/api
EOF
```

**Install Node dependencies and build:**

```bash
cd /root/ivr/web
npm install
npm run build
```

This produces a `dist/` folder with the compiled dashboard.

**Move the build to the nginx web root:**

```bash
mkdir -p /var/www/html/ivr-web-app
rm -rf /var/www/html/ivr-web-app/*
cp -r /root/ivr/web/dist/. /var/www/html/ivr-web-app/
chown -R www-data:www-data /var/www/html/ivr-web-app
chmod -R 755 /var/www/html/ivr-web-app
```

**Create the nginx site config:**

```bash
cat > /etc/nginx/sites-available/ivr-web-app << 'EOF'
server {
    listen 8000;
    server_name _;

    root /var/www/html/ivr-web-app;
    index index.html;

    # Vue Router — serve index.html for all routes so the SPA handles them
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|ico|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF
```

**Enable the site and reload nginx:**

```bash
ln -sf /etc/nginx/sites-available/ivr-web-app /etc/nginx/sites-enabled/
nginx -t   # must say "syntax is ok"
systemctl reload nginx
```

The dashboard is now at `http://YOUR_SERVER_IP:8000`.

---

### Step 18 — Verify everything is running

**Check all services:**

```bash
systemctl status mysql redis-server asterisk ivr-api ivr-events nginx
```

All should show `active (running)`.

**Check all ports are listening:**

```bash
ss -tlnp | grep -E '3306|6379|5000|5038|8088|5060|8000'
```

Expected output:

```
LISTEN  0.0.0.0:3306   mysql
LISTEN  127.0.0.1:6379 redis
LISTEN  0.0.0.0:5000   gunicorn (ivr-api)
LISTEN  0.0.0.0:5038   asterisk (AMI)
LISTEN  0.0.0.0:8088   asterisk (ARI/HTTP)
LISTEN  0.0.0.0:5060   asterisk (SIP)
LISTEN  0.0.0.0:8000   nginx (dashboard)
```

**Test the API health endpoint:**

```bash
curl http://localhost:5000/health
# {"status": "ok"}
```

**Test a login:**

```bash
curl -s -X POST http://localhost:5000/api/login \
  -d "username=admin@example.com" \
  -d "password=YourChosenPassword" | python3 -m json.tool
# Should return a JWT token and user details
```

**Open the dashboard:**

Navigate to `http://YOUR_SERVER_IP:8000` in a browser and log in with the admin credentials you created in Step 13.

---

## SIP Phone Setup

Connect a SIP phone (hardware or softphone like [Zoiper](https://www.zoiper.com/en/voip-softphone/download/current) or [Linphone](https://www.linphone.org/)) with these settings:

| Setting | Value |
|---|---|
| SIP Server | Your server IP (`ip a` to find it) |
| Port | `5060` |
| Username / Auth name | `200` |
| Password | `1234` |

> **Before going live:** change the SIP extension password by editing `/etc/asterisk/sip.conf` and running `asterisk -rx "sip reload"`.

To make a test call, dial any number from the registered softphone. Asterisk will answer it, run `agi.py`, and you will hear whatever the VXML app at the configured `voice_url` returns.

---

## Updating the Application

When you pull new code, run these steps to apply the update:

```bash
cd /root/ivr
git pull origin main

# Apply any new database migrations
source venv/bin/activate
alembic upgrade head

# Install any new Python dependencies
pip install -r requirements.txt

# Restart the API
systemctl restart ivr-api
systemctl restart ivr-events

# If you changed frontend code, rebuild and redeploy
cd /root/ivr/web
npm install
npm run build
rm -rf /var/www/html/ivr-web-app/*
cp -r dist/. /var/www/html/ivr-web-app/
chown -R www-data:www-data /var/www/html/ivr-web-app
```

---

## Environment Variables Reference

Set these in the systemd service file (`Environment=`) or your shell.

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_ORIGIN` | `http://localhost:8080` | Allowed CORS origin — must match the URL you use to access the dashboard in the browser |

The `secret-key` in `config.json` must be a strong random value. Regenerate it at any time with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> Changing the secret-key invalidates all existing JWT tokens (all users will be logged out).

---

## Running the Test Suite

```bash
cd /root/ivr
source venv/bin/activate
pytest
```

Run a single file verbosely:

```bash
pytest tests/test_cdr_manager.py -v
```

---

## Pre-commit Hooks

This repository uses [pre-commit](https://pre-commit.com) with [detect-secrets](https://github.com/Yelp/detect-secrets) to block accidental credential commits before they reach GitHub.

**Install once after cloning:**

```bash
pip install pre-commit detect-secrets
pre-commit install
```

After that, every `git commit` will:
- Scan staged files for secrets and block if any are found
- Prevent direct commits to `main` or `master`
- Check Python syntax, YAML/JSON validity, trailing whitespace

**If detect-secrets flags a false positive:**

```bash
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
git add .secrets.baseline && git commit -m "chore: update secrets baseline"
```

> **Never commit `config.json`** — it contains your real credentials. The `.gitignore` blocks it. Only `config.dev.json` (placeholder values) is tracked.

---

## Code Style

PEP 8 with a max line length of 120.

```bash
# Check
flake8 --max-line-length=120 ./run.py ./agi.py ./app

# Auto-fix
autopep8 --in-place --aggressive --aggressive ./run.py
```

---

## Docker Alternative

If you prefer containers, `docker-compose.yml` sets up MySQL, Redis, and the web app automatically. You still need Asterisk installed on the host (Asterisk cannot run inside a container and reach SIP phones on the local network without host networking).

```bash
cp .env.example .env
nano .env   # fill in MYSQL_ROOT_PASSWORD, FRONTEND_ORIGIN, VUE_APP_API_URL

apt install -y docker.io docker-compose
docker-compose up -d --build
```

| Service | URL |
|---|---|
| IVR API | `http://your-ip:5000` |
| Web Dashboard | `http://your-ip:8000` |

---

## Troubleshooting

**`systemctl status ivr-api` shows a failure**

```bash
journalctl -u ivr-api -n 50 --no-pager
```

Common causes: `config.json` missing, wrong database password, Redis not running, empty `secret-key`.

**API returns 500 on login**

Check the application log:

```bash
tail -f /root/ivr/logs/app.log
```

**Asterisk won't start**

```bash
journalctl -u asterisk -n 50 --no-pager
asterisk -cvvv           # run in foreground to see all errors
```

**Asterisk starts but AMI connection fails**

AMI connects in a background thread so the API starts regardless. Check the log:

```bash
grep -i ami /root/ivr/logs/app.log | tail -20
```

The most common cause is the AMI password in `manager.conf` not matching `asterisk-ami.pass` in `config.json`.

**AGI script fails on calls**

```bash
tail -f /var/log/asterisk/full | grep -i agi
```

Make sure the extensions.conf AGI line points to the venv Python:

```bash
grep AGI /etc/asterisk/extensions.conf
# Must be: AGI(/root/ivr/venv/bin/python3 /root/ivr/agi.py)
```

**Dashboard blank or shows "Network Error"**

Check the `VUE_APP_ROOT_API` URL in `/root/ivr/web/.env` matches your actual server IP. Rebuild and redeploy if you change it:

```bash
cd /root/ivr/web && npm run build
cp -r dist/. /var/www/html/ivr-web-app/
```

**CORS errors in the browser console**

`FRONTEND_ORIGIN` in the `ivr-api.service` must exactly match the URL in your browser's address bar (including the port). After changing it:

```bash
systemctl daemon-reload && systemctl restart ivr-api
```

**Permission errors writing logs**

```bash
chown -R root:asterisk /root/ivr
chmod -R 775 /root/ivr/logs
```

**MySQL "Access denied"**

```bash
mysql -u ivr_user -p ivr -e "SELECT 1;"
```

If this fails, the password in `config.json` doesn't match what you set in Step 3. Reset it:

```bash
mysql -u root -p
ALTER USER 'ivr_user'@'localhost' IDENTIFIED BY 'your_new_password';
FLUSH PRIVILEGES;
EXIT;
```

---

## References

| Component | Docs |
|---|---|
| Asterisk ARI | https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=29395573 |
| Asterisk AMI | https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=4817239 |
| Asterisk AGI | https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589 |
| Flask | https://flask.palletsprojects.com |
| SQLAlchemy | https://docs.sqlalchemy.org |
| Alembic | https://alembic.sqlalchemy.org |
| marshmallow | https://marshmallow.readthedocs.io |
| Redis | https://redis.io/documentation |
| BeautifulSoup4 | https://www.crummy.com/software/BeautifulSoup/bs4/doc |
| Gunicorn | https://docs.gunicorn.org |
| nginx | https://nginx.org/en/docs |
