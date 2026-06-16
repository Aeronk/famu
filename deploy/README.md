# Deploying Murimi OS to a Contabo Apache server (no Docker)

Production runs FastAPI under **Gunicorn (uvicorn workers)**, fronted by **Apache**
(`mod_proxy`), with **Celery** worker + beat as systemd services and
**PostgreSQL + pgvector** as the database.

## 1. Server prerequisites (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv git apache2 redis-server \
                    postgresql postgresql-contrib build-essential

# pgvector (Postgres 16 example)
sudo apt install -y postgresql-16-pgvector

sudo a2enmod proxy proxy_http headers ssl rewrite
```

Create the database:

```bash
sudo -u postgres psql -c "CREATE USER murimi WITH PASSWORD 'strong-password';"
sudo -u postgres psql -c "CREATE DATABASE murimi OWNER murimi;"
```

## 2. Application setup

```bash
sudo mkdir -p /opt/murimi && sudo chown $USER /opt/murimi
cd /opt/murimi
git clone <your-repo-url> farm_manager_api
cd farm_manager_api

python3.11 -m venv .venv
./.venv/bin/pip install --upgrade pip wheel setuptools
./.venv/bin/pip install -r requirements.txt

cp .env.example .env       # then edit:
#   DATABASE_URL=postgresql+asyncpg://murimi:strong-password@localhost:5432/murimi
#   SECRET_KEY=<random>     (python -c "import secrets;print(secrets.token_urlsafe(48))")
#   add OPENAI/WHATSAPP/WEATHER keys when ready

./.venv/bin/alembic upgrade head
./.venv/bin/python -m scripts.seed     # optional demo data
```

## 3. systemd services

```bash
sudo useradd -r -s /usr/sbin/nologin murimi || true
sudo chown -R murimi:www-data /opt/murimi

sudo cp deploy/murimi-api.service    /etc/systemd/system/
sudo cp deploy/murimi-worker.service /etc/systemd/system/
sudo cp deploy/murimi-beat.service   /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now murimi-api murimi-worker murimi-beat
```

## 4. Apache reverse proxy

```bash
sudo cp deploy/apache-vhost.conf /etc/apache2/sites-available/murimi-api.conf
# edit ServerName, then:
sudo a2ensite murimi-api
sudo systemctl reload apache2
sudo certbot --apache -d api.yourdomain.com   # HTTPS
```

## 5. WhatsApp webhook

Point your Meta App webhook to `https://api.yourdomain.com/webhooks/whatsapp`
with the verify token from `WHATSAPP_VERIFY_TOKEN`, and map each tenant's
business `phone_number_id` in `tenants.settings.whatsapp_phone_number_id`.

## 6. Continuous deployment

`/.github/workflows/deploy.yml` SSHes in on push to `main`, pulls, installs,
migrates and restarts the services. Set repo secrets: `CONTABO_HOST`,
`CONTABO_USER`, `CONTABO_SSH_KEY`, `CONTABO_APP_DIR` (`/opt/murimi/farm_manager_api`).
Ensure the deploy user may `sudo systemctl restart murimi-*` without a password.
