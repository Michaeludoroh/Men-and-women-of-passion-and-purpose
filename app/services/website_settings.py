"""Load website content from DB with config.py fallbacks."""

from flask import current_app

from ..models import WebsiteSettings


def _config_or(value, key, default=""):
    if value and str(value).strip():
        return str(value).strip()
    return (current_app.config.get(key) or default).strip()


def get_website_settings_row():
    return WebsiteSettings.get_singleton()


def get_ministry_context():
    """Merged ministry dict for templates (DB overrides env defaults)."""
    settings = get_website_settings_row()
    config = current_app.config
    return {
        "MINISTRY_NAME": config.get("MINISTRY_NAME", ""),
        "MINISTRY_TAGLINE": _config_or(settings.tagline, "MINISTRY_TAGLINE"),
        "MINISTRY_MISSION": _config_or(settings.mission, "MINISTRY_MISSION"),
        "MINISTRY_VISION": _config_or(settings.vision, "MINISTRY_VISION"),
        "MINISTRY_EMAIL": _config_or(settings.ministry_email, "MINISTRY_EMAIL"),
        "MINISTRY_PHONE": _config_or(settings.ministry_phone, "MINISTRY_PHONE"),
        "MINISTRY_ADDRESS": _config_or(settings.ministry_address, "MINISTRY_ADDRESS"),
        "APP_STORE_URL": _config_or(settings.app_store_url, "APP_STORE_URL"),
        "PLAY_STORE_URL": _config_or(settings.play_store_url, "PLAY_STORE_URL"),
    }


def get_about_intro():
    settings = get_website_settings_row()
    if settings.about_intro and settings.about_intro.strip():
        return settings.about_intro.strip()
    return (
        "A Christ-centered community raising believers who live intentionally, "
        "lead boldly, and serve sacrificially through the Word, prayer, and purpose."
    )


def mission_bullets():
    """Mission lines for About page (one bullet per line in admin)."""
    mission = get_ministry_context()["MINISTRY_MISSION"]
    lines = [line.strip() for line in mission.replace("\r", "").split("\n") if line.strip()]
    if len(lines) > 1:
        return lines
    if mission:
        return [mission]
    return [
        "To build, empower, and establish men & women through the unfiltered Word of God.",
        "To help discover God-ordained purpose and ignite passion for destiny fulfillment.",
        "To activate grace through discipleship, prayer, and kingdom advancement.",
    ]
