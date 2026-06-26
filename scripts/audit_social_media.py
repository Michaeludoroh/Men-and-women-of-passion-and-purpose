#!/usr/bin/env python3
"""Automated social media audit for MWPP ministry website."""
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("SECRET_KEY", "audit-secret")

FORBIDDEN_PATTERNS = [
    r"menandwomenofpassionandpurpose",
    r"@menandwomenofpassionandpurpose",
    r"tiktok\.com/@menandwomen",
    r"tiktok\.com/@womenofpassionandpurpose",
    r"youtube\.com/@menandwomen",
    r"youtube\.com/@moppandwopp",
    r"http://(www\.)?(tiktok|youtube|facebook)",
]

EXPECTED_URLS = {
    "https://www.tiktok.com/@moppandwopp",
    "https://www.facebook.com/share/18GWq4xT8s/?mibextid=wwXIfr",
    "https://www.instagram.com/menandwomenofpassionandpurpose",
    "https://www.youtube.com/@womenofpassionandpurpose",
}

SCAN_DIRS = [
    PROJECT_ROOT / "app" / "templates",
    PROJECT_ROOT / "app" / "routes",
    PROJECT_ROOT / "app" / "utils",
    PROJECT_ROOT / "app" / "static",
    PROJECT_ROOT / "app" / "__init__.py",
]


class SocialLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.social_anchors = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr = dict(attrs)
        href = attr.get("href", "")
        if not any(host in href for host in ("tiktok.com", "facebook.com", "youtube.com")):
            return
        self._current = {
            "href": href,
            "target": attr.get("target"),
            "rel": attr.get("rel"),
            "aria_label": attr.get("aria-label"),
        }

    def handle_endtag(self, tag):
        if tag == "a" and self._current:
            self.social_anchors.append(self._current)
            self._current = None


def scan_files():
    scanned = []
    issues = []
    for target in SCAN_DIRS:
        if target.is_file():
            paths = [target]
        else:
            paths = list(target.rglob("*"))
        for path in paths:
            if path.suffix not in {".html", ".py", ".js", ".css", ".md"}:
                continue
            if ".venv" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            scanned.append(str(path.relative_to(PROJECT_ROOT)))
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, text, re.I):
                    issues.append(f"Forbidden pattern `{pattern}` in {path.relative_to(PROJECT_ROOT)}")
    return scanned, issues


def audit_rendered_pages():
    from app import create_app

    app = create_app()
    client = app.test_client()
    pages = ["/", "/about", "/contact", "/events", "/gallery", "/app"]
    parser_issues = []
    all_anchors = []

    for path in pages:
        resp = client.get(path)
        if resp.status_code != 200:
            parser_issues.append(f"Page {path} returned {resp.status_code}")
            continue
        html = resp.data.decode()
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, html, re.I):
                parser_issues.append(f"Forbidden pattern `{pattern}` on rendered {path}")
        parser = SocialLinkParser()
        parser.feed(html)
        for anchor in parser.social_anchors:
            anchor["page"] = path
            all_anchors.append(anchor)
            if anchor["href"] not in EXPECTED_URLS:
                parser_issues.append(f"Unexpected social URL on {path}: {anchor['href']}")
            if anchor["target"] != "_blank":
                parser_issues.append(f"Missing target=_blank on {path}: {anchor['href']}")
            if not anchor["rel"] or "noopener" not in anchor["rel"] or "noreferrer" not in anchor["rel"]:
                parser_issues.append(f"Missing rel=noopener noreferrer on {path}: {anchor['href']}")
            if not anchor["aria_label"]:
                parser_issues.append(f"Missing aria-label on {path}: {anchor['href']}")
            if not anchor["href"].startswith("https://"):
                parser_issues.append(f"Non-HTTPS social link on {path}: {anchor['href']}")

    return parser_issues, all_anchors, pages


def audit_api():
    from app import create_app

    app = create_app()
    client = app.test_client()
    data = client.get("/api/v1/ministry").get_json()["data"]["social"]
    expected = {
        "tiktok": "https://www.tiktok.com/@moppandwopp",
        "facebook": "https://www.facebook.com/share/18GWq4xT8s/?mibextid=wwXIfr",
        "instagram": "https://www.instagram.com/menandwomenofpassionandpurpose",
        "youtube": "https://www.youtube.com/@womenofpassionandpurpose",
    }
    issues = []
    if data != expected:
        issues.append(f"API social mismatch: {data}")
    return issues, data


def audit_responsive_markup():
    css = (PROJECT_ROOT / "app" / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    template = (PROJECT_ROOT / "app" / "templates" / "includes" / "social_links.html").read_text(encoding="utf-8")
    checks = {
        "flex-wrap on social containers": "flex flex-wrap" in template,
        "about variant md:gap responsive": "md:gap-10" in template,
        "compact variant for mobile nav": "social-icon-btn--compact" in css,
        "footer variant styles": "social-icon-btn--footer" in css,
        "touch-friendly min size (2.5rem+)": "2.5rem" in css or "2.75rem" in css,
        "hover/focus transition": "social-icon-btn:hover" in css,
    }
    failed = [name for name, ok in checks.items() if not ok]
    return checks, failed


def main():
    scanned, file_issues = scan_files()
    render_issues, anchors, pages = audit_rendered_pages()
    api_issues, api_social = audit_api()
    responsive_checks, responsive_failures = audit_responsive_markup()

    all_issues = file_issues + render_issues + api_issues + responsive_failures
    print("SCANNED", len(scanned))
    print("ANCHORS", len(anchors))
    print("PAGES", len(pages))
    print("ISSUES", len(all_issues))
    for issue in all_issues:
        print("ISSUE:", issue)
    if not all_issues:
        print("AUDIT_PASSED")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
