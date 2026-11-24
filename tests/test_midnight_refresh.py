"""Tests for midnight refresh registration and callback execution."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import DOMAIN, UNIQUE_ID


@pytest.mark.asyncio
async def test_registers_midnight_refresh(hass, mock_usccb_feed) -> None:
    """Setup registers a local-midnight coordinator refresh."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        with patch(
            "custom_components.usccb_daily_readings.async_track_time_change"
        ) as track:
            cancel = AsyncMock()
            track.return_value = cancel
            entry = MockConfigEntry(
                domain=DOMAIN, title="USCCB", data={}, unique_id=UNIQUE_ID
            )
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
            track.assert_called_once()
            call = track.call_args
            assert call.kwargs["hour"] == 0
            assert call.kwargs["minute"] == 0
            assert call.kwargs["second"] == 5
            callback = call.args[1]

            coordinator = entry.runtime_data
            coordinator.async_request_refresh = AsyncMock()
            await callback(datetime.now())
            coordinator.async_request_refresh.assert_awaited_once()

            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()
