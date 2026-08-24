from urllib.parse import urljoin, urlparse

from flask import request


def is_safe_redirect_url(target):
    """Allow only same-host relative or absolute redirect targets."""
    if not target:
        return False
    if target.startswith("//"):
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ("http", "https")
        and ref_url.netloc == test_url.netloc
    )


def is_website_admin_path(target):
    """True when the target is a Website Admin route on this Flask app."""
    if not target or not is_safe_redirect_url(target):
        return False
    path = urlparse(urljoin(request.host_url, target)).path or ""
    return path == "/admin" or path.startswith("/admin/")
