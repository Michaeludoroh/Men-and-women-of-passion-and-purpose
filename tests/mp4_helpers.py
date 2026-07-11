"""Minimal ISO BMFF builders and upload fakes for Gallery MP4 tests."""
from __future__ import annotations

import struct
from io import BytesIO


def box(typ: bytes, payload: bytes) -> bytes:
    size = 8 + len(payload)
    return struct.pack(">I", size) + typ + payload


def make_ftyp() -> bytes:
    return box(b"ftyp", b"isom" + struct.pack(">I", 0) + b"isomiso2mp41")


def make_mvhd_v0(*, timescale: int, duration_ticks: int) -> bytes:
    # version(1) + flags(3) + creation(4) + modification(4) + timescale(4) + duration(4)
    payload = (
        b"\x00"
        + b"\x00\x00\x00"
        + struct.pack(">I", 0)
        + struct.pack(">I", 0)
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration_ticks)
        + b"\x00" * 80
    )
    return box(b"mvhd", payload)


def make_mp4_bytes(*, duration_seconds: float | None = None, timescale: int = 1000) -> bytes:
    """Minimal ISO BMFF: ftyp + optional moov/mvhd for duration checks."""
    data = make_ftyp()
    if duration_seconds is None:
        return data + b"\x00" * 64
    ticks = int(round(duration_seconds * timescale))
    moov = box(b"moov", make_mvhd_v0(timescale=timescale, duration_ticks=ticks))
    return data + moov


class FakeUpload:
    """Werkzeug FileStorage-like object for validator unit tests."""

    def __init__(self, filename: str | None, data: bytes, mimetype: str = ""):
        self.filename = filename
        self.mimetype = mimetype
        self.stream = BytesIO(data)
