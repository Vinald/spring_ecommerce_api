# Academy IVR

Academy IVR is an in-house Interactive Voice Response (IVR) system built for the **Call for Life** project. It handles outbound call campaigns, VXML-driven call flows, scheduled reporting, and a Vue.js web dashboard for monitoring and management.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Bare Ubuntu VM Setup (No Docker)](#bare-ubuntu-vm-setup-no-docker)
  - [1. System packages](#1-system-packages)
  - [2. MySQL 8.0](#2-mysql-80)
  - [3. Redis](#3-redis)
  - [4. Asterisk 20](#4-asterisk-20)
  - [5. Node.js and npm](#5-nodejs-and-npm)
  - [6. Clone the repository](#6-clone-the-repository)
  - [7. Python dependencies](#7-python-dependencies)
  - [8. Configure the application](#8-configure-the-application)
  - [9. Run Alembic database migrations](#9-run-alembic-database-migrations)
  - [10. Configure Asterisk](#10-configure-asterisk)
  - [11. Start the Flask API](#11-start-the-flask-api)
  - [12. Start the Asterisk events listener](#12-start-the-asterisk-events-listener)
  - [13. Configure the call queue cron job](#13-configure-the-call-queue-cron-job)
  - [14. Start the Vue.js web dashboard](#14-start-the-vuejs-web-dashboard)
  - [15. Run as systemd services (production)](#15-run-as-systemd-services-production)
  - [16. Verify everything is running](#16-verify-everything-is-running)
- [SIP Phone Configuration](#sip-phone-configuration)
- [Docker Setup (Alternative)](#docker-setup-alternative)
- [Environment Variables Reference](#environment-variables-reference)
- [Running the Test Suite](#running-the-test-suite)
- [Code Style](#code-style)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Architecture Overview

```
External App ──► /call.initiate ──► Flask API (port 5000)
                                         │
                              ┌──────────┼──────────┐
                         Asterisk AMI  Redis     MySQL 8
                         (port 5038)  (port 6379) (port 3306)
                              │
                         Asterisk AGI ──► agi.py ──► VXML Parser
                              │
                         Asterisk ARI ──► Event Handler ──► CDR
```

| Component | Technology | Port |
|---|---|---|
| REST API | Python / Flask + Gunicorn | 5000 |
| Web Dashboard | Vue 3 / Node.js | 8080 |
| Telephony engine | Asterisk 20 | 5038 (AMI), 8088 (ARI), 5060 (SIP) |
| Database | MySQL 8.0 | 3306 |
| Cache / Queue | Redis 7 | 6379 |

---

## Prerequisites

**Hardware (minimum)**

| CPU | RAM | Disk |
|---|---|---|
| 2 cores | 2 GB | 20 GB |

**Operating system:** Ubuntu 22.04 LTS or 24.04 LTS (fresh install recommended)

**Network:** A working internet connection is required during installation.

**SIP Phone:** A softphone such as [Zoiper](https://www.zoiper.com/en/voip-softphone/download/current) or a physical SIP phone (Fanvil, Grandstream, Yealink).

---

## Bare Ubuntu VM Setup (No Docker)

All commands below are run as **root** or with `sudo` unless noted. The instructions assume you are installing to `/root/ivr`. Adjust paths if you use a different directory.

---

### 1. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    git curl wget gnupg2 lsb-release ca-certificates \
    python3 python3-pip python3-venv \
    build-essential libssl-dev libffi-dev python3-dev \
    libmysqlclient-dev pkg-config \
    lxml libxml2-dev libxslt1-dev \
    sox libsox-fmt-all \
    cron
```

---

### 2. MySQL 8.0

```bash
sudo apt install -y mysql-server
sudo systemctl enable --now mysql
```

Secure the installation and create the IVR database user:

```bash
sudo mysql_secure_installation
```

Then open a MySQL shell and run:

```sql
CREATE DATABASE ivr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ivr_user'@'localhost' IDENTIFIED BY 'choose_a_strong_password';
GRANT ALL PRIVILEGES ON ivr.* TO 'ivr_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> **Note:** Use the username and password you create here in `config.json` (step 8).

---

### 3. Redis

```bash
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

Verify Redis is running:

```bash
redis-cli ping
# Expected output: PONG
```

---

### 4. Asterisk 20

Asterisk must be compiled from source on Ubuntu 22/24 to get version 20.

```bash
cd /tmp
sudo apt install -y \
    subversion libjansson-dev libxml2-dev libncurses5-dev \
    libsqlite3-dev uuid-dev libiksemel-dev libedit-dev \
    libspandsp-dev libsrtp2-dev

# Download Asterisk 20 LTS
wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz
tar xzf asterisk-20-current.tar.gz
cd asterisk-20*/

# Install prerequisites
sudo contrib/scripts/install_prereq install

# Configure and compile
sudo ./configure --with-jansson-bundled
sudo make menuselect  # Enable: res_ari, res_http_websocket, chan_sip, app_agi, cdr_csv
sudo make -j$(nproc)
sudo make install
sudo make samples      # installs sample config files to /etc/asterisk/
sudo make config       # installs init scripts
sudo ldconfig

# Create the asterisk user/group
sudo groupadd -r asterisk 2>/dev/null || true
sudo useradd -r -g asterisk -d /var/lib/asterisk -s /sbin/nologin asterisk 2>/dev/null || true

sudo systemctl enable asterisk
```

---

### 5. Node.js and npm

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # should be v20.x
npm --version
```

---

### 6. Clone the repository

```bash
cd /root
git clone https://github.com/Vinald/ivr-demo.git ivr
cd ivr
```

---

### 7. Python dependencies

Create a virtual environment and install all dependencies:

```bash
python3 -m venv /root/ivr/venv
source /root/ivr/venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

> **Tip:** Add `source /root/ivr/venv/bin/activate` to your `~/.bashrc` so the venv activates automatically on login.

---

### 8. Configure the application

Copy the example config and edit it with your values:

```bash
cd /root/ivr
cp config.dev.json config.json
nano config.json
```

Key fields to update in `config.json`:

```json
{
  "core": {
    "secret-key": "replace_with_a_long_random_string_at_least_32_chars",
    "log-level": "info",
    "audio-path": "/var/lib/asterisk/sounds/ivr",
    "max-channels": "10",
    "use-sip-trunks": "false"
  },
  "database": {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "ivr_user",
    "pass": "the_password_you_set_in_step_2",
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
    "pass": "choose_a_strong_ami_password"
  },
  "asterisk-ari": {
    "host": "127.0.0.1",
    "port": "8088",
    "user": "ivr",
    "pass": "choose_a_strong_ari_password"
  },
  "email-server": {
    "host": "smtp.office365.com",
    "port": "587",
    "user": "your_email@example.com",
    "pass": "your_email_password"
  }
}
```

Create the audio directory:

```bash
sudo mkdir -p /var/lib/asterisk/sounds/ivr
sudo chown asterisk:asterisk /var/lib/asterisk/sounds/ivr
```

Fix project directory permissions so the API can write logs:

```bash
sudo chown -R $USER:asterisk /root/ivr
sudo chmod -R 775 /root/ivr
```

---

### 9. Run Alembic database migrations

With the venv active:

```bash
cd /root/ivr
source venv/bin/activate
alembic upgrade head
```

This creates all required tables (`users`, `apps`, `cdr`, `reports`, `report_types`) in the `ivr` database.

---

### 10. Configure Asterisk

Copy the IVR Asterisk config files to `/etc/asterisk/`:

```bash
# Backup originals
sudo cp /etc/asterisk/sip.conf /etc/asterisk/sip.conf.bak
sudo cp /etc/asterisk/extensions.conf /etc/asterisk/extensions.conf.bak
sudo cp /etc/asterisk/manager.conf /etc/asterisk/manager.conf.bak

# Copy IVR configs
sudo cp /root/ivr/asterisk/sip.conf        /etc/asterisk/sip.conf
sudo cp /root/ivr/asterisk/extensions.conf /etc/asterisk/extensions.conf
sudo cp /root/ivr/asterisk/manager.conf    /etc/asterisk/manager.conf
sudo cp /root/ivr/asterisk/ari.conf        /etc/asterisk/ari.conf
sudo cp /root/ivr/asterisk/http.conf       /etc/asterisk/http.conf
sudo cp /root/ivr/asterisk/cdr.conf        /etc/asterisk/cdr.conf
```

Update the AMI and ARI passwords in the copied config files to match what you set in `config.json`:

```bash
# Update AMI password (manager.conf)
sudo sed -i 's/^secret=.*/secret=choose_a_strong_ami_password/' /etc/asterisk/manager.conf

# Update ARI password (ari.conf)
sudo sed -i 's/^password = .*/password = choose_a_strong_ari_password/' /etc/asterisk/ari.conf
```

Update `extensions.conf` to point to the correct path of `agi.py`:

```bash
sudo sed -i 's|AGI(/root/ivr/agi.py)|AGI(/root/ivr/venv/bin/python3 /root/ivr/agi.py)|' \
    /etc/asterisk/extensions.conf
```

Set correct ownership and restart Asterisk:

```bash
sudo chown -R asterisk:asterisk /etc/asterisk
sudo systemctl restart asterisk
sudo systemctl status asterisk
```

Verify Asterisk is up and the AMI is listening:

```bash
sudo asterisk -rvvv
# Inside the Asterisk CLI:
# core show channels
# manager show connected
# quit
```

---

### 11. Start the Flask API

For development (single process, auto-reload):

```bash
cd /root/ivr
source venv/bin/activate
export FRONTEND_ORIGIN=http://$(hostname -I | awk '{print $1}'):8080
python3 run.py
```

The API will be available at `http://<your-server-ip>:5000`.

For production (Gunicorn with multiple workers):

```bash
cd /root/ivr
source venv/bin/activate
export FRONTEND_ORIGIN=http://$(hostname -I | awk '{print $1}'):8080
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
```

---

### 12. Start the Asterisk events listener

The events listener forwards AMI events (call originate responses, hangups) to the Flask API. Run it in a separate terminal or as a service (see step 15):

```bash
cd /root/ivr/bin
source /root/ivr/venv/bin/activate
python3 asterisk-events-listener.py
```

---

### 13. Configure the call queue cron job

The call queue processor drains queued calls when Asterisk has free channels. Add it to cron to run every minute:

```bash
crontab -e
```

Add this line:

```
* * * * * cd /root/ivr/bin && /root/ivr/venv/bin/python3 call-request-queue.py >> /root/ivr/logs/queue.log 2>&1
```

---

### 14. Start the Vue.js web dashboard

Install Node dependencies (first time only):

```bash
cd /root/ivr/web
npm install
```

Set the API URL to point to your server:

```bash
# Replace the IP with your actual server IP
echo "VUE_APP_API_URL=http://$(hostname -I | awk '{print $1}'):5000" > .env.development
```

Start the development server:

```bash
npm run serve
```

The dashboard will be available at `http://<your-server-ip>:8080`.

For a production build served by a web server (nginx/apache):

```bash
npm run build
# Output goes to /root/ivr/web/dist — serve this directory with nginx or apache
```

---

### 15. Run as systemd services (production)

This keeps all processes running across reboots and restarts them on failure.

**IVR API service:**

```bash
sudo cp /root/ivr/bin/ivr-api.service /etc/systemd/system/ivr-api.service

# Edit the service file to use the virtualenv
sudo sed -i 's|ExecStart=.*|ExecStart=/root/ivr/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app|' \
    /etc/systemd/system/ivr-api.service

# Add the FRONTEND_ORIGIN env var — replace IP with your actual server IP
sudo sed -i '/\[Service\]/a Environment=FRONTEND_ORIGIN=http://YOUR_SERVER_IP:8080' \
    /etc/systemd/system/ivr-api.service

sudo systemctl daemon-reload
sudo systemctl enable --now ivr-api
sudo systemctl status ivr-api
```

**Asterisk events listener service:**

```bash
sudo cp /root/ivr/bin/asterisk-events-listener.service /etc/systemd/system/ivr-events.service

# Edit to use the virtualenv
sudo sed -i 's|ExecStart=.*|ExecStart=/root/ivr/venv/bin/python3 asterisk-events-listener.py|' \
    /etc/systemd/system/ivr-events.service

sudo systemctl daemon-reload
sudo systemctl enable --now ivr-events
sudo systemctl status ivr-events
```

Check logs for either service:

```bash
sudo journalctl -u ivr-api -f
sudo journalctl -u ivr-events -f
```

---

### 16. Verify everything is running

```bash
# Services
sudo systemctl status mysql redis-server asterisk ivr-api ivr-events

# Ports
ss -tlnp | grep -E '3306|6379|5038|8088|5000|5060'

# API health check
curl http://localhost:5000/health
# Expected: {"status": "ok"}

# Asterisk AMI
sudo asterisk -rvvv -x "core show version"
```

Open a browser and navigate to `http://<your-server-ip>:8080` to access the web dashboard.

Default admin credentials are created by the first Alembic migration. Check the migration file in `alembic/versions/` for the default username and password, and **change them immediately after first login**.

---

## SIP Phone Configuration

Configure any SIP softphone (Zoiper, Linphone) or hardware phone with these settings:

| Setting | Value |
|---|---|
| Username / Auth name | `200` |
| Password | `1234` *(change this in `/etc/asterisk/sip.conf` before production use)* |
| SIP Server / Host | Your server IP address (run `ip a` to find it) |
| Port | `5060` |

To find your server IP:

```bash
ip a | grep 'inet ' | grep -v '127.0.0.1'
```

---

## Docker Setup (Alternative)

If you prefer Docker, the `docker-compose.yml` in the repository sets up all services automatically.

```bash
git clone https://github.com/Vinald/ivr-demo.git ivr
cd ivr

# Copy and edit the env file
cp .env.example .env
nano .env   # set MYSQL_ROOT_PASSWORD, FRONTEND_ORIGIN, VUE_APP_API_URL

sudo apt update && sudo apt install -y docker.io docker-compose
sudo docker-compose up -d --build
```

| Service | URL |
|---|---|
| IVR API | `http://your-ip:5000` |
| Web Dashboard | `http://your-ip:8000` |

Daily commands:

```bash
docker-compose stop    # stop containers
docker-compose start   # resume containers
docker-compose logs -f # follow logs
```

---

## Environment Variables Reference

These can be set in your shell, in a `.env` file, or in the systemd service `Environment=` line.

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_ORIGIN` | `http://localhost:8080` | CORS allowed origin for the Vue dashboard |
| `MYSQL_ROOT_PASSWORD` | *(none)* | MySQL root password used by docker-compose |
| `VUE_APP_API_URL` | `http://localhost:5000` | API base URL used by the Vue frontend |

The `secret-key` in `config.json` must also be set to a strong random value before starting the API in any environment:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Paste the output into config.json under "core" > "secret-key"
```

---

## Running the Test Suite

```bash
cd /root/ivr
source venv/bin/activate
pytest
```

To run a specific test file:

```bash
pytest tests/test_cdr_manager.py -v
```

---

## Pre-commit Hooks (Secret Detection)

This repository uses [pre-commit](https://pre-commit.com) with [detect-secrets](https://github.com/Yelp/detect-secrets) to block accidental credential commits before they leave your machine.

**Install once after cloning:**

```bash
pip install pre-commit detect-secrets
pre-commit install
```

After that, every `git commit` will automatically:
- Scan staged files for secrets and block the commit if any are found
- Prevent direct commits to `main` or `master`
- Check Python syntax, YAML/JSON validity, and trailing whitespace

**If detect-secrets flags a false positive** (e.g. a test fixture or example value):

```bash
# Review what was flagged
detect-secrets scan > .secrets.baseline

# Audit each finding and mark safe ones as approved
detect-secrets audit .secrets.baseline

# Then commit the updated baseline
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

> **Never commit `config.json`** — it contains your real database password and JWT secret key. Only `config.dev.json` (with placeholder values) is tracked. The `.gitignore` blocks `config.json` by default.

---

## Code Style

This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) with a max line length of 120.

Check for style errors before pushing:

```bash
flake8 --max-line-length=120 --statistics ./run.py ./agi.py ./app
```

Auto-fix style errors:

```bash
autopep8 --in-place --aggressive --aggressive <filename_or_directory>
```

---

## Troubleshooting

**Asterisk won't start**
```bash
sudo journalctl -u asterisk -n 50
sudo asterisk -cvvv   # start in console mode to see errors
```

**API fails to connect to MySQL**
```bash
mysql -u ivr_user -p ivr -e "SELECT 1;"   # test credentials directly
# Also check: sudo systemctl status mysql
```

**API fails to connect to Redis**
```bash
redis-cli ping   # should return PONG
# Check: sudo systemctl status redis-server
```

**API starts but AMI connection fails**

AMI connects in a background thread — the API starts normally even if Asterisk is down. Check the log:

```bash
tail -f /root/ivr/logs/app.log | grep AMI
```

**AGI script not found by Asterisk**

Make sure `extensions.conf` references the correct Python path:

```bash
grep AGI /etc/asterisk/extensions.conf
# Should show: AGI(/root/ivr/venv/bin/python3 /root/ivr/agi.py)
sudo asterisk -rx "dialplan reload"
```

**Vue dashboard shows CORS errors**

Make sure `FRONTEND_ORIGIN` matches the exact URL (including port) you use to access the dashboard in your browser, and restart the API after changing it.

**Permission errors writing logs**

```bash
sudo chown -R $USER:asterisk /root/ivr
sudo chmod -R 775 /root/ivr/logs
```

---

## References

| Interface | Description | Reference |
|---|---|---|
| Asterisk ARI | Get SIP peer info, active channels | [ARI Docs](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=29395573) |
| Asterisk AMI | Initiate calls, receive call events | [AMI Docs](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=4817239) |
| Asterisk AGI | Manipulate call flow after VXML parsing | [AGI Docs](https://wiki.asterisk.org/wiki/pages/viewpage.action?pageId=32375589) |
| Flask | Python web framework for the REST API | [Flask Docs](https://flask.palletsprojects.com/) |
| Beautiful Soup | VXML parser | [BS4 Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) |
| SQLAlchemy | ORM for all database operations | [SQLAlchemy Docs](https://docs.sqlalchemy.org/) |
| Redis | In-memory cache and call queue | [Redis Docs](https://redis.io/documentation) |
| marshmallow | Request input validation | [marshmallow Docs](https://marshmallow.readthedocs.io/) |
| Alembic | Database schema migrations | [Alembic Docs](https://alembic.sqlalchemy.org/) |
| Flake8 | Python code style linter | [Flake8 Docs](http://flake8.pycqa.org/en/latest/) |
| Autopep8 | Auto code style fixer | [Autopep8 Docs](https://pypi.org/project/autopep8/) |
