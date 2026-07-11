"""Gallery media helpers — external URL parsing and MP4 duration checks."""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse, urlunparse

import requests


SUPPORTED_EXTERNAL_PROVIDERS = (
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "vimeo",
    "twitter",
)


@dataclass
class ExternalVideoInfo:
    provider: str
    video_id: str | None
    watch_url: str
    embed_url: str | None
    thumbnail_url: str | None
    platform_label: str


def _clean_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise ValueError("Please paste a video URL.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Video URL must start with http:// or https://.")
    if not parsed.netloc:
        raise ValueError("Video URL is missing a valid host.")
    return url


def _youtube_id(url: str, host: str, path: str, query: dict) -> str | None:
    if "youtu.be" in host:
        vid = path.strip("/").split("/")[0]
        return vid or None
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        if path.startswith("/watch"):
            return (query.get("v") or [None])[0]
        if path.startswith("/shorts/"):
            return path.split("/shorts/")[1].split("/")[0] or None
        if path.startswith("/embed/"):
            return path.split("/embed/")[1].split("/")[0] or None
        if path.startswith("/live/"):
            return path.split("/live/")[1].split("/")[0] or None
    return None


def _vimeo_id(path: str) -> str | None:
    # /123456789 or /video/123456789
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    if parts[0] == "video" and len(parts) > 1 and parts[1].isdigit():
        return parts[1]
    if parts[0].isdigit():
        return parts[0]
    return None


def parse_external_video_url(url: str) -> ExternalVideoInfo:
    """Detect provider, normalize watch URL, and build embed/thumbnail when possible."""
    url = _clean_url(url)
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path or "/"
    query = parse_qs(parsed.query)

    # YouTube
    yt_id = _youtube_id(url, host, path, query)
    if yt_id and re.fullmatch(r"[\w-]{6,}", yt_id):
        watch = f"https://www.youtube.com/watch?v={yt_id}"
        return ExternalVideoInfo(
            provider="youtube",
            video_id=yt_id,
            watch_url=watch,
            embed_url=f"https://www.youtube.com/embed/{yt_id}",
            thumbnail_url=f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg",
            platform_label="YouTube",
        )

    # Vimeo
    if "vimeo.com" in host:
        vid = _vimeo_id(path)
        if not vid:
            raise ValueError("Could not find a Vimeo video ID in that URL.")
        watch = f"https://vimeo.com/{vid}"
        thumb = None
        try:
            # Public oEmbed — best-effort thumbnail
            resp = requests.get(
                "https://vimeo.com/api/oembed.json",
                params={"url": watch},
                timeout=4,
            )
            if resp.ok:
                thumb = (resp.json() or {}).get("thumbnail_url")
        except Exception:
            thumb = None
        return ExternalVideoInfo(
            provider="vimeo",
            video_id=vid,
            watch_url=watch,
            embed_url=f"https://player.vimeo.com/video/{vid}",
            thumbnail_url=thumb,
            platform_label="Vimeo",
        )

    # Facebook
    if "facebook.com" in host or "fb.watch" in host or "fb.com" in host:
        watch = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))
        return ExternalVideoInfo(
            provider="facebook",
            video_id=None,
            watch_url=watch,
            embed_url=None,
            thumbnail_url=None,
            platform_label="Facebook",
        )

    # Instagram
    if "instagram.com" in host:
        # Keep reel/post path; strip tracking query
        clean_path = path.rstrip("/") + "/"
        watch = f"https://www.instagram.com{clean_path}"
        return ExternalVideoInfo(
            provider="instagram",
            video_id=None,
            watch_url=watch,
            embed_url=None,
            thumbnail_url=None,
            platform_label="Instagram",
        )

    # TikTok
    if "tiktok.com" in host or "vm.tiktok.com" in host:
        watch = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        return ExternalVideoInfo(
            provider="tiktok",
            video_id=None,
            watch_url=watch,
            embed_url=None,
            thumbnail_url=None,
            platform_label="TikTok",
        )

    # X / Twitter
    if host in ("x.com", "twitter.com", "mobile.twitter.com"):
        watch = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        return ExternalVideoInfo(
            provider="twitter",
            video_id=None,
            watch_url=watch,
            embed_url=None,
            thumbnail_url=None,
            platform_label="X",
        )

    raise ValueError(
        "Unsupported video platform. Use YouTube, Facebook, Instagram, TikTok, Vimeo, or X (Twitter)."
    )


def get_mp4_duration_seconds(file_storage) -> float | None:
    """
    Read MP4 duration from the mvhd atom without external tools.
    Returns seconds (float) or None if duration cannot be determined.
    Resets the file stream to the start afterward.
    """
    stream = getattr(file_storage, "stream", None) or file_storage
    try:
        stream.seek(0)
        data = stream.read()
        stream.seek(0)
    except Exception:
        try:
            stream.seek(0)
        except Exception:
            pass
        return None

    duration = _parse_mp4_duration(data)
    try:
        stream.seek(0)
    except Exception:
        pass
    return duration


def _parse_mp4_duration(data: bytes) -> float | None:
    """Walk top-level boxes looking for moov/mvhd."""
    if len(data) < 8:
        return None

    def walk(buf: bytes, start: int, end: int) -> float | None:
        i = start
        while i + 8 <= end:
            size = struct.unpack(">I", buf[i : i + 4])[0]
            typ = buf[i + 4 : i + 8]
            header = 8
            if size == 1:
                if i + 16 > end:
                    break
                size = struct.unpack(">Q", buf[i + 8 : i + 16])[0]
                header = 16
            elif size == 0:
                size = end - i
            if size < header or i + size > end:
                break
            payload_start = i + header
            payload_end = i + size
            if typ == b"moov":
                found = walk(buf, payload_start, payload_end)
                if found is not None:
                    return found
            elif typ == b"mvhd":
                return _parse_mvhd(buf[payload_start:payload_end])
            i += size
        return None

    return walk(data, 0, len(data))


def _parse_mvhd(payload: bytes) -> float | None:
    if len(payload) < 20:
        return None
    version = payload[0]
    try:
        if version == 0:
            # timescale @ 12, duration @ 16 (after version/flags)
            timescale = struct.unpack(">I", payload[12:16])[0]
            duration = struct.unpack(">I", payload[16:20])[0]
        elif version == 1:
            timescale = struct.unpack(">I", payload[20:24])[0]
            duration = struct.unpack(">Q", payload[24:32])[0]
        else:
            return None
    except struct.error:
        return None
    if not timescale:
        return None
    return float(duration) / float(timescale)


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    total = int(round(seconds))
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# Gallery MP4 upload validation (independent of Sermons)
# ---------------------------------------------------------------------------

# Hard-reject extensions (never accept, even if MIME looks video-like).
GALLERY_REJECT_VIDEO_EXTENSIONS = frozenset({
    "avi", "mov", "mkv", "wmv", "flv", "3gp", "3g2", "webm", "mpg", "mpeg", "m4a",
})

# Logged only — never used as a hard accept/reject gate.
GALLERY_MP4_MIME_HINTS = frozenset({
    "video/mp4",
    "video/x-m4v",
    "video/x-mp4",
    "video/mpeg4",
    "application/mp4",
    "application/octet-stream",
    "binary/octet-stream",
    "video/quicktime",
})


def _normalize_mime(mimetype: str | None) -> str:
    raw = (mimetype or "").strip().lower()
    if not raw:
        return ""
    # Strip parameters e.g. video/mp4; codecs="avc1.42E01E"
    return raw.split(";", 1)[0].strip()


def _filename_extension(filename: str | None) -> str:
    name = (filename or "").strip()
    # Some browsers send full paths or Content-Disposition artifacts
    name = name.replace("\\", "/").split("/")[-1]
    if not name or "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower().strip()


def sniff_is_mp4_container(data: bytes) -> bool:
    """Return True when bytes look like ISO BMFF / MP4 (ftyp box present)."""
    if not data or len(data) < 12:
        return False
    # Scan a generous prefix — some cameras put free/wide atoms before ftyp.
    head = data[:8192]
    if head[4:8] == b"ftyp":
        return True
    # ftyp must be at a box boundary (size field immediately before the type).
    idx = 0
    while True:
        idx = head.find(b"ftyp", idx)
        if idx < 0:
            return False
        if idx >= 4:
            return True
        idx += 1


def read_upload_bytes(file_storage, limit: int | None = None) -> bytes:
    """Read upload bytes and always rewind the stream afterward."""
    stream = getattr(file_storage, "stream", None) or file_storage
    try:
        stream.seek(0)
        data = stream.read(limit) if limit is not None else stream.read()
        stream.seek(0)
        return data or b""
    except Exception:
        try:
            stream.seek(0)
        except Exception:
            pass
        return b""


def rewind_upload(file_storage) -> None:
    stream = getattr(file_storage, "stream", None) or file_storage
    try:
        stream.seek(0)
    except Exception:
        pass


def validate_gallery_mp4_file(
    file_storage,
    *,
    max_seconds: int,
    max_bytes: int,
) -> tuple[dict | None, str | None]:
    """
    Validate a Gallery MP4 upload (content-first).

    Permanent strategy:
    1. Hard-reject only known non-MP4 extensions (AVI/MOV/MKV/…)
    2. Treat browser MIME as advisory (log only) — never reject solely on MIME
    3. Confirm ISO BMFF via ftyp sniff
    4. Enforce size + duration limits

    This mirrors Sermons' permissive MIME handling while adding container proof,
    without sharing code with the Sermons module.
    """
    if not file_storage or not getattr(file_storage, "filename", None):
        return None, "Please choose a file to upload."

    original_name = (file_storage.filename or "").strip()
    ext = _filename_extension(original_name)
    mime = _normalize_mime(getattr(file_storage, "mimetype", None))

    file_size = None
    try:
        stream = getattr(file_storage, "stream", None) or file_storage
        stream.seek(0, 2)
        file_size = stream.tell()
        stream.seek(0)
    except Exception:
        file_size = None

    if ext in GALLERY_REJECT_VIDEO_EXTENSIONS:
        return None, f"Unsupported video format (.{ext}). Upload an MP4 video only."

    if file_size is not None and file_size > max_bytes:
        mb = max_bytes / (1024 * 1024)
        mb_label = f"{mb:.0f}" if mb >= 1 else f"{mb:.2f}"
        return None, f"Video exceeds maximum size ({mb_label} MB)."

    if file_size == 0:
        return None, "Unable to process video. The uploaded file is empty."

    # Content inspection — authoritative. MIME/extension are hints only.
    # Read full file for sniff + duration (moov atom is often at the end).
    read_limit = None
    if file_size is not None:
        read_limit = min(file_size, max_bytes) + 1
    elif max_bytes:
        read_limit = max_bytes + 1

    data = read_upload_bytes(file_storage, read_limit)
    rewind_upload(file_storage)

    if not data:
        return None, "Unable to process video."

    if not sniff_is_mp4_container(data):
        # Distinguish "clearly not a video we accept" vs corrupt MP4-named file
        if ext == "mp4" or mime in GALLERY_MP4_MIME_HINTS or mime.startswith("video/"):
            return None, "Corrupted video or not a valid MP4 container."
        return None, "Unsupported video format. Upload an MP4 video only."

    duration = _parse_mp4_duration(data)
    rewind_upload(file_storage)

    if duration is not None and duration > max_seconds:
        return None, (
            f"Video exceeds {max_seconds} seconds "
            f"(detected {int(duration)}s)."
        )

    return {
        "filename": original_name,
        "extension": ext or "mp4",
        "mime_type": mime or "video/mp4",
        "file_size": file_size if file_size is not None else len(data),
        "duration_seconds": duration,
        "sniff_ok": True,
        "mime_hint_ok": mime in GALLERY_MP4_MIME_HINTS or mime == "",
    }, None
