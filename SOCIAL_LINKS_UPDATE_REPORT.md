# Social Links Update Report

**Project:** Men and Women of Passion and Purpose (MWPP)  
**Date:** June 25, 2026  
**Scope:** TikTok and YouTube official account URLs only

---

## Summary

TikTok and YouTube links were updated site-wide via the single source of truth in `app/utils/social.py`. Because footer, contact, about, mobile menu, homepage, and API all consume `get_social_links()` / `get_social_dict()`, **one configuration change propagates everywhere** automatically.

Facebook and Instagram were **not modified**.

---

## Old URLs Replaced

| Platform | Old URL | Old display |
|----------|---------|-------------|
| **TikTok** | `https://www.tiktok.com/@womenofpassionandpurpose` | `@womenofpassionandpurpose` |
| **YouTube** | `https://www.youtube.com/@moppandwopp` | `MOPP and WOPP` / `@moppandwopp` |

---

## New Official URLs

| Platform | New URL | New display |
|----------|---------|-------------|
| **TikTok** | `https://www.tiktok.com/@moppandwopp` | `@moppandwopp` |
| **YouTube** | `https://www.youtube.com/@womenofpassionandpurpose` | `@womenofpassionandpurpose` |

---

## Files Modified

| File | Change |
|------|--------|
| `app/utils/social.py` | Updated TikTok and YouTube URLs, labels, usernames, handles, and display names |
| `scripts/audit_social_media.py` | Updated expected URLs, API expectations, and forbidden patterns for retired accounts |

### Files verified unchanged (consume central config)

These locations inherit links automatically — no hardcoded TikTok/YouTube URLs found:

| Location | Template / module |
|----------|-------------------|
| Footer | `app/templates/base.html` → `includes/social_links.html` |
| Mobile menu | `app/templates/base.html` → `includes/social_links.html` (compact) |
| Contact page | `app/templates/contact.html` → `includes/social_links.html` |
| About page | `app/templates/about.html` → `includes/social_links.html` |
| Home page | `app/templates/index.html` → `includes/social_links.html` |
| Social partial | `app/templates/includes/social_links.html` |
| SVG icons | `app/templates/includes/social_icon_svg.html` (platform keys unchanged) |
| Context injection | `app/__init__.py` |
| API | `app/routes/api_routes.py` → `get_social_dict()` |

---

## Exact Fix Applied

### `app/utils/social.py`

**YouTube** — before:
```python
"label": "YouTube — MOPP and WOPP (@moppandwopp)",
"display_name": "MOPP and WOPP",
"handle": "@moppandwopp",
"url": "https://www.youtube.com/@moppandwopp",
```

**YouTube** — after:
```python
"label": "YouTube — Women of Passion and Purpose (@womenofpassionandpurpose)",
"display_name": "@womenofpassionandpurpose",
"handle": "@womenofpassionandpurpose",
"url": "https://www.youtube.com/@womenofpassionandpurpose",
```

**TikTok** — before:
```python
"label": "TikTok — Women of Passion and Purpose (@womenofpassionandpurpose)",
"username": "@womenofpassionandpurpose",
"url": "https://www.tiktok.com/@womenofpassionandpurpose",
```

**TikTok** — after:
```python
"label": "TikTok — MOPP and WOPP (@moppandwopp)",
"username": "@moppandwopp",
"url": "https://www.tiktok.com/@moppandwopp",
```

---

## Preserved Behavior

| Requirement | Status |
|-------------|--------|
| `target="_blank"` on all social links | **Preserved** — `social_links.html` |
| `rel="noopener noreferrer"` | **Preserved** — `social_links.html` |
| SVG icon styling (gold footer, hover animations) | **Unchanged** — CSS and SVG partial untouched |
| Facebook link | **Unchanged** |
| Instagram link | **Unchanged** |
| Platform icons (TikTok/YouTube SVG) | **Unchanged** — still correct platforms |

---

## Verification Results

### Application code scan

Searched all `.py`, `.html`, `.js`, `.css`, `.json`, `.yaml` files:

| Pattern | In application code |
|---------|---------------------|
| `tiktok.com/@womenofpassionandpurpose` (old) | **Not found** |
| `youtube.com/@moppandwopp` (old) | **Not found** |
| `tiktok.com/@moppandwopp` (new) | **Found** — `app/utils/social.py` |
| `youtube.com/@womenofpassionandpurpose` (new) | **Found** — `app/utils/social.py` |

Retired URLs are listed only as **forbidden patterns** in `scripts/audit_social_media.py` (to prevent regression).

### Automated verification

```
VERIFICATION PASS
TikTok: https://www.tiktok.com/@moppandwopp
YouTube: https://www.youtube.com/@womenofpassionandpurpose
```

Checks performed:
- `get_social_dict()` returns new TikTok and YouTube URLs
- Display usernames: TikTok `@moppandwopp`, YouTube `@womenofpassionandpurpose`
- Rendered `/about` and `/contact` HTML contain new URLs
- Rendered pages do **not** contain old TikTok or YouTube URLs
- `target="_blank"` and `noopener noreferrer` present on social anchors
- API `GET /api/v1/ministry` → `data.social.tiktok` and `data.social.youtube` match new URLs

### Pages affected (via shared templates)

| Page | TikTok | YouTube |
|------|--------|---------|
| Footer (all pages) | New URL | New URL |
| About — Connect With Us | New URL + `@moppandwopp` label | New URL + `@womenofpassionandpurpose` label |
| Contact — Follow Us | New URL | New URL |
| Home — Connect With Us | New URL | New URL |
| Mobile nav (compact) | New URL | New URL |
| API `/api/v1/ministry` | New URL | New URL |

---

## Confirmation

**Every TikTok link** across the ministry website now points to:

`https://www.tiktok.com/@moppandwopp`

**Every YouTube link** across the ministry website now points to:

`https://www.youtube.com/@womenofpassionandpurpose`

No other social platforms were modified.

---

## Note on historical documentation

Older reports (`SOCIAL_MEDIA_AUDIT_REPORT.md`, `SOCIAL_MEDIA_FIX_REPORT.md`) may still mention previous URLs as historical audit records. Application code and the audit script reflect the **current official accounts** only.
