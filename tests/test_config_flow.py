"""Tests for the config flow."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import (
    CONF_EXPOSE_FULL_TEXT,
    DEFAULT_EXPOSE_FULL_TEXT,
    DOMAIN,
    UNIQUE_ID,
)


@pytest.mark.asyncio
async def test_user_step_defaults_to_disabled(hass) -> None:
    """Initial config flow defaults full-text exposure to disabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert CONF_EXPOSE_FULL_TEXT in result["data_schema"].schema
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "USCCB Daily Readings"
    assert result["result"].unique_id == UNIQUE_ID
    assert result["result"].options[CONF_EXPOSE_FULL_TEXT] is DEFAULT_EXPOSE_FULL_TEXT


@pytest.mark.asyncio
async def test_user_step_can_enable_full_text(hass) -> None:
    """Initial setup can enable full-text exposure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_EXPOSE_FULL_TEXT: True}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].options[CONF_EXPOSE_FULL_TEXT] is True


@pytest.mark.asyncio
async def test_user_step_can_disable_full_text(hass) -> None:
    """Initial setup can keep full-text exposure disabled explicitly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_EXPOSE_FULL_TEXT: False}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].options[CONF_EXPOSE_FULL_TEXT] is False


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
