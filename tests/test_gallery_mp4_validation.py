"""Automated tests for Gallery MP4 content-first validation."""
from __future__ import annotations

import pytest

from mp4_helpers import make_mp4_bytes


MAX_SECONDS = 300
MAX_BYTES = 100 * 1024 * 1024


def _validate(gallery_media, upload, *, max_seconds=MAX_SECONDS, max_bytes=MAX_BYTES):
    return gallery_media.validate_gallery_mp4_file(
        upload,
        max_seconds=max_seconds,
        max_bytes=max_bytes,
    )


class TestSniffIsMp4Container:
    def test_standard_ftyp(self, gallery_media, mp4_bytes):
        assert gallery_media.sniff_is_mp4_container(mp4_bytes) is True

    def test_empty_and_short(self, gallery_media):
        assert gallery_media.sniff_is_mp4_container(b"") is False
        assert gallery_media.sniff_is_mp4_container(b"ftyp") is False
        assert gallery_media.sniff_is_mp4_container(b"\x00" * 11) is False

    def test_junk_rejected(self, gallery_media):
        assert gallery_media.sniff_is_mp4_container(b"NOTANMP4FILEXXXX") is False

    def test_ftyp_after_free_atom(self, gallery_media):
        # free(8) + ftyp — still a valid ISO BMFF layout some cameras emit
        free = (8).to_bytes(4, "big") + b"free"
        body = free + make_mp4_bytes()
        assert gallery_media.sniff_is_mp4_container(body) is True


class TestNormalizeHelpers:
    def test_normalize_mime_strips_codecs(self, gallery_media):
        assert (
            gallery_media._normalize_mime('video/mp4; codecs="avc1.42E01E"')
            == "video/mp4"
        )
        assert gallery_media._normalize_mime(None) == ""
        assert gallery_media._normalize_mime("  VIDEO/MP4  ") == "video/mp4"

    def test_filename_extension_handles_paths(self, gallery_media):
        assert gallery_media._filename_extension(r"C:\Users\x\clip.MP4") == "mp4"
        assert gallery_media._filename_extension("/tmp/photos/IMG_1.mov") == "mov"
        assert gallery_media._filename_extension("noext") == ""
        assert gallery_media._filename_extension(None) == ""


class TestValidateAcceptsValidMp4:
    @pytest.mark.parametrize(
        "filename,mimetype",
        [
            ("clip.mp4", "video/mp4"),
            ("clip.mp4", "video/quicktime"),
            ("clip.mp4", "application/octet-stream"),
            ("clip.mp4", "application/mp4"),
            ("clip.mp4", "video/x-m4v"),
            ("clip.mp4", ""),
            ("clip.mp4", 'video/mp4; codecs="avc1.42E01E"'),
            ("IMG_1234", "video/quicktime"),  # mobile: no extension
            ("clip.m4v", "video/x-m4v"),
            (r"C:\Downloads\sermon.mp4", "binary/octet-stream"),
        ],
    )
    def test_accepts_browser_mime_variants(
        self, gallery_media, make_upload, mp4_bytes, filename, mimetype
    ):
        meta, err = _validate(gallery_media, make_upload(filename, mp4_bytes, mimetype))
        assert err is None, err
        assert meta is not None
        assert meta["sniff_ok"] is True
        assert meta["file_size"] == len(mp4_bytes)

    def test_accepts_under_duration_limit(self, gallery_media, make_upload, build_mp4):
        data = build_mp4(duration_seconds=299)
        meta, err = _validate(gallery_media, make_upload("ok.mp4", data, "video/mp4"))
        assert err is None
        assert meta["duration_seconds"] == pytest.approx(299.0)

    def test_accepts_exact_duration_limit(self, gallery_media, make_upload, build_mp4):
        data = build_mp4(duration_seconds=300)
        meta, err = _validate(gallery_media, make_upload("ok.mp4", data, "video/mp4"))
        assert err is None
        assert meta["duration_seconds"] == pytest.approx(300.0)


class TestValidateRejectsInvalid:
    def test_missing_file(self, gallery_media):
        meta, err = _validate(gallery_media, None)
        assert meta is None
        assert err == "Please choose a file to upload."

    def test_missing_filename(self, gallery_media, make_upload, mp4_bytes):
        meta, err = _validate(gallery_media, make_upload(None, mp4_bytes, "video/mp4"))
        assert meta is None
        assert "choose a file" in err.lower()

    def test_empty_file(self, gallery_media, make_upload):
        meta, err = _validate(gallery_media, make_upload("empty.mp4", b"", "video/mp4"))
        assert meta is None
        assert "empty" in err.lower()

    @pytest.mark.parametrize(
        "filename,mimetype",
        [
            ("clip.mov", "video/quicktime"),
            ("clip.avi", "video/x-msvideo"),
            ("clip.mkv", "video/x-matroska"),
            ("clip.webm", "video/webm"),
            ("clip.wmv", "video/x-ms-wmv"),
            ("clip.flv", "video/x-flv"),
        ],
    )
    def test_rejects_forbidden_extensions(
        self, gallery_media, make_upload, mp4_bytes, filename, mimetype
    ):
        meta, err = _validate(gallery_media, make_upload(filename, mp4_bytes, mimetype))
        assert meta is None
        assert "Unsupported video format" in err
        ext = filename.rsplit(".", 1)[-1]
        assert f".{ext}" in err

    def test_rejects_corrupt_mp4_named_file(self, gallery_media, make_upload):
        meta, err = _validate(
            gallery_media,
            make_upload("fake.mp4", b"NOTANMP4FILEXXXX", "video/mp4"),
        )
        assert meta is None
        assert "Corrupted video" in err

    def test_rejects_non_video_junk(self, gallery_media, make_upload):
        meta, err = _validate(
            gallery_media,
            make_upload("notes.txt", b"hello world", "text/plain"),
        )
        assert meta is None
        assert "Unsupported video format" in err

    def test_rejects_oversize(self, gallery_media, make_upload, mp4_bytes):
        meta, err = _validate(
            gallery_media,
            make_upload("big.mp4", mp4_bytes, "video/mp4"),
            max_bytes=50,
        )
        assert meta is None
        assert "maximum size" in err.lower()

    def test_rejects_over_duration(self, gallery_media, make_upload, build_mp4):
        data = build_mp4(duration_seconds=301)
        meta, err = _validate(
            gallery_media,
            make_upload("long.mp4", data, "video/mp4"),
            max_seconds=300,
        )
        assert meta is None
        assert "exceeds 300 seconds" in err
        assert "301" in err

    def test_mime_alone_does_not_reject_valid_container(
        self, gallery_media, make_upload, mp4_bytes
    ):
        """Regression: Gallery used to hard-fail on non-allowlisted MIME."""
        meta, err = _validate(
            gallery_media,
            make_upload("clip.mp4", mp4_bytes, "application/x-unknown"),
        )
        assert err is None
        assert meta["sniff_ok"] is True


class TestStreamRewound:
    def test_stream_position_reset_after_validation(
        self, gallery_media, make_upload, mp4_bytes
    ):
        upload = make_upload("clip.mp4", mp4_bytes, "video/mp4")
        upload.stream.seek(10)
        meta, err = _validate(gallery_media, upload)
        assert err is None
        assert upload.stream.tell() == 0
