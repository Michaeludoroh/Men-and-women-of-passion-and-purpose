import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "site.db")


def _database_uri(default_sqlite=True):
    """Resolve database URI with PostgreSQL compatibility."""
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    if default_sqlite:
        return f"sqlite:///{DB_PATH}"
    return None


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@ministry.org")

    PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")
    FLUTTERWAVE_SECRET_KEY = os.environ.get("FLUTTERWAVE_SECRET_KEY", "")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    GALLERY_PER_PAGE = int(os.environ.get("GALLERY_PER_PAGE", 12))
    GALLERY_PER_PAGE_OPTIONS = (6, 12, 24, 36)

    MINISTRY_NAME = "Men and Women of Passion and Purpose"
    MINISTRY_TAGLINE = (
        "Raising purpose-driven believers through fire-filled worship, "
        "prophetic Word, prayer, and kingdom impact worldwide."
    )
    MINISTRY_EMAIL = os.environ.get(
        "MINISTRY_EMAIL", "womenofpassionandpurpose2024@gmail.com"
    )
    MINISTRY_PHONE = os.environ.get("MINISTRY_PHONE", "")
    MINISTRY_ADDRESS = os.environ.get("MINISTRY_ADDRESS", "")
    MINISTRY_MISSION = (
        "To build, empower, and establish men and women through the unfiltered Word of God, "
        "help them discover God-ordained purpose, and activate grace through discipleship, "
        "prayer, and kingdom advancement."
    )
    MINISTRY_VISION = (
        "To raise a community of confident, valued, and impactful men and women who will "
        "fill their space and take their place in life through the Word of God, prayer, and purpose."
    )

    APP_STORE_URL = os.environ.get("APP_STORE_URL", "")
    PLAY_STORE_URL = os.environ.get("PLAY_STORE_URL", "")
    API_KEY = os.environ.get("API_KEY", "")

    SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "")

    # External WOPP App Admin URL (separate system at admin.woppandmopp.com)
    APP_ADMIN_URL = os.environ.get("APP_ADMIN_URL", "").rstrip("/")


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    @classmethod
    def validate(cls):
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY environment variable is required in production."
            )
        if not _database_uri(default_sqlite=False):
            raise RuntimeError(
                "DATABASE_URL environment variable is required in production."
            )
        if not os.environ.get("API_KEY"):
            raise RuntimeError(
                "API_KEY environment variable is required in production."
            )
        if not os.environ.get("SITE_URL"):
            raise RuntimeError(
                "SITE_URL environment variable is required in production."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config_name():
    return os.environ.get("FLASK_ENV", os.environ.get("FLASK_CONFIG", "development"))
