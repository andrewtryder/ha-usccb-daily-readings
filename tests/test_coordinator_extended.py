"""Additional coordinator behavior tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.api import USCCBClient
from custom_components.usccb_daily_readings.const import DOMAIN, UNIQUE_ID
from custom_components.usccb_daily_readings.coordinator import DailyReadingsCoordinator
from tests.fixtures import load_fixture_bytes

FIXTURE = Path(__file__).parent / "fixtures" / "rss" / "weekday_sample.xml"
YESTERDAY_ONLY = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Old</title>
<link>https://bible.usccb.org/bible/readings/112326.cfm</link>
<description>&lt;h4&gt;Gospel &lt;a href="https://bible.usccb.org/bible/luke/1?1"&gt;Luke 1:1&lt;/a&gt;&lt;/h4&gt;</description>
</item></channel></rss>"""


@pytest.mark.asyncio
async def test_new_local_day_without_feed_entry_unavailable(
    hass, mock_usccb_feed
) -> None:
    """Sensors become unavailable when the local calendar advances past the feed."""
    hass.config.time_zone = "America/New_York"
    nov_24_evening = datetime(2026, 11, 25, 3, 30, tzinfo=timezone.utc)
    nov_25_morning = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id=UNIQUE_ID)
    entry.add_to_hass(hass)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(nov_24_evening)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert hass.states.get("sensor.usccb_daily_readings_gospel").state != "unknown"

    with patch.object(dt_util, "now", return_value=dt_util.as_local(nov_25_morning)):
        await entry.runtime_data.async_request_refresh()
        await hass.async_block_till_done()
    gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
    assert gospel is not None
    assert gospel.state in ("unavailable", "unknown")
    assert not entry.runtime_data.last_update_success


@pytest.mark.asyncio
async def test_recovers_when_today_published(hass) -> None:
    """Hourly retries succeed once today's item appears in the feed."""
    from custom_components.usccb_daily_readings.rss_parser import parse_feed

    today_frozen = datetime(2026, 11, 24, 17, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id="usccb")
    entry.add_to_hass(hass)
    client = USCCBClient(async_get_clientsession(hass))
    fetch_mock = AsyncMock(
        side_effect=[
            parse_feed(YESTERDAY_ONLY),
            parse_feed(load_fixture_bytes(FIXTURE)),
        ]
    )
    with patch.object(client, "fetch_feed", fetch_mock):
        coordinator = DailyReadingsCoordinator(hass, entry, client)
        with patch.object(dt_util, "now", return_value=dt_util.as_local(today_frozen)):
            await coordinator.async_refresh()
            assert fetch_mock.await_count == 1
            assert not coordinator.last_update_success
            await coordinator.async_refresh()
            assert fetch_mock.await_count == 2
            assert coordinator.last_update_success
            assert coordinator.data.mass.date == date(2026, 11, 24)


@pytest.mark.asyncio
async def test_transient_failure_raises_update_failed(hass, aioclient_mock) -> None:
    """Surface UpdateFailed when the feed cannot be retrieved."""
    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=503,
        headers={"Content-Type": "application/rss+xml"},
    )
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id="u")
        entry.add_to_hass(hass)
        coordinator = DailyReadingsCoordinator(
            hass, entry, USCCBClient(async_get_clientsession(hass))
        )
        await coordinator.async_refresh()
        assert not coordinator.last_update_success
        assert isinstance(coordinator.last_exception, UpdateFailed)
