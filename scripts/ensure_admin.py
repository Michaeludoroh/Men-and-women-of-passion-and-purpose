#!/usr/bin/env python3
"""Create or update a website admin account (non-interactive).

Usage (from ministry_project / production app root):

    python scripts/ensure_admin.py --email you@example.com --name "Ministry Admin"
    python scripts/ensure_admin.py --email you@example.com --password '...' --name "Ministry Admin"

If --password is omitted, you will be prompted. This writes to the database
configured by .env / DATABASE_URL (the live site when run on the VPS).
"""
import argparse
import getpass
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from admin_bootstrap import setup_or_exit, validate_email_address, validate_name, validate_password


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update a website admin user.")
    parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL", ""), help="Admin email")
    parser.add_argument("--name", default=os.environ.get("ADMIN_NAME", "Ministry Admin"), help="Admin display name")
    parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD", ""), help="Admin password")
    return parser.parse_args()


def main():
    args = parse_args()
    app, db, user_model, admin_role = setup_or_exit()

    email_raw = (args.email or "").strip()
    if not email_raw:
        print("FAIL: Provide --email or ADMIN_EMAIL.")
        sys.exit(1)

    try:
        email = validate_email_address(email_raw)
        name = validate_name(args.name)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("FAIL: Passwords do not match.")
            sys.exit(1)

    try:
        validate_password(password)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)

    with app.app_context():
        user = user_model.query.filter_by(email=email).first()
        if user:
            user.name = name
            user.role = admin_role
            user.set_password(password)
            db.session.commit()
            print(f"SUCCESS: Updated existing user '{email}' to role '{admin_role}' and set a new password.")
        else:
            user = user_model(name=name, email=email, role=admin_role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"SUCCESS: Created admin '{email}' with role '{admin_role}'.")


if __name__ == "__main__":
    main()
