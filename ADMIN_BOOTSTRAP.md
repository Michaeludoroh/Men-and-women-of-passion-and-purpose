# Admin Bootstrap Guide

Production-safe CLI utilities for creating and managing the first admin account on the **Men and Women of Passion and Purpose** website.

These scripts operate directly on the database configured in your environment. They do not modify application routes, templates, or runtime behavior.

---

## Overview

| Script | Purpose |
|--------|---------|
| `scripts/create_admin.py` | Create the first admin user |
| `scripts/reset_admin_password.py` | Reset an existing admin password |
| `scripts/list_users.py` | List all users (ID, name, email, role, created date) |

Shared logic lives in `scripts/admin_bootstrap.py` (model/role detection, validation, env loading).

---

## How It Works

### User model

The scripts auto-detect `User` from `app.models`:

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Primary key |
| `name` | String(120) | Required |
| `email` | String(255) | Unique, indexed |
| `password` | String(255) | Stored hashed via `User.set_password()` |
| `role` | String(50) | Default `"member"`; admin uses `"admin"` |
| `created_at` | DateTime | UTC timestamp |

### Admin role detection

The admin role is read from `app/routes/admin_routes.py`:

- Access guard: `current_user.role != "admin"`
- Promotion: `user.role = "admin"`

**Detected role: `"admin"`**

### Password hashing

Passwords are never stored in plain text. Both scripts call:

```python
user.set_password(raw_password)
```

This uses Werkzeug's `generate_password_hash()` — the same method used by registration and login.

### Validation rules

| Field | Rule |
|-------|------|
| Name | 2–120 characters |
| Email | Valid format (`email-validator`), max 255 characters, normalized to lowercase |
| Password | Minimum 6 characters (matches `RegisterForm`), confirmation required |

---

## Prerequisites

1. Python virtual environment activated
2. Dependencies installed: `pip install -r requirements.txt`
3. Database schema applied:

```bash
flask db upgrade
```

---

## Development Usage (SQLite)

From the `ministry_project/` directory:

```bash
# Windows
.venv\Scripts\activate
python scripts/create_admin.py

# Linux/macOS
source .venv/bin/activate
python scripts/create_admin.py
```

Without a `.env` file, the app defaults to SQLite at `database/site.db`.

### Example: Create first admin

```
Detected User model: User
Detected admin role: admin
Database: sqlite:///database/site.db

Name: Ministry Admin
Email: admin@yourdomain.com
Password:
Confirm password:

SUCCESS: Admin account created for 'admin@yourdomain.com' with role 'admin'.
```

If the email already exists:

```
User with email 'admin@yourdomain.com' already exists. No changes made.
```

---

## Production Usage (PostgreSQL)

On your VPS, run as the application user after `.env` is configured:

```bash
cd /var/www/mwpp
sudo -u mwpp bash -c 'source .venv/bin/activate && python scripts/create_admin.py'
```

### Required `.env` values for production

When `FLASK_ENV=production`, the application validates:

- `SECRET_KEY`
- `DATABASE_URL`
- `API_KEY`
- `SITE_URL`

Ensure these are set in `/var/www/mwpp/.env` before running bootstrap scripts.

### Recommended production workflow

```bash
# 1. Apply migrations
sudo -u mwpp bash -c 'set -a && source .env && set +a && .venv/bin/flask db upgrade'

# 2. Create first admin (interactive)
sudo -u mwpp bash -c 'source .venv/bin/activate && python scripts/create_admin.py'

# 3. Verify user was created
sudo -u mwpp bash -c 'source .venv/bin/activate && python scripts/list_users.py'

# 4. Log in at https://yourdomain.com/auth/login
# 5. Access admin dashboard at https://yourdomain.com/admin
```

---

## Reset Admin Password

```bash
python scripts/reset_admin_password.py
```

Prompts:

- Admin email (must belong to a user with role `"admin"`)
- New password + confirmation

Example:

```
Admin email: admin@yourdomain.com
New password:
Confirm password:

SUCCESS: Password updated for admin 'admin@yourdomain.com'.
```

The script refuses to reset passwords for non-admin accounts.

---

## List Users

```bash
python scripts/list_users.py
```

Example output:

```
ID  Name            Email                  Role    Created
--  --------------  ---------------------  ------  ------------------
1   Ministry Admin  admin@yourdomain.com   admin   2026-06-19 06:30 UTC
2   John Member     john@example.com       member  2026-06-19 07:15 UTC

Total users: 2 (1 admin)
```

Database credentials in the connection string are masked in script output (`***`).

---

## Safety Features

- **No duplicate emails** — `create_admin.py` exits safely if email exists
- **Admin-only reset** — `reset_admin_password.py` verifies `role == "admin"`
- **Hashed passwords** — `User.set_password()` only; plain text never persisted
- **Masked DB URI** — passwords hidden in console output
- **Email validation** — rejects malformed addresses before database writes
- **Non-interactive safe exit** — duplicate/missing users exit with code `0` or `1` and clear messages

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FAIL: Setup error` — missing env vars | Set required `.env` values for production |
| `no such table: user` | Run `flask db upgrade` first |
| `User already exists` | Use `reset_admin_password.py` or choose a different email |
| `does not have admin role` | Promote via admin panel or update role in `list_users.py` output |
| Script hangs on password | Password fields are hidden (`getpass`); type blindly and press Enter |

---

## Security Notes

- Run these scripts only on trusted servers with SSH/shell access
- Do not commit `.env` or share generated passwords
- Delete shell history containing passwords if required by your policy
- Rotate `SECRET_KEY` and admin passwords if a breach is suspected
- Prefer `reset_admin_password.py` over manual database edits

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `VPS_DEPLOYMENT.md` | Full Ubuntu VPS deployment runbook |
| `DEPLOYMENT.md` | Application-level production config |
| `BACKUP_AND_RECOVERY.md` | Database backup and restore |
