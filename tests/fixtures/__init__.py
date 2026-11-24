"""Test fixture helpers."""

from __future__ import annotations

from pathlib import Path


def load_fixture_bytes(path: Path) -> bytes:
    """Load a binary fixture file."""
    return path.read_bytes()
