"""Shared utilities for production-safe admin bootstrap scripts."""
import getpass
import inspect
import os
import re
import sys

from email_validator import EmailNotValidError, validate_email

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ADMIN_ROUTES_PATH = os.path.join(PROJECT_ROOT, "app", "routes", "admin_routes.py")

MIN_PASSWORD_LENGTH = 6
MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 255


def load_env_file():
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def mask_database_uri(uri):
    if not uri:
        return "unknown"
    return re.sub(r"://([^:/]+):([^@]+)@", r"://\1:***@", uri)


def detect_admin_role():
    with open(ADMIN_ROUTES_PATH, encoding="utf-8") as admin_routes:
        source = admin_routes.read()

    promote_match = re.search(r'user\.role\s*=\s*["\']([^"\']+)["\']', source)
    guard_match = re.search(r'current_user\.role\s*!=\s*["\']([^"\']+)["\']', source)

    if promote_match and guard_match and promote_match.group(1) == guard_match.group(1):
        return promote_match.group(1)
    if guard_match:
        return guard_match.group(1)
    if promote_match:
        return promote_match.group(1)
    return "admin"


def detect_user_model():
    import app.models as models_module

    candidates = []
    for _, obj in inspect.getmembers(models_module, inspect.isclass):
        if getattr(obj, "__module__", "") != models_module.__name__:
            continue
        if not all(hasattr(obj, attr) for attr in ("set_password", "role", "email", "name")):
            continue
        candidates.append(obj)

    if not candidates:
        raise RuntimeError("Could not detect a User model in app.models.")

    for obj in candidates:
        if obj.__name__ == "User":
            return obj

    if len(candidates) == 1:
        return candidates[0]

    raise RuntimeError("Multiple user-like models found; expected a single User model.")


def bootstrap():
    load_env_file()
    os.environ.setdefault("FLASK_APP", "run.py")

    from app import create_app
    from app.extensions import db

    app = create_app()
    user_model = detect_user_model()
    admin_role = detect_admin_role()
    return app, db, user_model, admin_role


def print_context(user_model, admin_role, database_uri):
    print(f"Detected User model: {user_model.__name__}")
    print(f"Detected admin role: {admin_role}")
    print(f"Database: {mask_database_uri(database_uri)}")
    print()


def validate_email_address(email):
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(f"Email must be {MAX_EMAIL_LENGTH} characters or fewer.")
    try:
        result = validate_email(email, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc
    return result.normalized.lower()


def validate_password(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )


def validate_name(name):
    name = name.strip()
    if len(name) < 2:
        raise ValueError("Name must be at least 2 characters.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer.")
    return name


def prompt_required(label):
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(f"  {label} is required.")


def prompt_name():
    while True:
        try:
            return validate_name(prompt_required("Name"))
        except ValueError as exc:
            print(f"  {exc}")


def prompt_email():
    while True:
        try:
            return validate_email_address(prompt_required("Email"))
        except ValueError as exc:
            print(f"  Invalid email: {exc}")


def prompt_password(label="Password"):
    while True:
        password = getpass.getpass(f"{label}: ")
        confirm = getpass.getpass("Confirm password: ")
        if not password:
            print("  Password is required.")
            continue
        if password != confirm:
            print("  Passwords do not match. Try again.")
            continue
        try:
            validate_password(password)
        except ValueError as exc:
            print(f"  {exc}")
            continue
        return password


def setup_or_exit():
    try:
        app, db, user_model, admin_role = bootstrap()
    except Exception as exc:
        print(f"FAIL: Setup error — {exc}")
        sys.exit(1)

    print_context(
        user_model,
        admin_role,
        app.config.get("SQLALCHEMY_DATABASE_URI", "unknown"),
    )
    return app, db, user_model, admin_role
