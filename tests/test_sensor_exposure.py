"""Verify copyrighted reading text is not exposed on entities."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import ATTR_SECTIONS, DOMAIN, UNIQUE_ID


@pytest.mark.asyncio
async def test_reading_entities_omit_text_attribute(hass, mock_usccb_feed) -> None:
    """Reading sensors must not expose full text when EXPOSE_FULL_TEXT is False."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        entry = MockConfigEntry(
            domain=DOMAIN, title="USCCB", data={}, unique_id=UNIQUE_ID
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        for entity_id in (
            "sensor.usccb_daily_readings_first_reading",
            "sensor.usccb_daily_readings_gospel",
        ):
            state = hass.states.get(entity_id)
            assert state is not None
            assert "text" not in state.attributes

        daily = hass.states.get("sensor.usccb_daily_readings_daily_mass")
        assert daily is not None
        sections = daily.attributes.get(ATTR_SECTIONS, [])
        assert sections
        blob = str(sections)
        assert "Synthetic gospel text" not in blob
        assert "Synthetic first reading text" not in blob