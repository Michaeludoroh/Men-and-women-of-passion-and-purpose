# STATUS

**ARCHIVED FOR FUTURE IMPLEMENTATION**

| Field | Value |
|-------|--------|
| **Priority** | Medium |
| **Current Status** | Deferred until after the website launch |
| **Reason** | To keep the current release focused on core ministry website functionality while preserving the complete implementation plan for a future release |

---

# Enhanced Sermons & Video Experience

## Overview

Transform the ministry sermon experience into a unified video platform that supports:

1. **Uploaded sermon videos** (hosted on the ministry site)
2. **External sermon URLs** (YouTube, Facebook, and other social platforms)

Administrators will manage both sources from the Admin Dashboard. Visitors will enjoy autoplay previews on the homepage, modern sermon cards on the Sermons page, and a reusable in-site video player for uploaded content.

**This document is the source of truth for a future release.** Do not implement until this feature is explicitly scheduled.

---

## Current Baseline (as of archive date)

The live site already includes a lighter sermon preview experience:

- Homepage recent sermons use `includes/sermon_preview_video.html`
- External watch URLs are resolved via social helpers (e.g. YouTube / Facebook preference)
- `Sermon` model currently exposes fields such as `video_url` (and related metadata)

The future feature should **extend** this baseline rather than discard it: keep external URL behavior, and add first-class uploaded video support, richer admin UX, and a reusable player component.

---

## Goals

| Goal | Description |
|------|-------------|
| Dual media sources | Support uploaded files and external URLs per sermon |
| Admin control | Upload, replace, preview, remove; validate URLs; detect source type |
| Homepage excellence | Muted looping preview with custom mute control; smart click behavior |
| Sermons page | Modern cards, thumbnails, conditional play vs redirect |
| Reusable player | Full controls, fullscreen, a11y, error/loading states |
| Performance & a11y | Lazy load, posters, keyboard, ARIA |
| Backward compatibility | Existing external-URL sermons continue to work |

## Non-Goals (for this feature release)

- Live streaming (listed under Future Improvements)
- Changing payment, partnership, or unrelated modules
- Breaking existing sermon list/API contracts without a migration plan

---

## Admin Dashboard Enhancements

### Media sources

Administrators must be able to attach sermon media as:

| Source | Description |
|--------|-------------|
| **Uploaded video** | File stored under ministry uploads (e.g. `static/uploads/sermons/`) |
| **External URL** | Link to YouTube, Facebook, or other approved platforms |

A sermon may have one primary playable source. Rules to define at implementation time:

- Prefer uploaded video for in-site playback when present
- Fall back to external URL for redirect / social open
- Clear UX when both are set (e.g. “Primary source” selector or last-write-wins with warning)

### Upload workflow

- Upload new sermon video (MP4 required; WebM optional if project already supports it)
- Replace existing uploaded video
- Preview video in admin before/after save
- Remove uploaded video without deleting the sermon record
- Enforce project upload size limits and allowed extensions
- Client + server validation with user-friendly error messages

### External URL workflow

- Enter / edit external sermon URL
- Validate URL format and (where practical) known platforms
- Preview thumbnail or embed preview when possible
- Clear / remove external URL independently of uploaded file

### Media source detection

Automatically detect and store:

- `upload` — file-based sermon video
- `external` — social / remote URL
- `none` — no video attached

Display a **media type badge** in sermon management lists (Image/Video/External as applicable).

### Updated sermon management workflow

1. Create or edit sermon (title, preacher, category, description, etc.)
2. Optionally upload video **or** paste external URL
3. Optionally set poster / thumbnail image
4. Preview media
5. Save
6. From list: Edit · Replace media · Remove media · Delete sermon

Preserve existing authentication and admin authorization.

---

## Homepage Experience

### Preview behavior

| Requirement | Detail |
|-------------|--------|
| Autoplay | Background preview starts automatically when in view (respect browser policies) |
| Muted by default | Required for autoplay compliance |
| Custom mute/unmute | Ministry-styled control; **no** native HTML5 controls on the preview |
| Loop | Continuous loop while visible |
| Poster | Show poster/thumbnail before load or if video fails |

### Click behavior

| Media type | Action |
|------------|--------|
| External URL | Open the social / platform page in a new tab (`noopener noreferrer`) |
| Uploaded video | Open fullscreen modal / lightbox and play with full controls |

### UX notes

- Do not place competing overlays (badges, stickers) on the preview beyond mute + play affordance if needed
- Keep brand purple / gold styling consistent with the site
- Lazy-load preview sources until the card is near the viewport

---

## Sermons Page

### Layout

- Modern sermon cards in a responsive grid
- Video thumbnails or poster images
- Title, preacher, category, short description
- Clear CTA: “Watch” / “Play”

### Conditional behavior

| Media type | Action |
|------------|--------|
| External URL | Redirect / open external platform |
| Uploaded video | Play within the website (modal or dedicated player section) |

### Uploaded playback

- Full HTML5 video controls
- Responsive sizing
- Accessible labels
- Loading and error states

---

## Video Player Component

### `SermonVideoPlayer` (reusable)

Implement as a shared include / JS module usable from:

- Homepage modal
- Sermons page
- Admin preview (simplified mode)

### Features

| Feature | Notes |
|---------|--------|
| Fullscreen | Native Fullscreen API + UI button |
| Volume control | Mute toggle + volume where supported |
| Playback speed | e.g. 0.75×, 1×, 1.25×, 1.5×, 2× |
| Keyboard shortcuts | Space play/pause, arrows seek, M mute, F fullscreen, Esc close modal |
| Loading state | Spinner / skeleton while buffering |
| Error handling | Friendly message + optional “Open external link” fallback |
| Responsive design | Works on mobile, tablet, desktop |
| Poster | Display until playback starts |

### Suggested API (implementation-time)

```text
SermonVideoPlayer.mount(container, {
  src,           // uploaded video URL
  poster,        // optional poster image URL
  title,         // for aria-label
  autoplay,      // modal may autoplay after user gesture
  controls,      // true for full player; false for homepage preview
})
```

Exact stack (vanilla JS vs Alpine) should match existing site patterns.

---

## Database Changes

Extend the `Sermon` model (names illustrative — align with existing columns at implementation):

| Field | Type | Purpose |
|-------|------|---------|
| `video_file_path` / uploaded video URL | String, nullable | Path under `static/uploads/...` |
| `external_video_url` | String, nullable | YouTube / Facebook / other URL |
| `poster_path` | String, nullable | Thumbnail / poster image |
| `video_source_type` | String enum | `upload` \| `external` \| `none` |
| Existing fields | — | Keep title, description, category, preacher, `created_at`, etc. |

### Migration requirements

- Alembic migration adding new columns with safe defaults
- Backfill: existing `video_url` values → treat as `external` where present
- Do not break API `to_dict` / mobile consumers — extend payload, don’t remove keys without versioning

### Storage

- Reuse existing upload service patterns (`save_upload`, allowed video extensions, delete on replace/remove)
- Ensure upload directories exist in production (`ensure_upload_dirs`)

---

## Admin Improvements (UI)

- Media type badges on sermon cards/rows
- Inline or modal video preview for uploads
- Replace / remove uploaded video and clear external URL
- Full **Edit Sermon** support for all media fields
- Validation messages for unsupported files and invalid URLs
- Display order / featured flags unchanged unless already planned elsewhere

---

## Forms, DTOs & API

### Forms

Update `SermonForm` (or equivalent) to include:

- File field for uploaded video
- Optional poster image field
- External URL field with validators
- Optional “remove video” / “remove poster” checkboxes (pattern used on leaders)

### API

Extend sermon JSON to include:

```json
{
  "video_source_type": "upload|external|none",
  "video_file_url": "...",
  "external_video_url": "...",
  "poster_url": "...",
  "video_url": "..." 
}
```

Keep `video_url` for backward compatibility (map to primary watchable URL).

---

## Performance

| Technique | Application |
|-----------|-------------|
| Lazy loading | Preview videos and posters load when near viewport |
| Poster first | Avoid downloading full video until interaction (except muted preview policy) |
| Preload | `preload="none"` or `metadata` for cards; `auto` only in active modal |
| Responsive media | Appropriate sizes; avoid layout shift with aspect-ratio boxes |
| Efficient replace | Delete old upload files when replaced |

---

## Accessibility

- Proper heading hierarchy on Sermons page
- ARIA labels on play, mute, close, and player controls
- Keyboard navigation for cards, modal, and player shortcuts
- Visible focus states (brand gold outline)
- Screen reader announcements for loading/errors (`aria-live`)
- Do not rely on color alone for media type badges
- Respect `prefers-reduced-motion` (reduce autoplay / decorative motion)

---

## Security

- Validate uploads on client and server (extension + size)
- Reject unsupported types
- Sanitize / validate external URLs (scheme `https` preferred)
- Only admins can upload/replace/delete
- Store files only under allowed upload paths; never trust client paths for delete

---

## Suggested Implementation Order

1. Database migration + model helpers (`video_source_type`, paths, backfill)
2. Upload service extensions for sermon videos / posters
3. Admin form + manage/edit UI (upload, replace, remove, preview, badges)
4. Reusable `SermonVideoPlayer` + modal shell
5. Homepage preview click behavior (external vs upload)
6. Sermons page cards + conditional play/redirect
7. API payload extensions
8. Performance pass (lazy load, posters)
9. Accessibility pass
10. Full testing checklist below

---

## Testing Checklist

Use this checklist when the feature is implemented — do not rewrite requirements from scratch.

### Admin

- [ ] Upload sermon video (MP4) succeeds
- [ ] Unsupported file types are rejected with clear message
- [ ] Upload size limit is enforced
- [ ] Video preview works in admin
- [ ] Replace uploaded video works; old file removed
- [ ] Remove uploaded video works; sermon record remains
- [ ] External URL can be saved and cleared
- [ ] Invalid URLs are rejected
- [ ] Media type badge shows correctly (upload / external / none)
- [ ] Edit sermon updates all fields without data loss
- [ ] Unauthorized users cannot access admin media actions

### Homepage

- [ ] Preview autoplays muted
- [ ] Custom mute/unmute works
- [ ] Preview loops
- [ ] Native controls are not shown on preview
- [ ] Click on external sermon opens platform URL
- [ ] Click on uploaded sermon opens modal/fullscreen player
- [ ] No console errors during preview

### Sermons page

- [ ] Cards render responsively (mobile / tablet / desktop)
- [ ] Thumbnails / posters display
- [ ] External sermons redirect / open correctly
- [ ] Uploaded sermons play in-site with full controls
- [ ] Layout does not shift when media loads

### Player

- [ ] Play / pause works
- [ ] Volume / mute works
- [ ] Playback speed works
- [ ] Fullscreen works
- [ ] Keyboard shortcuts work
- [ ] Loading state appears while buffering
- [ ] Error state appears for broken sources
- [ ] Modal closes with Esc and close button; focus returns

### Data & compatibility

- [ ] Existing sermons with only external URLs still work
- [ ] Migration / backfill correct
- [ ] API consumers still receive expected fields
- [ ] No database errors
- [ ] No regressions on sermon create/delete

### Quality

- [ ] Lazy loading verified
- [ ] Accessibility spot-check (keyboard + screen reader)
- [ ] Lighthouse / performance acceptable on sermon pages
- [ ] Brand styling consistent (purple / gold / white)

---

## Future Improvements

Ideas beyond the core feature (not required for the first Enhanced Sermons release):

- Live streaming integration
- Playlist support
- Sermon series grouping
- Watch history
- Recently watched
- Video analytics (views, completion rate)
- Download sermons (where licensing allows)
- Closed captions / subtitles
- Multiple quality streaming (adaptive bitrate)
- Chromecast / AirPlay support
- Offline viewing in the mobile app
- Chapter markers within long sermons
- Related sermons recommendations

---

## Out of Scope Reminder

When this feature is picked up:

- Do not expand scope into unrelated modules (partnership, gallery, giving) unless required for shared upload utilities
- Prefer reusing existing upload, auth, and UI patterns
- Ship behind a clear migration and rollback plan

---

## Archive Metadata

| Item | Value |
|------|--------|
| Document path | `docs/future-features/enhanced-sermons-video-experience.md` |
| Feature name | Enhanced Sermons & Video Experience |
| Implementation status | **Not started** (archived) |
| Code changes in this archive task | **None** — documentation only |

---

*End of archived implementation plan.*
