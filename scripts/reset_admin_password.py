#!/usr/bin/env python3
"""Reset password for an existing admin account."""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from admin_bootstrap import (
    prompt_email,
    prompt_password,
    setup_or_exit,
    validate_email_address,
)


def main():
    app, db, user_model, admin_role = setup_or_exit()

    while True:
        raw_email = input("Admin email: ").strip()
        if not raw_email:
            print("  Admin email is required.")
            continue
        try:
            email = validate_email_address(raw_email)
            break
        except ValueError as exc:
            print(f"  Invalid email: {exc}")

    password = prompt_password("New password")

    with app.app_context():
        user = user_model.query.filter_by(email=email).first()
        if not user:
            print(f"\nFAIL: No user found with email '{email}'.")
            sys.exit(1)

        if user.role != admin_role:
            print(
                f"\nFAIL: User '{email}' exists but does not have admin role "
                f"('{admin_role}'). Current role: '{user.role}'."
            )
            sys.exit(1)

        user.set_password(password)
        db.session.commit()

        print(f"\nSUCCESS: Password updated for admin '{email}'.")


if __name__ == "__main__":
    main()
