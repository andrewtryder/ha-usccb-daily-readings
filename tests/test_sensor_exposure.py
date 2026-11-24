"""Verify reading text exposure respects the user configuration."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import (
    ATTR_SECTIONS,
    CONF_EXPOSE_FULL_TEXT,
    DOMAIN,
    UNIQUE_ID,
)
from custom_components.usccb_daily_readings.sensor import UsccbReadingSensor


@pytest.mark.asyncio
async def test_reading_entities_omit_text_when_disabled(hass, mock_usccb_feed) -> None:
    """Reading sensors must not expose full text when the option is disabled."""
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


@pytest.mark.asyncio
async def test_reading_entities_expose_text_when_enabled(hass, mock_usccb_feed) -> None:
    """Reading sensors expose text when the option is enabled."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="USCCB",
            data={},
            options={CONF_EXPOSE_FULL_TEXT: True},
            unique_id=UNIQUE_ID,
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        first = hass.states.get("sensor.usccb_daily_readings_first_reading")
        assert first is not None
        assert first.state == "Romans 1:1-7"
        assert first.attributes["text"] == "Synthetic first reading text."

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert gospel.state == "Luke 10:21-24"
        assert gospel.attributes["text"] == "Synthetic gospel text."

        daily = hass.states.get("sensor.usccb_daily_readings_daily_mass")
        sections = daily.attributes.get(ATTR_SECTIONS, [])
        assert any(section.get("text") for section in sections)


@pytest.mark.asyncio
async def test_citations_unchanged_in_both_modes(hass, mock_usccb_feed) -> None:
    """Scripture citations remain the sensor state regardless of text exposure."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)

    async def states_for(enabled: bool) -> dict[str, str]:
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="USCCB",
            data={},
            options={CONF_EXPOSE_FULL_TEXT: enabled},
            unique_id=UNIQUE_ID,
        )
        entry.add_to_hass(hass)
        with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
            return {
                "first_reading": hass.states.get(
                    "sensor.usccb_daily_readings_first_reading"
                ).state,
                "gospel": hass.states.get("sensor.usccb_daily_readings_gospel").state,
            }

    disabled = await states_for(False)
    await hass.config_entries.async_remove(
        hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    await hass.async_block_till_done()
    enabled = await states_for(True)
    assert disabled == enabled


def test_recorder_excludes_large_attributes() -> None:
    """Full reading bodies are excluded from Recorder history."""
    assert "text" in UsccbReadingSensor._unrecorded_attributes
    assert "sections" in UsccbReadingSensor._unrecorded_attributes
