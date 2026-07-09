"""Ministry social media links — single source of truth with URL validation."""
from urllib.parse import urlparse

SOCIAL_LINKS = [
    {
        "key": "facebook",
        "label": "Facebook — Men and Women of Passion and Purpose",
        "url": "https://www.facebook.com/share/18GWq4xT8s/?mibextid=wwXIfr",
        "icon": "fab fa-facebook-f",
    },
    {
        "key": "instagram",
        "label": "Instagram — Men and Women of Passion and Purpose",
        "username": "@menandwomenofpassionandpurpose",
        "url": "https://www.instagram.com/menandwomenofpassionandpurpose",
        "icon": "fab fa-instagram",
    },
    {
        "key": "youtube",
        "label": "YouTube — Women of Passion and Purpose (@womenofpassionandpurpose)",
        "display_name": "@womenofpassionandpurpose",
        "handle": "@womenofpassionandpurpose",
        "url": "https://www.youtube.com/@womenofpassionandpurpose",
        "icon": "fab fa-youtube",
    },
    {
        "key": "tiktok",
        "label": "TikTok — MOPP and WOPP (@moppandwopp)",
        "username": "@moppandwopp",
        "url": "https://www.tiktok.com/@moppandwopp",
        "icon": "fab fa-tiktok",
    },
]

CONTACT_ICON_BACKGROUNDS = (
    "var(--purple-primary)",
    "var(--gold-primary)",
    "var(--purple-dark)",
    "linear-gradient(135deg, var(--gold-primary), var(--gold-secondary))",
)


def validate_external_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Social link must use http or https: {url}")
    if not parsed.netloc:
        raise ValueError(f"Social link must include a valid host: {url}")
    return url


def get_social_links():
    links = []
    for item in SOCIAL_LINKS:
        entry = dict(item)
        entry["url"] = validate_external_url(item["url"])
        links.append(entry)
    return links


def get_social_dict():
    return {link["key"]: link["url"] for link in get_social_links()}


def get_sermon_watch_url():
    """Prefer YouTube for full sermons; fall back to Facebook if configured."""
    links = {link["key"]: link["url"] for link in get_social_links()}
    return links.get("youtube") or links.get("facebook") or ""


# Validate all configured links at import time.
for _social in SOCIAL_LINKS:
    validate_external_url(_social["url"])
