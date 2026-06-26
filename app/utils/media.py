import os
from urllib.parse import quote
from flask import current_app, url_for

# Canonical static asset paths
LOGO_PATH = "images/logo.png"
FAVICON_PATH = "images/favicon.png"
APPLE_TOUCH_ICON_PATH = "images/apple-touch-icon.png"
FAVICON_16_PATH = "images/favicon-16.png"
SERMON_PLACEHOLDER = "images/sermon-placeholder.jpg"
LEADER_PLACEHOLDER = "images/leader-placeholder.jpg"
OG_SHARE_IMAGE = "images/og-share.png"
QR_PLACEHOLDER = "images/app/qr-placeholder.png"

APP_SCREENSHOTS = [
    "images/app/screenshot-1.png",
    "images/app/screenshot-2.png",
    "images/app/screenshot-3.png",
]

APP_FEATURES = [
    {"icon": "fa-bullhorn", "title": "Announcements", "description": "Stay updated with ministry news and prophetic releases."},
    {"icon": "fa-calendar-alt", "title": "Events", "description": "Never miss conferences, prayer nights, and empowerment gatherings."},
    {"icon": "fa-play-circle", "title": "Sermons", "description": "Watch fire-filled messages on demand, anywhere."},
    {"icon": "fa-hands-praying", "title": "Prayer Requests", "description": "Submit prayer needs and join the global prayerline."},
    {"icon": "fa-users", "title": "Community Engagement", "description": "Connect with believers and grow in fellowship."},
    {"icon": "fa-bolt", "title": "Empowerment Programs", "description": "Access empowerment initiatives and kingdom resources."},
    {"icon": "fa-chalkboard-teacher", "title": "Mentorship Classes", "description": "Join mentorship classes and grow in purpose-driven leadership."},
    {"icon": "fa-book-open", "title": "Digital Library", "description": "Browse sermons, teachings, and spiritual resources on demand."},
]

def _static_path(filename):
    return os.path.join(current_app.static_folder, filename.replace("/", os.sep))


def asset_exists(filename):
    return os.path.isfile(_static_path(filename))


def asset_url(filename, fallback=None):
    if asset_exists(filename):
        return url_for("static", filename=filename)
    if fallback and asset_exists(fallback):
        return url_for("static", filename=fallback)
    return url_for("static", filename=filename)


def logo_url():
    return asset_url(LOGO_PATH)


def favicon_url():
    return asset_url(FAVICON_PATH, fallback=LOGO_PATH)


def apple_touch_icon_url():
    return asset_url(APPLE_TOUCH_ICON_PATH, fallback=LOGO_PATH)


def favicon_16_url():
    return asset_url(FAVICON_16_PATH, fallback=FAVICON_PATH)


def sermon_placeholder_url():
    return asset_url(SERMON_PLACEHOLDER)


def leader_placeholder_url():
    return asset_url(LEADER_PLACEHOLDER)


def og_image_url():
    filename = OG_SHARE_IMAGE if asset_exists(OG_SHARE_IMAGE) else LOGO_PATH
    path = url_for("static", filename=filename)
    site = (current_app.config.get("SITE_URL") or "").strip().rstrip("/")
    if site:
        return f"{site}{path}"
    return url_for("static", filename=filename, _external=True)


def app_screenshots():
    return [asset_url(s) for s in APP_SCREENSHOTS]


def qr_placeholder_url():
    return asset_url(QR_PLACEHOLDER)


def app_page_url():
    from .urls import external_route

    return external_route("main.app_download")


def app_qr_code_url():
    """QR code image URL encoding the WOP App download page."""
    page_url = app_page_url()
    return (
        "https://api.qrserver.com/v1/create-qr-code/?size=256x256&margin=10&data="
        + quote(page_url, safe="")
    )
