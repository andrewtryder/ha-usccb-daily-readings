"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util

from tests.fixtures import load_fixture_bytes

if find_spec("pytest_homeassistant") is None:
    pytest_plugins = "pytest_homeassistant_custom_component"

FIXTURES = Path(__file__).parent / "fixtures" / "rss"
FROZEN_TIME = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test."""
    yield


@pytest.fixture
def frozen_time():
    """Patch dt_util.now() to a stable instant."""
    with patch.object(
        dt_util, "now", return_value=dt_util.as_local(FROZEN_TIME)
    ) as mocked:
        yield mocked


@pytest.fixture
def rss_weekday_bytes() -> bytes:
    """Return synthetic weekday RSS bytes."""
    return load_fixture_bytes(FIXTURES / "weekday_sample.xml")


@pytest.fixture
def mock_usccb_feed(aioclient_mock, rss_weekday_bytes: bytes):
    """Mock the USCCB RSS feed."""
    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=200,
        content=rss_weekday_bytes,
        headers={"Content-Type": "application/rss+xml; charset=utf-8"},
    )
    return aioclient_mock
