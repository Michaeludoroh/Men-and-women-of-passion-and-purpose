# GitHub Actions CI/CD — Men and Women of Passion and Purpose

Production deployment automation for the ministry website. This pipeline **automates the existing VPS process** without changing Gunicorn, Flask, Nginx, `mwpp.service`, or `/var/www/mwpp`.

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
git pull origin main   (as mwpp in /var/www/mwpp)
        │
        ▼
systemctl restart mwpp
        │
        ▼
Health checks (service + HTTP 200 pages)
        │
        ├─ PASS → Deployment successful
        │
        └─ FAIL → Automatic rollback to previous commit + restart + re-check
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
| `VPS_USERNAME` | **Yes** | SSH login user (must be able to `sudo` for `systemctl` and run git as `mwpp`) |
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

Copy the **public** key to the VPS authorized_keys for `VPS_USERNAME`:

```bash
# Example as root on the VPS
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Add the **private** key contents as GitHub secret `VPS_SSH_KEY`.

### 2. Pin host key (recommended)

On your PC:

```bash
ssh-keyscan -p 22 YOUR_VPS_HOST
```

Paste the output into GitHub secret `VPS_SSH_KNOWN_HOSTS`.

### 3. Passwordless sudo for service control

The remote script restarts `mwpp` via `systemctl`. If `VPS_USERNAME` is not `root`, allow only the needed commands:

```bash
sudo visudo -f /etc/sudoers.d/mwpp-deploy
```

Example (adjust username):

```
deploy ALL=(mwpp) NOPASSWD: /usr/bin/git, /usr/bin/git *
deploy ALL=(root) NOPASSWD: /bin/systemctl restart mwpp, /bin/systemctl status mwpp, /bin/systemctl is-active mwpp, /bin/journalctl -u mwpp *
```

If you SSH as `root`, no sudoers change is required; the script uses `sudo -u mwpp` for git.

### 4. Confirm app path and git remote

```bash
cd /var/www/mwpp
sudo -u mwpp git remote -v
sudo -u mwpp git status
sudo systemctl status mwpp
```

The VPS clone must track `origin/main` for the same GitHub repository.

### 5. Ensure GitHub can reach the VPS

- Firewall allows SSH from GitHub Actions IPs **or** keep SSH open with key-only auth + fail2ban
- Prefer a dedicated deploy user + deploy key with no interactive shell extras

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
| Backup | Writes current `git rev-parse HEAD` under `/var/backups/mwpp/` |
| Pull | `git fetch` + `git pull --ff-only origin main` as `mwpp` |
| Restart | `systemctl restart mwpp` |
| Health | Service active, Gunicorn process present, HTTP 200 for `/`, `/partnership/`, `/giving/`, `/leadership` |
| Summary | Job summary in the Actions UI |

Remote logic lives in `scripts/deploy/remote_deploy.sh` (piped over SSH so the **new** script always runs).

---

## Health check strategy

Checks run **on the VPS** against Gunicorn (`HEALTH_BASE_URL`, default `http://127.0.0.1:8000`):

1. `systemctl is-active mwpp`
2. Gunicorn process for user `mwpp`
3. HTTP 200:
   - `/` (homepage)
   - `/partnership/`
   - `/giving/`
   - `/leadership`

Retries: 12 attempts × 5 seconds (configurable in the remote script).

Any failure after pull/restart triggers **automatic rollback**.

---

## Rollback strategy

On failure after code has been updated:

1. `git reset --hard <previous_sha>`
2. `systemctl restart mwpp`
3. Re-run health checks
4. Log `ROLLBACK COMPLETED` or `ROLLBACK HEALTH CHECK FAILED`

Previous SHA files:

- `/var/backups/mwpp/pre-deploy-<timestamp>.sha`
- `/var/backups/mwpp/last_good_sha`

### Manual rollback

```bash
cd /var/www/mwpp
PREV=$(cat /var/backups/mwpp/last_good_sha)
sudo -u mwpp git reset --hard "$PREV"
sudo systemctl restart mwpp
curl -I http://127.0.0.1:8000/
```

---

## How to deploy manually (unchanged)

```bash
cd /var/www/mwpp
sudo -u mwpp git pull
sudo systemctl restart mwpp
```

Optional (deps / migrations — not part of the automated minimal path):

```bash
sudo -u mwpp .venv/bin/pip install -r requirements.txt
sudo -u mwpp bash -c 'set -a && source .env && set +a && .venv/bin/flask db upgrade'
sudo systemctl restart mwpp
```

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
   cd /var/www/mwpp
   sudo -u mwpp git status
   sudo -u mwpp git reset --hard "$(cat /var/backups/mwpp/last_good_sha)"
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
- Least privilege: dedicated deploy key; sudo limited to service/git as needed

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

- [ ] GitHub Secrets configured (`VPS_HOST`, `VPS_USERNAME`, `VPS_SSH_KEY`, `VPS_PORT`)
- [ ] `VPS_SSH_KNOWN_HOSTS` pinned (recommended)
- [ ] SSH key auth works from a test machine
- [ ] Passwordless sudo (or root SSH) can restart `mwpp`
- [ ] `/var/www/mwpp` is a clean git clone of this repo on `main`
- [ ] First Actions run succeeds (validation + deploy + health)
- [ ] Intentional bad deploy test confirms rollback (optional but recommended)

---

*Related: `VPS_DEPLOYMENT.md`, `DEPLOYMENT.md`, `BACKUP_AND_RECOVERY.md`*
