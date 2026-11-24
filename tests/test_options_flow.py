"""Tests for the options flow."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import (
    ATTR_SECTIONS,
    CONF_EXPOSE_FULL_TEXT,
    DOMAIN,
    UNIQUE_ID,
)


@pytest.mark.asyncio
async def test_options_flow_shows_saved_preference(hass, mock_usccb_feed) -> None:
    """Options flow displays the saved preference."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB Daily Readings",
        data={},
        options={CONF_EXPOSE_FULL_TEXT: True},
        unique_id=UNIQUE_ID,
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_can_enable_full_text(hass, mock_usccb_feed) -> None:
    """Options flow can enable full-text exposure."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB Daily Readings",
        data={},
        options={CONF_EXPOSE_FULL_TEXT: False},
        unique_id=UNIQUE_ID,
    )
    entry.add_to_hass(hass)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_EXPOSE_FULL_TEXT: True}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        updated = hass.config_entries.async_get_entry(entry.entry_id)
        assert updated is not None
        assert updated.options[CONF_EXPOSE_FULL_TEXT] is True

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert gospel.attributes.get("text") == "Synthetic gospel text."


@pytest.mark.asyncio
async def test_options_flow_can_disable_full_text(hass, mock_usccb_feed) -> None:
    """Options flow can disable full-text exposure and remove attributes."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB Daily Readings",
        data={},
        options={CONF_EXPOSE_FULL_TEXT: True},
        unique_id=UNIQUE_ID,
    )
    entry.add_to_hass(hass)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert gospel.attributes.get("text") == "Synthetic gospel text."

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_EXPOSE_FULL_TEXT: False}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert "text" not in gospel.attributes

        daily = hass.states.get("sensor.usccb_daily_readings_daily_mass")
        sections = daily.attributes.get(ATTR_SECTIONS, [])
        blob = str(sections)
        assert "Synthetic gospel text" not in blob


@pytest.mark.asyncio
async def test_legacy_entry_without_option_defaults_disabled(
    hass, mock_usccb_feed
) -> None:
    """Existing config entries without the setting default to disabled."""
    frozen = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB Daily Readings",
        data={},
        unique_id=UNIQUE_ID,
    )
    entry.add_to_hass(hass)
    with patch.object(dt_util, "now", return_value=dt_util.as_local(frozen)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        gospel = hass.states.get("sensor.usccb_daily_readings_gospel")
        assert gospel is not None
        assert "text" not in gospel.attributes
