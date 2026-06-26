#!/usr/bin/env python3
"""List all users in the application database."""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPTS_DIR)

from admin_bootstrap import setup_or_exit


def format_created_at(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def main():
    app, db, user_model, admin_role = setup_or_exit()

    with app.app_context():
        users = user_model.query.order_by(user_model.id.asc()).all()

        if not users:
            print("No users found.")
            sys.exit(0)

        rows = []
        for user in users:
            rows.append(
                (
                    str(user.id),
                    user.name,
                    user.email,
                    user.role,
                    format_created_at(getattr(user, "created_at", None)),
                )
            )

        headers = ("ID", "Name", "Email", "Role", "Created")
        widths = [len(header) for header in headers]
        for row in rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], len(str(cell)))

        def render_row(values):
            return "  ".join(str(value).ljust(widths[index]) for index, value in enumerate(values))

        print(render_row(headers))
        print(render_row("-" * width for width in widths))
        for row in rows:
            print(render_row(row))

        admin_count = sum(1 for user in users if user.role == admin_role)
        print()
        print(f"Total users: {len(users)} ({admin_count} admin)")


if __name__ == "__main__":
    main()
