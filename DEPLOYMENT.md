# Deployment Guide — Men and Women of Passion and Purpose

This guide prepares the ministry website for production using **Gunicorn**, **PostgreSQL**, and **Alembic migrations**.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- A reverse proxy (Nginx or Caddy) for HTTPS

## 1. Environment setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

Copy environment template and configure:

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Linux/macOS
```

### Required production variables

| Variable | Description |
|----------|-------------|
| `FLASK_ENV` | Must be `production` |
| `SECRET_KEY` | Long random secret (required) |
| `DATABASE_URL` | PostgreSQL URI (`postgresql://user:pass@host:5432/dbname`) |
| `API_KEY` | Protects API write endpoints (required) |
| `SITE_URL` | Public HTTPS base URL, e.g. `https://yourdomain.com` (required) |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowlist for `/api/v1` |

`postgres://` URLs are automatically normalized to `postgresql://`.

### Session cookies (production defaults)

Production enables secure session defaults automatically:

- `SESSION_COOKIE_SECURE = True`
- `SESSION_COOKIE_HTTPONLY = True`
- `SESSION_COOKIE_SAMESITE = Lax`
- `PERMANENT_SESSION_LIFETIME = 7 days`

## 2. Database migrations (primary workflow)

Production must **not** rely on `db.create_all()`.

```bash
set FLASK_APP=run.py
set FLASK_ENV=production
flask db upgrade
```

Create new migrations after model changes:

```bash
flask db migrate -m "describe change"
flask db upgrade
```

Development may still bootstrap with `python run.py` (calls `create_all()` only when `FLASK_ENV` is not `production`).

## 3. Media and upload paths

Uploads are stored under `app/static/uploads/`:

| Subfolder | Content |
|-----------|---------|
| `gallery/` | Gallery images |
| `leaders/` | Leadership photos |
| `events/` | Event banner images |

Branding assets live in `app/static/images/` (logo, favicon, OG image).

**Production note:** Mount `app/static/uploads/` on persistent storage so uploads survive redeployments.

## 4. Run with Gunicorn

```bash
set FLASK_ENV=production
set FLASK_APP=run.py
gunicorn -c gunicorn.conf.py "run:app"
```

Or bind explicitly:

```bash
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8000 "run:app"
```

## 5. Reverse proxy (Nginx example)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/ministry_project/app/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Post-deploy checklist

- [ ] `flask db upgrade` completed
- [ ] `SECRET_KEY`, `DATABASE_URL`, `API_KEY`, and `SITE_URL` set
- [ ] `ALLOWED_ORIGINS` configured for API clients
- [ ] Upload directories writable (`uploads/gallery`, `uploads/leaders`, `uploads/events`)
- [ ] Logo/favicon assets present in `static/images/`
- [ ] Admin account created
- [ ] HTTPS enabled
- [ ] Payment and mail env vars configured (if using giving/contact email)

## 7. Health checks

- Website: `GET /`
- API health: `GET /api/v1/health`
- Gallery: `GET /gallery`
- Events: `GET /events`
- WOP App page: `GET /app`

## 8. Security headers

The application sets these headers on every response:

| Header | Value |
|--------|-------|
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

API CORS uses `ALLOWED_ORIGINS` — wildcard `*` is not used. Only listed origins receive `Access-Control-Allow-Origin`.

### Content-Security-Policy (recommended at reverse proxy)

CSP is not enforced in-app because the site uses Tailwind CDN and Font Awesome CDN. Configure at Nginx/Caddy when ready:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com; connect-src 'self'; frame-ancestors 'self';" always;
```

Tune `script-src` and `style-src` after auditing inline scripts. Consider self-hosting Tailwind for stricter CSP.

## 9. Logs

Application logs: `logs/app.log`  
Gunicorn access/error logs: stdout (configurable in `gunicorn.conf.py`)
