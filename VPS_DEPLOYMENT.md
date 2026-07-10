# Ubuntu VPS Deployment Plan

**Men and Women of Passion and Purpose** — production deployment on Ubuntu with PostgreSQL, Gunicorn, Nginx, and Let's Encrypt HTTPS.

This document is the end-to-end server runbook. It does not replace `DEPLOYMENT.md` (application-level notes) or `BACKUP_AND_RECOVERY.md` (restore procedures).

---

## Assumptions

| Item | Value |
|------|-------|
| OS | Ubuntu 22.04 LTS or 24.04 LTS |
| Domain | `yourdomain.com` (replace everywhere) |
| App path | `/var/www/mwpp` |
| Linux user | `mwpp` (dedicated service account) |
| Gunicorn bind | `127.0.0.1:8000` (Nginx reverse proxy only) |
| Database | PostgreSQL 14+ on the same VPS |

---

## 1. Server Requirements

### Minimum (low traffic)

| Resource | Specification |
|----------|---------------|
| CPU | 1 vCPU |
| RAM | 2 GB |
| Disk | 25 GB SSD |
| Network | Public IPv4, ports 22 / 80 / 443 open |

### Recommended (production)

| Resource | Specification |
|----------|---------------|
| CPU | 2 vCPUs |
| RAM | 4 GB |
| Disk | 40 GB SSD (room for DB dumps + uploads) |
| Network | Static IP, DNS A/AAAA records for domain and `www` |

### Software versions

| Component | Version |
|-----------|---------|
| Python | 3.11 or 3.12 |
| PostgreSQL | 14+ |
| Nginx | 1.18+ (Ubuntu package) |
| Certbot | Latest from `snap` or Ubuntu repos |
| Git | 2.x |

### DNS (before SSL)

Create records pointing to your VPS public IP:

```
A     yourdomain.com      → <VPS_IP>
A     www.yourdomain.com  → <VPS_IP>
```

Optional: `AAAA` records if using IPv6.

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 2. Installation Commands

Run as a user with `sudo` on a fresh Ubuntu VPS.

### 2.1 System update and base packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip python3-dev \
  build-essential libpq-dev \
  git nginx postgresql postgresql-contrib \
  certbot python3-certbot-nginx \
  ufw fail2ban curl
```

### 2.2 Create service user and directories

```bash
sudo adduser --system --group --home /var/www/mwpp mwpp
sudo mkdir -p /var/www/mwpp /var/backups/mwpp /var/log/mwpp
sudo chown -R mwpp:mwpp /var/www/mwpp /var/backups/mwpp /var/log/mwpp
```

### 2.3 Deploy application code

**Option A — Git clone (recommended)**

```bash
sudo -u mwpp git clone <YOUR_REPO_URL> /var/www/mwpp
cd /var/www/mwpp
# If repo root is the parent folder, cd into ministry_project:
# cd /var/www/mwpp/ministry_project
```

**Option B — Upload via SCP/SFTP**

Upload the `ministry_project` directory contents to `/var/www/mwpp`.

### 2.4 Python virtual environment

```bash
cd /var/www/mwpp
sudo -u mwpp python3 -m venv .venv
sudo -u mwpp .venv/bin/pip install --upgrade pip
sudo -u mwpp .venv/bin/pip install -r requirements.txt
```

### 2.5 Writable runtime directories

```bash
cd /var/www/mwpp
sudo -u mwpp mkdir -p logs database app/static/uploads/gallery app/static/uploads/leaders app/static/uploads/events
```

---

## 3. PostgreSQL Setup

### 3.1 Create database and user

```bash
sudo -u postgres psql <<'EOF'
CREATE USER mwpp_user WITH PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';
CREATE DATABASE mwpp_ministry OWNER mwpp_user;
GRANT ALL PRIVILEGES ON DATABASE mwpp_ministry TO mwpp_user;
\q
EOF
```

### 3.2 Restrict local connections (default on Ubuntu)

PostgreSQL should accept local connections only. Verify in `/etc/postgresql/*/main/pg_hba.conf` that local connections use `scram-sha-256` or `md5`, not open remote access.

### 3.3 Connection string

```text
postgresql://mwpp_user:REPLACE_WITH_STRONG_PASSWORD@localhost:5432/mwpp_ministry
```

### 3.4 Run Alembic migrations

```bash
cd /var/www/mwpp
sudo -u mwpp bash -c 'set -a && source .env && set +a && .venv/bin/flask db upgrade'
```

Run this **after** creating `.env` (Section 4). Production must use migrations — not `db.create_all()`.

### 3.5 Create first admin user

Register via the site (`/auth/register`), then promote in Flask shell:

```bash
cd /var/www/mwpp
sudo -u mwpp bash -c 'set -a && source .env && set +a && .venv/bin/flask shell'
```

```python
from app.models import User
from app.extensions import db

user = User.query.filter_by(email="admin@yourdomain.com").first()
user.role = "admin"
db.session.commit()
exit()
```

Alternatively, create the user directly in the shell with `set_password()`.

---

## 4. Environment Variables

Create `/var/www/mwpp/.env` owned by `mwpp` with mode `600`:

```bash
sudo -u mwpp nano /var/www/mwpp/.env
sudo chmod 600 /var/www/mwpp/.env
```

### 4.1 Required production variables

```bash
# Flask
FLASK_ENV=production
FLASK_APP=run.py

# Security (generate with: python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_SECRET
API_KEY=REPLACE_WITH_API_WRITE_KEY

# Database
DATABASE_URL=postgresql://mwpp_user:REPLACE_WITH_STRONG_PASSWORD@localhost:5432/mwpp_ministry

# Public URL (must match HTTPS domain — no trailing slash)
SITE_URL=https://yourdomain.com

# CORS allowlist for /api/v1 (comma-separated, no spaces)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 4.2 Recommended optional variables

```bash
# Ministry contact
MINISTRY_EMAIL=womenofpassionandpurpose2024@gmail.com
MINISTRY_PHONE=
MINISTRY_ADDRESS=

# Mail (if sending contact notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=no-reply@yourdomain.com

# Payments (if using online giving)
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
FLUTTERWAVE_SECRET_KEY=

# WOP App store links
APP_STORE_URL=
PLAY_STORE_URL=

# Gallery
GALLERY_PER_PAGE=12

# Gunicorn
GUNICORN_BIND=127.0.0.1:8000
GUNICORN_WORKERS=2
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

### 4.3 Payment dashboard configuration

After deploy, configure provider dashboards:

| Provider | Callback / redirect URL |
|----------|-------------------------|
| Flutterwave | `https://yourdomain.com/giving/success` |
| Paystack | `https://yourdomain.com/giving/success` |

### 4.4 Load env in systemd

The Gunicorn service file (Section 5) loads `.env` via `EnvironmentFile`. Never commit `.env` to Git.

---

## 5. Gunicorn Service File

Create `/etc/systemd/system/mwpp.service`:

```ini
[Unit]
Description=Men and Women of Passion and Purpose (Gunicorn)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=mwpp
Group=mwpp
WorkingDirectory=/var/www/mwpp
EnvironmentFile=/var/www/mwpp/.env
ExecStart=/var/www/mwpp/.venv/bin/gunicorn -c gunicorn.conf.py "run:app"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
PrivateTmp=true
Restart=on-failure
RestartSec=5

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/mwpp/logs /var/www/mwpp/app/static/uploads /var/www/mwpp/database
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mwpp
sudo systemctl start mwpp
sudo systemctl status mwpp
```

View logs:

```bash
sudo journalctl -u mwpp -f
```

---

## 6. Nginx Configuration

### 6.1 HTTP server block (pre-SSL)

Create `/etc/nginx/sites-available/mwpp`:

```nginx
upstream mwpp_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 16M;

    # Certbot webroot (added automatically by certbot --nginx)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /static/ {
        alias /var/www/mwpp/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location / {
        proxy_pass http://mwpp_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

Enable the site:

```bash
sudo mkdir -p /var/www/certbot
sudo ln -s /etc/nginx/sites-available/mwpp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6.2 Redirect www to apex (optional)

If you prefer `www` → bare domain, add a separate server block or use Certbot's redirect option during SSL setup.

---

## 7. SSL Configuration (Let's Encrypt)

### 7.1 Obtain certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts:

- Enter email for renewal notices
- Agree to terms
- Choose whether to redirect HTTP → HTTPS (recommended: **Yes**)

Certbot modifies the Nginx config to add `listen 443 ssl` and certificate paths.

### 7.2 Verify auto-renewal

```bash
sudo certbot renew --dry-run
sudo systemctl status certbot.timer
```

Certificates renew automatically via systemd timer. Default renewal attempts occur twice daily.

### 7.3 Expected post-Certbot HTTPS block

Certbot typically produces something like:

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 16M;

    location /static/ {
        alias /var/www/mwpp/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location / {
        proxy_pass http://mwpp_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

### 7.4 Recommended Nginx security additions (manual)

After Certbot succeeds, optionally add to the `443` server block:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

Application-level headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) are already set by Flask. See `DEPLOYMENT.md` for optional CSP at the proxy layer.

---

## 8. Backup Automation

### 8.1 Backup script

Create `/usr/local/bin/mwpp-backup.sh`:

```bash
sudo tee /usr/local/bin/mwpp-backup.sh > /dev/null <<'SCRIPT'
#!/bin/bash
set -euo pipefail

BACKUP_ROOT="/var/backups/mwpp"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DB_NAME="mwpp_ministry"
DB_USER="mwpp_user"
APP_DIR="/var/www/mwpp"
RETENTION_DAYS=7

mkdir -p "${BACKUP_ROOT}/db" "${BACKUP_ROOT}/uploads"

# PostgreSQL dump
export PGPASSWORD="$(grep DATABASE_URL "${APP_DIR}/.env" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')"
pg_dump -h localhost -U "${DB_USER}" -Fc -f "${BACKUP_ROOT}/db/mwpp_${TIMESTAMP}.dump" "${DB_NAME}"

# Uploads archive
tar -czf "${BACKUP_ROOT}/uploads/uploads_${TIMESTAMP}.tar.gz" \
  -C "${APP_DIR}/app/static" uploads 2>/dev/null || true

# Prune old backups
find "${BACKUP_ROOT}/db" -name "*.dump" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_ROOT}/uploads" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date -Is)] Backup completed: ${TIMESTAMP}"
SCRIPT

sudo chmod 750 /usr/local/bin/mwpp-backup.sh
```

> **Note:** For production, prefer a `.pgpass` file or a dedicated backup user instead of parsing `.env` for the password. See `BACKUP_AND_RECOVERY.md` for restore steps.

### 8.2 Cron schedule (daily at 02:30 UTC)

```bash
sudo tee /etc/cron.d/mwpp-backup > /dev/null <<'EOF'
30 2 * * * root /usr/local/bin/mwpp-backup.sh >> /var/log/mwpp/backup.log 2>&1
EOF
```

### 8.3 Off-site copy (recommended)

Copy backups to remote storage nightly:

```bash
# Example: rsync to backup server
rsync -az /var/backups/mwpp/ backup-user@backup-server:/backups/mwpp/

# Example: AWS S3
aws s3 sync /var/backups/mwpp/ s3://your-bucket/mwpp-backups/ --storage-class STANDARD_IA
```

### 8.4 Quarterly restore test

On a staging VPS, restore a recent `.dump` and uploads archive per `BACKUP_AND_RECOVERY.md`.

---

## 9. Monitoring Recommendations

### 9.1 Service health (essential)

| Check | Command / endpoint |
|-------|------------------|
| Gunicorn running | `systemctl is-active mwpp` |
| Nginx running | `systemctl is-active nginx` |
| PostgreSQL running | `systemctl is-active postgresql` |
| App health API | `curl -fsS https://yourdomain.com/api/v1/health` |
| Homepage | `curl -fsS -o /dev/null -w "%{http_code}" https://yourdomain.com/` |

### 9.2 Uptime monitoring (external)

Use a free or paid service to poll every 1–5 minutes:

- [UptimeRobot](https://uptimerobot.com)
- [Better Stack](https://betterstack.com)
- [Pingdom](https://www.pingdom.com)

Monitor:

- `https://yourdomain.com/`
- `https://yourdomain.com/api/v1/health`

Alert via email/SMS/Slack on non-200 responses or timeouts.

### 9.3 Log monitoring

| Log | Location |
|-----|----------|
| Application | `/var/www/mwpp/logs/app.log` |
| Gunicorn | `journalctl -u mwpp` |
| Nginx access | `/var/log/nginx/access.log` |
| Nginx errors | `/var/log/nginx/error.log` |
| Backup job | `/var/log/mwpp/backup.log` |

Watch for spikes in 4xx/5xx:

```bash
sudo tail -f /var/log/nginx/access.log
sudo journalctl -u mwpp -p err -f
```

### 9.4 Resource monitoring

```bash
# Disk space (uploads and backups fill disk first)
df -h /var/www /var/backups

# Memory and CPU
htop

# PostgreSQL connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

Consider **Netdata**, **Grafana + Prometheus**, or your VPS provider's monitoring dashboard for ongoing metrics.

### 9.5 Security monitoring

- `fail2ban` is installed — verify SSH jail is active: `sudo fail2ban-client status sshd`
- Enable unattended security upgrades: `sudo apt install unattended-upgrades`
- Review `mwpp` and `postgres` auth logs after deploy

### 9.6 SSL expiry

Certbot auto-renews, but add a calendar reminder or external check for certificate expiry (Let's Encrypt certs are valid 90 days; renewed at ~60 days).

---

## 10. Post-Deployment Verification Checklist

Run through this list immediately after go-live.

### Infrastructure

- [ ] `sudo nginx -t` passes
- [ ] `systemctl status mwpp` is **active (running)**
- [ ] `systemctl status nginx` is **active (running)**
- [ ] `systemctl status postgresql` is **active (running)**
- [ ] HTTPS loads with valid certificate (padlock in browser)
- [ ] HTTP redirects to HTTPS
- [ ] `ufw status` shows only 22, 80, 443 (or your intended ports)

### Environment and database

- [ ] `.env` exists, mode `600`, owned by `mwpp`
- [ ] `FLASK_ENV=production`
- [ ] `SECRET_KEY`, `API_KEY`, `DATABASE_URL`, `SITE_URL` are set
- [ ] `ALLOWED_ORIGINS` includes production domain(s)
- [ ] `flask db upgrade` completed without errors
- [ ] First admin account created and can access `/admin`

### Public pages

- [ ] Homepage: `https://yourdomain.com/`
- [ ] Events: `https://yourdomain.com/events`
- [ ] Gallery: `https://yourdomain.com/gallery`
- [ ] Contact: `https://yourdomain.com/contact`
- [ ] Prayer: `https://yourdomain.com/prayer/prayer_request`
- [ ] Giving: `https://yourdomain.com/giving/`
- [ ] WOP App: `https://yourdomain.com/app`
- [ ] Login: `https://yourdomain.com/auth/login`

### Forms and writes

- [ ] Contact form submission succeeds (CSRF + flash message)
- [ ] Prayer form submission succeeds
- [ ] Admin login works; session persists across requests
- [ ] Admin promote user action works
- [ ] Admin delete/publish/feature toggles work (CSRF protected)

### API

- [ ] `GET https://yourdomain.com/api/v1/health` returns success
- [ ] `GET https://yourdomain.com/api/v1/events` returns JSON
- [ ] `GET https://yourdomain.com/api/v1/gallery` returns JSON
- [ ] API write without `X-API-Key` returns `401` with `{"success": false, "message": "Unauthorized"}`
- [ ] API write with valid `X-API-Key` succeeds
- [ ] CORS: request with `Origin: https://yourdomain.com` receives `Access-Control-Allow-Origin`
- [ ] CORS: request with `Origin: https://evil.com` does **not** receive allow header

### Security headers

- [ ] `X-Frame-Options: SAMEORIGIN` present
- [ ] `X-Content-Type-Options: nosniff` present
- [ ] `Referrer-Policy: strict-origin-when-cross-origin` present
- [ ] Open Graph image URL is absolute (`https://yourdomain.com/static/images/...`)

### Payments (if enabled)

- [ ] Paystack/Flutterwave keys set in `.env`
- [ ] Provider dashboard callback URL set to `https://yourdomain.com/giving/success`
- [ ] Test transaction completes and redirects back to success page

### Static assets and uploads

- [ ] Logo and favicon display correctly
- [ ] `/static/` files served by Nginx (check response headers for cache)
- [ ] `app/static/uploads/` subdirectories exist and are writable by `mwpp`
- [ ] Admin can upload gallery/leader/event images

### Backups and operations

- [ ] Manual backup script runs: `sudo /usr/local/bin/mwpp-backup.sh`
- [ ] Backup files appear in `/var/backups/mwpp/db/` and `/var/backups/mwpp/uploads/`
- [ ] Cron job installed: `cat /etc/cron.d/mwpp-backup`
- [ ] `certbot renew --dry-run` succeeds
- [ ] Application log writing: `tail /var/www/mwpp/logs/app.log`

### Performance smoke test

- [ ] Homepage loads in under 3 seconds on mobile network
- [ ] Gallery pagination works
- [ ] No 500 errors in `journalctl -u mwpp` during testing

---

## Quick Reference — Common Operations

### Deploy code update

```bash
cd /var/www/mwpp
sudo -u mwpp git pull
sudo -u mwpp .venv/bin/pip install -r requirements.txt
sudo -u mwpp bash -c 'set -a && source .env && set +a && .venv/bin/flask db upgrade'
sudo systemctl restart mwpp
```

### Restart services

```bash
sudo systemctl restart mwpp
sudo systemctl reload nginx
```

### Roll back Gunicorn

```bash
cd /var/www/mwpp
sudo -u mwpp git checkout <previous-tag-or-commit>
sudo systemctl restart mwpp
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `DEPLOYMENT.md` | Application config, migrations, security headers |
| `BACKUP_AND_RECOVERY.md` | Full backup/restore and disaster recovery |
| `docs/deployment/github-actions.md` | GitHub Actions CI/CD (auto-deploy to VPS) |
| `.env.example` | Environment variable template |

---

*Last updated: June 2026 — Men and Women of Passion and Purpose production stack.*
