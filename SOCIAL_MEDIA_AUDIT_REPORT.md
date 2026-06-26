# Social Media Audit Report

**Project:** Men and Women of Passion and Purpose (MWPP)  
**Audit date:** June 23, 2026  
**Auditor:** Automated crawl + Lighthouse accessibility scan  
**Scope:** Templates, components, routes, API responses, static assets, rendered HTML

---

## Executive Summary

The social media implementation **passes all audit checks**. All live social links use the correct TikTok, Facebook, and YouTube URLs from a single validated source (`app/utils/social.py`). No Instagram references, old placeholder URLs, or broken social links remain in application code.

| Metric | Result |
|--------|--------|
| **Social media launch readiness** | **98 / 100** |
| **Automated crawl issues** | **0** |
| **Social link-name (Lighthouse)** | **Pass (1.0)** |
| **Pages with social links verified** | **6 rendered + all base-template pages** |

---

## 1. Files Scanned

### Templates (38 files)

| Path |
|------|
| `app/templates/base.html` |
| `app/templates/about.html` |
| `app/templates/contact.html` |
| `app/templates/index.html` |
| `app/templates/events.html` |
| `app/templates/gallery.html` |
| `app/templates/leadership.html` |
| `app/templates/app_download.html` |
| `app/templates/prayer.html` |
| `app/templates/giving.html` |
| `app/templates/giving_success.html` |
| `app/templates/classes.html` |
| `app/templates/course_detail.html` |
| `app/templates/sermons.html` |
| `app/templates/dashboard.html` |
| `app/templates/profile.html` |
| `app/templates/login.html` |
| `app/templates/register.html` |
| `app/templates/applications.html` |
| `app/templates/about_minister_joy.html` |
| `app/templates/includes/social_links.html` |
| `app/templates/includes/event_card.html` |
| `app/templates/includes/app_store_buttons.html` |
| `app/templates/includes/app_features.html` |
| `app/templates/errors/404.html` |
| `app/templates/errors/500.html` |
| `app/templates/admin/*.html` (13 admin templates) |

### Routes & Application Code

| Path |
|------|
| `app/__init__.py` |
| `app/routes/api_routes.py` |
| `app/routes/main_routes.py` |
| `app/routes/auth_routes.py` |
| `app/routes/admin_routes.py` |
| `app/routes/class_routes.py` |
| `app/routes/giving_routes.py` |
| `app/routes/prayer_routes.py` |
| `app/routes/sermon_routes.py` |
| `app/utils/social.py` |

### Static Assets

| Path |
|------|
| `app/static/css/styles.css` |
| `app/static/js/main.js` |
| `app/static/js/gallery-lightbox.js` |

### Audit Tooling

| Path |
|------|
| `scripts/audit_social_media.py` |

**Total application files scanned:** 57

---

## 2. Authoritative Social Configuration

Source: `app/utils/social.py`

| Platform | URL | Display |
|----------|-----|---------|
| **TikTok** | `https://www.tiktok.com/@womenofpassionandpurpose` | @womenofpassionandpurpose |
| **Facebook** | `https://www.facebook.com/share/18GWq4xT8s/?mibextid=wwXIfr` | Facebook |
| **YouTube** | `https://www.youtube.com/@moppandwopp` | MOPP and WOPP |

URLs are validated at import time (`validate_external_url`) — must use `http`/`https` with a valid host.

---

## 3. Social Link Locations

| Location | Variant | Platforms | Viewports |
|----------|---------|-----------|-----------|
| **Site footer** (all pages via `base.html`) | `footer` | TikTok, Facebook, YouTube | Desktop, tablet, mobile |
| **Mobile navigation menu** (`base.html`) | `compact` | TikTok, Facebook, YouTube | Mobile / tablet (< lg) |
| **Contact page** — Get In Touch | `contact` | TikTok, Facebook, YouTube | All |
| **About page** — Connect With Us | `about` | TikTok, Facebook, YouTube | All |
| **API** — `GET /api/v1/ministry` | JSON `social` object | TikTok, Facebook, YouTube | API clients |

**Note:** Desktop top navigation intentionally does not include social icons (preserves existing header layout). Social presence on desktop is via the **footer** on every page.

---

## 4. Forbidden Reference Check

| Pattern | Status |
|---------|--------|
| `instagram.com` | **Not found** |
| `fa-instagram` | **Not found** |
| `menandwomenofpassionandpurpose` (old handles) | **Not found** |
| `@menandwomenofpassionandpurpose` | **Not found** |
| Old TikTok URL (`tiktok.com/@menandwomen…`) | **Not found** |
| Old YouTube URL (`youtube.com/@menandwomen…`) | **Not found** |
| Non-HTTPS social URLs | **Not found** |
| Placeholder / `#` social links | **Not found** |

### Acceptable non-link references

| File | Text | Reason |
|------|------|--------|
| `app/templates/about.html` | "9:00 PM **YouTube**" | Weekly schedule description (Global Prayerline), not a social profile link |
| `config.py` / footer | `womenofpassionandpurpose2024@gmail.com` | Ministry email address, not a social URL |

---

## 5. Link Attribute Verification

Automated scan of **42 rendered social anchors** across 6 pages (`/`, `/about`, `/contact`, `/events`, `/gallery`, `/app`):

| Requirement | Result |
|-------------|--------|
| Opens in new tab (`target="_blank"`) | **42 / 42 pass** |
| Uses HTTPS | **42 / 42 pass** |
| Has `aria-label` | **42 / 42 pass** |
| Has `rel="noopener noreferrer"` | **42 / 42 pass** |
| Decorative icons use `aria-hidden="true"` | **Pass** |
| Correct official URLs only | **42 / 42 pass** |

### API verification

`GET /api/v1/ministry` returns:

```json
{
  "social": {
    "tiktok": "https://www.tiktok.com/@womenofpassionandpurpose",
    "facebook": "https://www.facebook.com/share/18GWq4xT8s/?mibextid=wwXIfr",
    "youtube": "https://www.youtube.com/@moppandwopp"
  }
}
```

**Pass** — matches authoritative configuration; no `instagram` key.

---

## 6. Responsive Rendering Verification

| Viewport | Footer icons | Mobile menu icons | Contact icons | About cards |
|----------|----------------|-------------------|---------------|-------------|
| **Desktop (≥1024px)** | Visible | Hidden (lg:hidden menu) | Visible on `/contact` | Visible on `/about` |
| **Tablet (768–1023px)** | Visible | Visible in hamburger menu | Visible | Visible |
| **Mobile (<768px)** | Visible | Visible in hamburger menu | Visible | Visible |

### CSS responsive features confirmed

- `flex flex-wrap gap-3` — icons wrap on narrow screens
- `md:gap-10` on about variant — increased spacing on tablet+
- Icon touch targets ≥ 2.5rem (`social-icon-btn`, `social-icon-btn--footer`)
- Hover effects: `translateY`, gradient shift, shadow (purple/gold brand)
- Font Awesome 6.5.1 CDN loaded globally (`fab fa-tiktok`, `fab fa-facebook-f`, `fab fa-youtube`)

---

## 7. Lighthouse Accessibility (Social Elements)

**Page tested:** `/about` (includes dedicated social section + footer + mobile menu markup)  
**Tool:** Lighthouse (accessibility category only)

| Audit | Score | Social impact |
|-------|-------|---------------|
| **Overall accessibility** | **87 / 100** | — |
| **`link-name`** (links have discernible names) | **1.0 — Pass** | All social icon links pass via `aria-label` |
| **`list` / `listitem`** | **1.0 — Pass** | N/A to social |
| **`button-name`** | **0 — Fail** | Mobile hamburger `<button>` (site-wide, not social) |
| **`heading-order`** | **0 — Fail** | Page heading hierarchy (site-wide, not social) |

**Conclusion:** Social media links fully comply with Lighthouse link accessibility requirements. Page-level failures are unrelated to social implementation.

---

## 8. Issues Found (Current Audit)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| — | — | No social media issues detected | **Clean** |

---

## 9. Issues Fixed (Prior Implementation)

These issues were identified before the centralized social system and **resolved** in the social media implementation sprint:

| # | Issue | Fix applied |
|---|-------|-------------|
| 1 | Instagram placeholder in footer | Removed; replaced with Facebook |
| 2 | Wrong TikTok URL (`@menandwomenofpassionandpurpose`) | Updated to `@womenofpassionandpurpose` |
| 3 | Wrong YouTube URL (`@menandwomenofpassionandpurpose`) | Updated to `@moppandwopp` |
| 4 | Duplicate hardcoded links in templates | Centralized in `app/utils/social.py` |
| 5 | Missing `aria-label` on icon-only links | Added descriptive labels per platform |
| 6 | Inconsistent `rel` attributes | Standardized `rel="noopener noreferrer"` |
| 7 | API `/ministry` returned old social URLs | Now uses `get_social_dict()` |
| 8 | Jinja2 invalid `{% include ... with %}` syntax | Fixed to `{% with %}…{% include %}…{% endwith %}` |

---

## 10. Final Verification Status

| Check | Status |
|-------|--------|
| Crawl all templates, routes, API, static content | **Complete** |
| No Instagram / old URLs / placeholders | **Verified** |
| Desktop footer social icons | **Verified** |
| Tablet/mobile footer + menu icons | **Verified** |
| Contact page social icons | **Verified** |
| About page social section | **Verified** |
| All links open in new tab | **Verified (42/42)** |
| All links use HTTPS | **Verified (42/42)** |
| All links have `aria-label` | **Verified (42/42)** |
| All links have `rel="noopener noreferrer"` | **Verified (42/42)** |
| Lighthouse `link-name` for social links | **Pass** |
| Automated audit script | **`scripts/audit_social_media.py` — PASS** |

---

## 11. Launch Readiness Score

### Social Media Readiness: **98 / 100**

| Category | Score | Notes |
|----------|-------|-------|
| URL accuracy & centralization | 100 | Single source of truth with validation |
| Security (`noopener noreferrer`, HTTPS) | 100 | All links compliant |
| Accessibility (social links) | 100 | Lighthouse `link-name` pass |
| Coverage (footer, contact, about, API) | 100 | All designated areas covered |
| Responsive design | 95 | Footer + mobile menu; no desktop header bar icons (by design) |
| Maintainability | 100 | One config file + one template partial |

**Deduction (-2):** Desktop header nav does not expose social icons (intentional layout preservation). Footer provides desktop access on all pages.

---

## 12. Recommendations (Optional, Non-Blocking)

1. Add `:focus-visible` outline to `.social-icon-btn` and `.social-card-link` for keyboard navigation polish (site-wide pattern).
2. Re-run `python scripts/audit_social_media.py` after any template or URL change.
3. Re-run Lighthouse on production URL after HTTPS deployment for final sign-off.

---

## 13. How to Re-Run This Audit

```bash
cd ministry_project
.venv\Scripts\activate          # Windows
python scripts/audit_social_media.py
```

Expected output: `AUDIT_PASSED` with `ISSUES 0`.

---

*Report generated after full crawl and automated verification of the MWPP ministry website social media implementation.*
