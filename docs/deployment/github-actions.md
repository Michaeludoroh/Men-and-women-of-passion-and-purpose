# GitHub Actions CI/CD — Men and Women of Passion and Purpose

Production deployment automation for the ministry website. This pipeline **automates the existing VPS process** without changing Gunicorn, Flask, Nginx, or `mwpp.service`.

## Actual production configuration

| Item | Value |
|------|--------|
| Systemd service | `mwpp.service` |
| Service user | `ubuntu` |
| Service group | `www-data` |
| Working directory | `/home/ubuntu/Men-and-women-of-passion-and-purpose` |
| Virtualenv | `/home/ubuntu/Men-and-women-of-passion-and-purpose/.venv` |
| Process | Gunicorn |

---

## How deployment works

```
Developer (VS Code)
        │
        ▼
git add / commit / push origin main
        │
        ▼
GitHub Actions  (.github/workflows/deploy.yml)
        │
        ├─ Pre-deployment validation (syntax, templates, integrity)
        │
        ▼
SSH into production VPS
        │
        ▼
Backup current Git commit SHA
        │
        ▼
git pull origin main   (as ubuntu in /home/ubuntu/Men-and-women-of-passion-and-purpose)
        │
        ▼
flask db upgrade       (.venv + .env; must succeed before restart)
        │
        ▼
systemctl restart mwpp
        │
        ▼
Health checks (service + HTTP 200 pages)
        │
        ├─ PASS → Deployment successful
        │
        └─ FAIL → Automatic rollback to previous commit (+ DB downgrade when possible) + restart + re-check
           (migration failure: restore git/DB, do NOT restart Gunicorn)
```

**Triggers**

| Event | Deploys? |
|-------|----------|
| Push to `main` | Yes |
| Manual **Run workflow** (`workflow_dispatch`) | Yes |
| Feature / other branches | No |

---

## Required GitHub Secrets

Configure under: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Required | Description |
|--------|----------|-------------|
| `VPS_HOST` | **Yes** | VPS hostname or public IP |
| `VPS_USERNAME` | **Yes** | SSH login user (typically `ubuntu`; must be able to `sudo systemctl` for `mwpp`) |
| `VPS_SSH_KEY` | **Yes** | Private SSH key (full PEM, including `BEGIN` / `END` lines) |
| `VPS_PORT` | **Yes** | SSH port (usually `22`) |
| `VPS_SSH_KNOWN_HOSTS` | Recommended | Output of `ssh-keyscan -p PORT HOST` (pins host key) |
| `HEALTH_BASE_URL` | Optional | Defaults to `http://127.0.0.1:8000` (Gunicorn behind Nginx) |

**Never commit secrets, private keys, or `.env` files to the repository.**

---

## One-time VPS setup

### 1. Deploy SSH key (on your PC)

```bash
# Generate a dedicated deploy key (do not reuse your personal key)
ssh-keygen -t ed25519 -C "mwpp-github-deploy" -f mwpp_deploy_ed25519 -N ""
```

Copy the **public** key to the VPS `ubuntu` user authorized_keys:

```bash
# On the VPS as ubuntu
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Add the **private** key contents as GitHub secret `VPS_SSH_KEY`.  
Set `VPS_USERNAME` to `ubuntu`.

### 2. Pin host key (recommended)

On your PC:

```bash
ssh-keyscan -p 22 YOUR_VPS_HOST
```

Paste the output into GitHub secret `VPS_SSH_KNOWN_HOSTS`.

### 3. Passwordless sudo for service control

The remote script restarts `mwpp` via `sudo systemctl`. Allow only the needed commands for `ubuntu`:

```bash
sudo visudo -f /etc/sudoers.d/mwpp-deploy
```

```
ubuntu ALL=(root) NOPASSWD: /bin/systemctl restart mwpp, /bin/systemctl status mwpp, /bin/systemctl is-active mwpp, /bin/journalctl -u mwpp *
```

Git operations run as `ubuntu` (the SSH user / app user), so no `sudo -u` is required for `git pull` when `VPS_USERNAME=ubuntu`.

### 4. Confirm app path and git remote

```bash
cd /home/ubuntu/Men-and-women-of-passion-and-purpose
git remote -v
git status
sudo systemctl status mwpp
ls .venv
```

The VPS clone must track `origin/main` for the same GitHub repository.

### 5. Ensure GitHub can reach the VPS

- Firewall allows SSH from GitHub Actions IPs **or** keep SSH open with key-only auth + fail2ban
- Prefer a dedicated deploy key

### 6. First workflow run

1. Commit and push these CI files to `main`, **or** run **Actions → Deploy Production → Run workflow**
2. Watch the job logs for validation → SSH → backup → pull → restart → health

---

## Deployment flow (detailed)

| Stage | What happens |
|-------|----------------|
| Checkout | Actions checks out the commit being deployed |
| Validate | `scripts/deploy/validate.sh` — integrity, Python `compileall`, template balance, CSS presence, workflow YAML |
| SSH | Key-based login; host key verification |
| Backup | Writes current `git rev-parse HEAD` under `/home/ubuntu/mwpp-deploy-backups/` |
| Pull | `git fetch` + `git pull --ff-only origin main` as `ubuntu` in the app directory |
| Migrate | Activate `.venv`, load `.env`, run `flask db upgrade` (**before** restart) |
| Restart | `systemctl restart mwpp` (only after migrations succeed) |
| Health | Service active, Gunicorn process for `ubuntu`, HTTP 200 for `/`, `/partnership/`, `/giving/`, `/leadership` |
| Summary | Job summary in the Actions UI |

Remote logic lives in `scripts/deploy/remote_deploy.sh` (piped over SSH so the **new** script always runs).

---

## Health check strategy

Checks run **on the VPS** against Gunicorn (`HEALTH_BASE_URL`, default `http://127.0.0.1:8000`):

1. `systemctl is-active mwpp`
2. Gunicorn process for user `ubuntu`
3. HTTP 200:
   - `/` (homepage)
   - `/partnership/`
   - `/giving/`
   - `/leadership`

Retries: 12 attempts × 5 seconds (configurable in the remote script).

Any failure after pull/migrate/restart triggers **automatic rollback**.

Migration failures restore the previous git commit and attempt `flask db downgrade` to the pre-deploy revision. **Gunicorn is not restarted** on migration failure (the running process keeps serving the previous code).

---

## Rollback strategy

On failure after code has been updated:

1. `git reset --hard <previous_sha>`
2. Attempt `flask db downgrade <pre-deploy-revision>` when the revision was captured
3. `systemctl restart mwpp` (skipped for migration-only failures)
4. Re-run health checks (when the service was restarted)
5. Log `ROLLBACK COMPLETED` or `ROLLBACK HEALTH CHECK FAILED`

Previous SHA files:

- `/home/ubuntu/mwpp-deploy-backups/pre-deploy-<timestamp>.sha`
- `/home/ubuntu/mwpp-deploy-backups/last_good_sha`

### Manual rollback

```bash
cd /home/ubuntu/Men-and-women-of-passion-and-purpose
PREV=$(cat /home/ubuntu/mwpp-deploy-backups/last_good_sha)
git reset --hard "$PREV"
sudo systemctl restart mwpp
curl -I http://127.0.0.1:8000/
```

---

## How to deploy manually (unchanged architecture)

```bash
cd /home/ubuntu/Men-and-women-of-passion-and-purpose
git pull
set -a && source .env && set +a && .venv/bin/flask db upgrade
sudo systemctl restart mwpp
```

Optional (deps):

```bash
cd /home/ubuntu/Men-and-women-of-passion-and-purpose
.venv/bin/pip install -r requirements.txt
```

Automated deploys always run `flask db upgrade` after `git pull` and before restarting `mwpp`.
---

## How to disable automatic deployment

**Option A — Disable the workflow**

GitHub → **Actions** → **Deploy Production** → **⋯** → **Disable workflow**

**Option B — Protect `main`**

Require PR reviews so pushes to `main` are controlled.

**Option C — Temporary skip**

Push only to a feature branch (workflow does not deploy non-`main` branches).

---

## How to recover from deployment failure

1. Open the failed Actions run and read the log stage (pull / restart / health / rollback).
2. If rollback completed, the site should already be on the previous commit — verify pages in a browser.
3. If rollback failed:
   ```bash
   cd /home/ubuntu/Men-and-women-of-passion-and-purpose
   git status
   git reset --hard "$(cat /home/ubuntu/mwpp-deploy-backups/last_good_sha)"
   sudo systemctl restart mwpp
   sudo journalctl -u mwpp -n 100 --no-pager
   ```
4. Fix the bad commit on a branch, merge to `main`, and redeploy.

---

## Security practices

- Secrets only in GitHub Secrets (never in YAML or repo files)
- SSH private key written to a temp file on the runner and deleted after the job
- `StrictHostKeyChecking yes` with known_hosts
- Deploy lock (`flock`) prevents overlapping deploys on the VPS
- Logs avoid printing secret values
- Concurrency group `production-deploy` prevents overlapping Actions deploys
- Least privilege: dedicated deploy key; sudo limited to `mwpp` service control

---

## Files in this pipeline

| Path | Role |
|------|------|
| `.github/workflows/deploy.yml` | GitHub Actions workflow |
| `scripts/deploy/validate.sh` | Pre-deploy checks on the runner |
| `scripts/deploy/remote_deploy.sh` | VPS pull / restart / health / rollback |
| `docs/deployment/github-actions.md` | This document |

---

## Production readiness checklist

- [ ] GitHub Secrets configured (`VPS_HOST`, `VPS_USERNAME=ubuntu`, `VPS_SSH_KEY`, `VPS_PORT`)
- [ ] `VPS_SSH_KNOWN_HOSTS` pinned (recommended)
- [ ] SSH key auth works as `ubuntu`
- [ ] Passwordless sudo can restart `mwpp`
- [ ] `/home/ubuntu/Men-and-women-of-passion-and-purpose` is a clean git clone on `main`
- [ ] `.venv` exists at that path
- [ ] First Actions run succeeds (validation + deploy + health)
- [ ] Intentional bad deploy test confirms rollback (optional but recommended)

---

*Related: `VPS_DEPLOYMENT.md` (generic Ubuntu runbook — paths there may differ from this live server), `DEPLOYMENT.md`, `BACKUP_AND_RECOVERY.md`*
