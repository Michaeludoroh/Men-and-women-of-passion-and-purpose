#!/usr/bin/env bash
# =============================================================================
# Remote production deploy for Men and Women of Passion and Purpose
# Runs on the VPS (invoked by GitHub Actions over SSH).
#
# Automates the existing manual flow:
#   cd /home/ubuntu/Men-and-women-of-passion-and-purpose
#   git pull && sudo systemctl restart mwpp
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

# Paths checked after restart (must return HTTP 200)
HEALTH_PATHS=(
  "/"
  "/partnership/"
  "/giving/"
  "/leadership"
)

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
  [[ -d "$APP_DIR/.venv" ]] || log "WARNING: virtualenv not found at ${APP_DIR}/.venv (service may still manage it)"
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

  require_cmd git
  require_cmd curl
  require_cmd flock
  require_cmd systemctl
  require_cmd pgrep

  acquire_lock
  ensure_layout
  backup_commit

  if ! pull_latest; then
    fail "git pull failed — no service restart performed"
  fi

  if [[ "$NEW_SHA" == "$PREV_SHA" ]]; then
    log "Already up to date (${NEW_SHA_SHORT}). Restarting service for consistency."
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
