"""Tests for integration setup and unload."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNKNOWN
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import DOMAIN, UNIQUE_ID


@pytest.mark.asyncio
async def test_setup_and_sensors(hass, mock_usccb_feed) -> None:
    """Load entities and expose expected citation states."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="USCCB Daily Readings",
            data={},
            unique_id=UNIQUE_ID,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.usccb_daily_readings_first_reading")
        assert state is not None
        assert state.state == "Romans 1:1-7"

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert gospel.state == "Luke 10:21-24"

        second = hass.states.get("sensor.usccb_daily_readings_second_reading")
        assert second is not None
        assert second.state == STATE_UNKNOWN


@pytest.mark.asyncio
async def test_unload_entry(hass, mock_usccb_feed) -> None:
    """Unload removes entities."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="USCCB Daily Readings",
            data={},
            unique_id=UNIQUE_ID,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.NOT_LOADED
