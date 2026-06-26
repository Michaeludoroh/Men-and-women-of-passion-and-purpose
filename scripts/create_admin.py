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
            print(f"\nUser with email '{email}' already exists. No changes made.")
            sys.exit(0)

        user = user_model(name=name, email=email, role=admin_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"\nSUCCESS: Admin account created for '{email}' with role '{admin_role}'.")


if __name__ == "__main__":
    main()
