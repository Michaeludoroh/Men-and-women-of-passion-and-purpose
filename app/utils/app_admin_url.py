"""External URL for the separate WOPP App Admin (admin.woppandmopp.com)."""

from flask import current_app, request


def app_admin_url():
    """Return the App Admin base URL — a separate system, not this Flask app."""
    configured = (current_app.config.get("APP_ADMIN_URL") or "").strip().rstrip("/")
    if configured:
        return configured
    return "https://admin.woppandmopp.com"
