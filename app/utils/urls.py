from flask import current_app, request, url_for


def get_allowed_origins():
    raw = current_app.config.get("ALLOWED_ORIGINS") or ""
    if isinstance(raw, (list, tuple)):
        return [str(origin).strip() for origin in raw if str(origin).strip()]
    return [origin.strip() for origin in str(raw).split(",") if origin.strip()]


def cors_allow_origin():
    origin = request.headers.get("Origin")
    if not origin:
        return None
    if origin in get_allowed_origins():
        return origin
    return None


def external_route(endpoint, **values):
    site = (current_app.config.get("SITE_URL") or "").strip().rstrip("/")
    base_url = f"{site}/" if site else "http://localhost/"
    with current_app.test_request_context(base_url=base_url):
        path = url_for(endpoint, **values)
    if site:
        return f"{site}{path}"
    return url_for(endpoint, _external=True, **values)
