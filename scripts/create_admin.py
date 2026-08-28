#!/usr/bin/env python3
"""Create the first admin user for Men and Women of Passion and Purpose."""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from admin_bootstrap import prompt_email, prompt_name, prompt_password, setup_or_exit


def main():
    app, db, user_model, admin_role = setup_or_exit()

    name = prompt_name()
    email = prompt_email()
    password = prompt_password()

    with app.app_context():
        existing = user_model.query.filter_by(email=email).first()
        if existing:
            current_role = getattr(existing, "role", None) or "member"
            print(f"\nUser with email '{email}' already exists (role: '{current_role}').")
            if current_role == admin_role:
                print("No changes made. To change the password, run scripts/reset_admin_password.py")
                sys.exit(0)

            confirm = input("Promote this account to admin and set the password you just entered? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("No changes made.")
                sys.exit(0)

            existing.role = admin_role
            existing.set_password(password)
            if name and getattr(existing, "name", None) != name:
                existing.name = name
            db.session.commit()
            print(f"\nSUCCESS: '{email}' promoted to '{admin_role}' and password updated.")
            sys.exit(0)

        user = user_model(name=name, email=email, role=admin_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"\nSUCCESS: Admin account created for '{email}' with role '{admin_role}'.")


if __name__ == "__main__":
    main()
