#!/usr/bin/env bash
# =============================================================================
# Remote production deploy for Men and Women of Passion and Purpose
# Runs on the VPS (invoked by GitHub Actions over SSH).
#
# Automates the existing manual flow:
#   cd /home/ubuntu/Men-and-women-of-passion-and-purpose
#   git pull
#   flask db upgrade
#   sudo systemctl restart mwpp
# Plus: commit backup, health checks, and automatic rollback on failure.
#
# Production facts (do not invent alternate paths):
#   Service:  mwpp.service
#   User:     ubuntu
#   Group:    www-data
#   App dir:  /home/ubuntu/Men-and-women-of-passion-and-purpose
#   Venv:     /home/ubuntu/Men-and-women-of-passion-and-purpose/.venv
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/Men-and-women-of-passion-and-purpose}"
APP_USER="${APP_USER:-ubuntu}"
APP_GROUP="${APP_GROUP:-www-data}"
SERVICE_NAME="${SERVICE_NAME:-mwpp}"
GIT_BRANCH="${GIT_BRANCH:-main}"
HEALTH_BASE_URL="${HEALTH_BASE_URL:-http://127.0.0.1:8000}"
BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/mwpp-deploy-backups}"
LOCK_FILE="${LOCK_FILE:-/tmp/mwpp-deploy.lock}"
STARTUP_WAIT_SECONDS="${STARTUP_WAIT_SECONDS:-8}"
HEALTH_RETRIES="${HEALTH_RETRIES:-12}"
HEALTH_RETRY_DELAY="${HEALTH_RETRY_DELAY:-5}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/.venv}"
FLASK_BIN="${FLASK_BIN:-${VENV_DIR}/bin/flask}"

# Paths checked after restart (must return HTTP 200)
HEALTH_PATHS=(
  "/"
  "/partnership/"
  "/giving/"
  "/leadership"
)

# Populated during deploy
PREV_SHA=""
PREV_SHA_SHORT=""
NEW_SHA=""
NEW_SHA_SHORT=""
PREV_DB_REV=""

log() {
  printf '[%s] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

as_app() {
  if [[ "$(id -un)" == "$APP_USER" ]]; then
    "$@"
  else
    sudo -u "$APP_USER" -- "$@"
  fi
}

svc() {
  if [[ "$(id -un)" == "root" ]]; then
    systemctl "$@"
  else
    sudo systemctl "$@"
  fi
}

acquire_lock() {
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    fail "Another deployment is already in progress (lock: $LOCK_FILE)"
  fi
  log "Acquired deploy lock"
}

ensure_layout() {
  [[ -d "$APP_DIR" ]] || fail "App directory not found: $APP_DIR"
  [[ -d "$APP_DIR/.git" ]] || fail "Not a git repository: $APP_DIR"
  [[ -x "$FLASK_BIN" ]] || fail "Flask binary not found (activate venv path): ${FLASK_BIN}"
  [[ -d "$VENV_DIR" ]] || fail "Virtualenv not found: ${VENV_DIR}"
  mkdir -p "$BACKUP_DIR"
  if [[ "$(id -un)" == "root" ]]; then
    chown -R "${APP_USER}:${APP_GROUP}" "$BACKUP_DIR" 2>/dev/null || true
  fi
}

backup_commit() {
  PREV_SHA="$(as_app git -C "$APP_DIR" rev-parse HEAD)"
  PREV_SHA_SHORT="$(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
  BACKUP_STAMP="$(date -u +'%Y%m%dT%H%M%SZ')"
  BACKUP_FILE="${BACKUP_DIR}/pre-deploy-${BACKUP_STAMP}.sha"
  printf '%s\n' "$PREV_SHA" >"$BACKUP_FILE"
  if [[ "$(id -un)" == "root" ]]; then
    chown "${APP_USER}:${APP_GROUP}" "$BACKUP_FILE" 2>/dev/null || true
  fi
  printf '%s\n' "$PREV_SHA" >"${BACKUP_DIR}/last_good_sha"
  if [[ "$(id -un)" == "root" ]]; then
    chown "${APP_USER}:${APP_GROUP}" "${BACKUP_DIR}/last_good_sha" 2>/dev/null || true
  fi
  log "Backed up current commit ${PREV_SHA_SHORT} (${PREV_SHA}) -> ${BACKUP_FILE}"
}

pull_latest() {
  log "Fetching and pulling origin/${GIT_BRANCH}"
  as_app git -C "$APP_DIR" fetch --prune origin "$GIT_BRANCH"
  as_app git -C "$APP_DIR" checkout "$GIT_BRANCH"
  as_app git -C "$APP_DIR" pull --ff-only origin "$GIT_BRANCH"
  NEW_SHA="$(as_app git -C "$APP_DIR" rev-parse HEAD)"
  NEW_SHA_SHORT="$(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
  log "Code updated to ${NEW_SHA_SHORT} (${NEW_SHA})"
}

# Run a flask CLI command as the app user with venv activated + .env loaded.
run_flask() {
  as_app bash -c '
    set -euo pipefail
    cd "$1"
    shift
    venv_dir="$1"
    shift
    # shellcheck disable=SC1091
    . "${venv_dir}/bin/activate"
    set -a
    if [ -f .env ]; then
      # shellcheck disable=SC1091
      . ./.env
    fi
    set +a
    export FLASK_APP="${FLASK_APP:-run.py}"
    exec flask "$@"
  ' bash "$APP_DIR" "$VENV_DIR" "$@"
}

capture_db_revision() {
  # Best-effort parse of `flask db current` (e.g. "h5c8d0e2f4a7 (head)")
  local output
  output="$(run_flask db current 2>/dev/null || true)"
  PREV_DB_REV="$(printf '%s\n' "$output" | awk '/^[0-9a-fA-F]/ { print $1; exit }')"
  if [[ -n "$PREV_DB_REV" ]]; then
    log "Pre-deploy database revision: ${PREV_DB_REV}"
  else
    log "WARNING: Could not determine current Alembic revision (will skip downgrade on failure)"
  fi
}

run_migrations() {
  log "Running database migrations..."
  capture_db_revision

  if ! run_flask db upgrade; then
    log "Database migration failed."
    log "Rolling back deployment."
    rollback_migration_failure
    return 1
  fi

  log "Database migrations completed successfully."
  return 0
}

# Migration failure: restore DB (while new revision files still present), then
# restore git. Do NOT restart Gunicorn — leave the running process on old code.
rollback_migration_failure() {
  if [[ -n "${PREV_DB_REV:-}" ]]; then
    log "Restoring previous migration state to ${PREV_DB_REV}"
    if run_flask db downgrade "$PREV_DB_REV"; then
      log "Database revision restored to ${PREV_DB_REV}"
    else
      log "WARNING: Could not restore database revision to ${PREV_DB_REV} — manual DB check required"
    fi
  else
    log "WARNING: Previous DB revision unknown — skipped alembic downgrade"
  fi

  log "Restoring previous commit ${PREV_SHA} (service not restarted)"
  as_app git -C "$APP_DIR" reset --hard "$PREV_SHA"
  echo "rollback_status=migration_failed" >>"${GITHUB_OUTPUT:-/dev/null}" 2>/dev/null || true
}

restart_service() {
  log "Restarting ${SERVICE_NAME}.service"
  if ! svc restart "$SERVICE_NAME"; then
    log "systemctl restart ${SERVICE_NAME} failed"
    return 1
  fi
  log "Waiting ${STARTUP_WAIT_SECONDS}s for service startup"
  sleep "$STARTUP_WAIT_SECONDS"
  return 0
}

soft_health_checks() {
  local path code
  svc is-active --quiet "$SERVICE_NAME" || return 1
  pgrep -u "$APP_USER" -f "gunicorn" >/dev/null 2>&1 || return 1
  for path in "${HEALTH_PATHS[@]}"; do
    code="$(curl -sS -o /dev/null -w '%{http_code}' \
      --connect-timeout 5 --max-time 20 \
      "${HEALTH_BASE_URL}${path}" || true)"
    [[ "$code" == "200" ]] || return 1
  done
  return 0
}

wait_for_healthy() {
  local attempt
  for attempt in $(seq 1 "$HEALTH_RETRIES"); do
    log "Health check attempt ${attempt}/${HEALTH_RETRIES}"
    if soft_health_checks; then
      for path in "${HEALTH_PATHS[@]}"; do
        log "Health OK ${path} -> HTTP 200"
      done
      log "All health checks passed"
      return 0
    fi
    log "Not healthy yet; waiting ${HEALTH_RETRY_DELAY}s"
    sleep "$HEALTH_RETRY_DELAY"
  done
  log "Health checks exhausted — collecting diagnostics"
  svc status "$SERVICE_NAME" --no-pager -l || true
  if [[ "$(id -un)" == "root" ]]; then
    journalctl -u "$SERVICE_NAME" -n 80 --no-pager || true
  else
    sudo journalctl -u "$SERVICE_NAME" -n 80 --no-pager || true
  fi
  return 1
}

rollback() {
  local reason="${1:-unknown failure}"
  log "ROLLBACK START — reason: ${reason}"
  log "Restoring previous commit ${PREV_SHA}"
  as_app git -C "$APP_DIR" reset --hard "$PREV_SHA"
  # Schema may already be upgraded; that is usually safe for older code.
  # If a pre-upgrade revision was captured, attempt downgrade with restored code.
  if [[ -n "${PREV_DB_REV:-}" ]]; then
    log "Attempting database downgrade to ${PREV_DB_REV} during rollback"
    run_flask db downgrade "$PREV_DB_REV" || log "WARNING: DB downgrade to ${PREV_DB_REV} failed during rollback"
  fi
  restart_service
  if soft_health_checks; then
    log "ROLLBACK COMPLETED — site restored to ${PREV_SHA}"
    echo "rollback_status=completed" >>"${GITHUB_OUTPUT:-/dev/null}" 2>/dev/null || true
    return 0
  fi
  log "ROLLBACK HEALTH CHECK FAILED — manual intervention required"
  echo "rollback_status=failed" >>"${GITHUB_OUTPUT:-/dev/null}" 2>/dev/null || true
  return 1
}

main() {
  local started
  started="$(date +%s)"
  log "=== MWPP deployment started ==="
  log "Host=$(hostname) User=$(id -un) AppDir=${APP_DIR} AppUser=${APP_USER} Branch=${GIT_BRANCH}"
  log "Venv=${VENV_DIR} Flask=${FLASK_BIN}"

  require_cmd git
  require_cmd curl
  require_cmd flock
  require_cmd systemctl
  require_cmd pgrep

  acquire_lock
  ensure_layout
  backup_commit

  if ! pull_latest; then
    fail "git pull failed — no migrations or service restart performed"
  fi

  if [[ "$NEW_SHA" == "$PREV_SHA" ]]; then
    log "Already up to date (${NEW_SHA_SHORT}). Continuing with migrations + restart for consistency."
  fi

  if ! run_migrations; then
    fail "Deployment failed during database migrations; service was not restarted"
  fi

  if ! restart_service; then
    if ! rollback "service restart failed"; then
      fail "Deployment failed during service restart; rollback also failed"
    fi
    fail "Deployment failed during service restart; rollback completed"
  fi

  if ! wait_for_healthy; then
    if ! rollback "post-deploy health checks failed"; then
      fail "Deployment failed health checks; rollback also failed"
    fi
    fail "Deployment failed health checks; rollback completed"
  fi

  local ended duration
  ended="$(date +%s)"
  duration=$((ended - started))
  log "=== DEPLOYMENT SUCCESSFUL ==="
  log "Previous: ${PREV_SHA_SHORT}"
  log "Current:  ${NEW_SHA_SHORT}"
  log "Duration: ${duration}s"
}

main "$@"
