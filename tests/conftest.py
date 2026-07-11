"""Shared fixtures for Gallery MP4 validator tests."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from mp4_helpers import FakeUpload, make_mp4_bytes

ROOT = Path(__file__).resolve().parents[1]
GALLERY_MEDIA_PATH = ROOT / "app" / "services" / "gallery_media.py"
MODULE_NAME = "gallery_media_under_test"


@pytest.fixture(scope="session")
def gallery_media():
    """
    Load gallery_media.py directly so tests do not boot Flask / create_app.

    The validator has no Flask dependency; importing ``app.services...`` would
    pull in ``app/__init__.py`` and the full extension stack.
    """
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]

    spec = importlib.util.spec_from_file_location(MODULE_NAME, GALLERY_MEDIA_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Required so dataclasses / annotations resolve during exec_module.
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def make_upload():
    def _make(filename: str | None, data: bytes, mimetype: str = "") -> FakeUpload:
        return FakeUpload(filename, data, mimetype)

    return _make


@pytest.fixture
def mp4_bytes():
    return make_mp4_bytes()


@pytest.fixture
def build_mp4():
    return make_mp4_bytes
