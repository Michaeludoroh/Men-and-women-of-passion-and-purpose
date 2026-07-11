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
