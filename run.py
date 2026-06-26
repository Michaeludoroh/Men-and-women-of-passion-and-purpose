import os

from app import create_app
from app.extensions import db
from app.services.seed import seed_default_leaders

app = create_app()


def init_dev_database():
    """Development-only schema bootstrap. Production uses Alembic migrations."""
    with app.app_context():
        db.create_all()
        seed_default_leaders()


if __name__ == "__main__":
    if app.config.get("DEBUG") or os.environ.get("FLASK_ENV", "development") != "production":
        init_dev_database()
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))
