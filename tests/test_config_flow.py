"""Tests for the config flow."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import DOMAIN, UNIQUE_ID


@pytest.mark.asyncio
async def test_user_step_success(hass) -> None:
    """Create the config entry after confirmation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "USCCB Daily Readings"
    assert result["result"].unique_id == UNIQUE_ID


@pytest.mark.asyncio
async def test_duplicate_entry(hass) -> None:
    """Abort when the integration is already configured."""
    MockConfigEntry(
        domain=DOMAIN, data={}, unique_id=UNIQUE_ID, title="USCCB"
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
