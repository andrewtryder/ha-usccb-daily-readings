"""Tests for user-visible coordinator logging."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.api import USCCBClient
from custom_components.usccb_daily_readings.const import DOMAIN, UNIQUE_ID
from custom_components.usccb_daily_readings.coordinator import DailyReadingsCoordinator


@pytest.mark.asyncio
async def test_info_when_checking_feed(
    hass, mock_usccb_feed, caplog: pytest.LogCaptureFixture
) -> None:
    """Log at INFO when contacting the RSS feed."""
    caplog.set_level(
        logging.INFO, logger="custom_components.usccb_daily_readings.coordinator"
    )
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id=UNIQUE_ID)
    entry.add_to_hass(hass)
    client = USCCBClient(async_get_clientsession(hass))
    coordinator = DailyReadingsCoordinator(hass, entry, client)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        await coordinator.async_refresh()
    assert any(
        "Checking USCCB RSS feed for 2026-11-24" in record.message
        for record in caplog.records
    )
    assert any(
        record.message.startswith("Loaded readings for 2026-11-24:")
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_info_when_today_missing_from_feed(
    hass, caplog: pytest.LogCaptureFixture
) -> None:
    """Log at INFO when today's item is not yet published."""
    from custom_components.usccb_daily_readings.rss_parser import parse_feed

    caplog.set_level(
        logging.INFO, logger="custom_components.usccb_daily_readings.coordinator"
    )
    frozen = datetime(2026, 11, 30, 8, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id="x")
    entry.add_to_hass(hass)
    client = USCCBClient(async_get_clientsession(hass))
    coordinator = DailyReadingsCoordinator(hass, entry, client)
    stale = b"""<?xml version="1.0"?><rss version="2.0"><channel>
    <item><title>Old</title>
    <link>https://bible.usccb.org/bible/readings/112426.cfm</link>
    <description>&lt;h4&gt;Gospel &lt;a href="https://bible.usccb.org/bible/luke/1?1"&gt;Luke 1:1&lt;/a&gt;&lt;/h4&gt;</description>
    </item></channel></rss>"""
    client.fetch_feed = AsyncMock(return_value=parse_feed(stale))
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        await coordinator.async_refresh()
    assert any("not yet in RSS feed" in record.message for record in caplog.records)
