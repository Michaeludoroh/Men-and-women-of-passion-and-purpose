#!/usr/bin/env bash
# Pre-deployment validation for MWPP (runs on GitHub Actions runner).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

log() { printf '[validate] %s\n' "$*"; }
fail() { printf '[validate] ERROR: %s\n' "$*" >&2; exit 1; }

log "Repository root: $ROOT"

# --- Integrity ---
[[ -f run.py ]] || fail "Missing run.py"
[[ -f gunicorn.conf.py ]] || fail "Missing gunicorn.conf.py"
[[ -f requirements.txt ]] || fail "Missing requirements.txt"
[[ -d app ]] || fail "Missing app/"
[[ -f app/__init__.py ]] || fail "Missing app/__init__.py"
[[ -f scripts/deploy/remote_deploy.sh ]] || fail "Missing remote_deploy.sh"
log "Repository integrity OK"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  fail "python3/python not available"
fi

# --- Workflow YAML present ---
[[ -f .github/workflows/deploy.yml ]] || fail "Missing .github/workflows/deploy.yml"
"$PYTHON" - <<'PY'
import pathlib, sys
try:
    import yaml  # type: ignore
except ImportError:
    # Fallback: basic structural checks without PyYAML
    text = pathlib.Path(".github/workflows/deploy.yml").read_text(encoding="utf-8")
    required = ["name:", "on:", "jobs:", "deploy:", "VPS_HOST", "VPS_SSH_KEY"]
    missing = [r for r in required if r not in text]
    if missing:
        print("YAML structural check failed; missing:", ", ".join(missing))
        sys.exit(1)
    print("YAML structural check OK (PyYAML not installed)")
else:
    data = yaml.safe_load(pathlib.Path(".github/workflows/deploy.yml").read_text(encoding="utf-8"))
    assert data and "jobs" in data, "workflow missing jobs"
    print("YAML parse OK")
PY

# --- Python syntax ---
log "Running Python compileall"
"$PYTHON" -m compileall -q app run.py config.py gunicorn.conf.py wsgi.py \
  || fail "Python syntax check failed"
log "Python syntax OK"

# --- Critical templates exist ---
for t in \
  app/templates/base.html \
  app/templates/index.html \
  app/templates/giving.html \
  app/templates/partnership.html \
  app/templates/leadership.html
do
  [[ -f "$t" ]] || fail "Missing template: $t"
done
log "Critical templates present"

# --- Jinja brace balance (lightweight) ---
"$PYTHON" - <<'PY'
from pathlib import Path
errors = []
for path in Path("app/templates").rglob("*.html"):
    text = path.read_text(encoding="utf-8", errors="replace")
    # Ignore raw blocks roughly; still a useful smoke check
    if text.count("{%") != text.count("%}"):
        errors.append(f"{path}: mismatched {{% %}}")
    if text.count("{{") != text.count("}}"):
        errors.append(f"{path}: mismatched {{{{ }}}}")
if errors:
    print("\n".join(errors[:20]))
    raise SystemExit(1)
print(f"Template delimiter balance OK ({sum(1 for _ in Path('app/templates').rglob('*.html'))} files)")
PY

# --- CSS present ---
[[ -f app/static/css/styles.css ]] || fail "Missing styles.css"
[[ -f app/static/css/partnership.css ]] || fail "Missing partnership.css"
log "CSS assets present"

# --- Remote script shell syntax (if bash available) ---
if command -v bash >/dev/null 2>&1; then
  bash -n scripts/deploy/remote_deploy.sh || fail "remote_deploy.sh syntax error"
  log "remote_deploy.sh syntax OK"
fi

log "All pre-deployment checks passed"
