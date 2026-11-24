"""Tests for diagnostics."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import DOMAIN, FEED_URL, UNIQUE_ID
from custom_components.usccb_daily_readings.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.mark.asyncio
async def test_diagnostics_exclude_text(hass, mock_usccb_feed) -> None:
    """Diagnostics include metadata but not scripture bodies."""
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

        diagnostics = await async_get_config_entry_diagnostics(hass, entry)
        assert diagnostics["feed_url"] == FEED_URL
        assert diagnostics["liturgical_date"] == "2026-11-24"
        assert "Synthetic gospel text" not in str(diagnostics)
