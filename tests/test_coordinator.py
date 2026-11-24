"""Tests for the data coordinator."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.api import USCCBClient
from custom_components.usccb_daily_readings.const import DOMAIN
from custom_components.usccb_daily_readings.coordinator import DailyReadingsCoordinator
from tests.fixtures import load_fixture_bytes

FIXTURE = Path(__file__).parent / "fixtures" / "rss" / "weekday_sample.xml"
FROZEN = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_coordinator_caches_same_day(hass, mock_usccb_feed) -> None:
    """Avoid duplicate network calls for the same liturgical day."""
    with patch.object(dt_util, "now", return_value=dt_util.as_local(FROZEN)):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="USCCB",
            data={},
            unique_id="usccb_daily_readings",
        )
        config_entry.add_to_hass(hass)
        coordinator = DailyReadingsCoordinator(
            hass, config_entry, USCCBClient(async_get_clientsession(hass))
        )
        await coordinator.async_refresh()
        assert coordinator.last_update_success
        first_calls = len(mock_usccb_feed.mock_calls)
        await coordinator.async_refresh()
        assert len(mock_usccb_feed.mock_calls) == first_calls
        assert coordinator.data.mass.date == date(2026, 11, 24)


@pytest.mark.asyncio
async def test_coordinator_missing_today(hass, aioclient_mock) -> None:
    """Fail when today's readings are not published yet."""
    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=200,
        content=load_fixture_bytes(FIXTURE),
        headers={"Content-Type": "application/rss+xml; charset=utf-8"},
    )
    with patch.object(
        dt_util,
        "now",
        return_value=dt_util.as_local(
            datetime(2026, 11, 30, 8, 0, tzinfo=timezone.utc)
        ),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN, title="USCCB", data={}, unique_id="usccb"
        )
        config_entry.add_to_hass(hass)
        coordinator = DailyReadingsCoordinator(
            hass, config_entry, USCCBClient(async_get_clientsession(hass))
        )
        await coordinator.async_refresh()
        assert not coordinator.last_update_success
        assert coordinator.data is None
        assert isinstance(coordinator.last_exception, UpdateFailed)
        assert "not yet available" in str(coordinator.last_exception)
