"""USCCB Daily Readings integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from .api import USCCBClient
from .const import UPDATE_INTERVAL
from .coordinator import DailyReadingsCoordinator, UsccbConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: UsccbConfigEntry) -> bool:
    """Set up USCCB Daily Readings from a config entry."""
    coordinator = DailyReadingsCoordinator(
        hass, entry, USCCBClient(async_get_clientsession(hass))
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _LOGGER.info(
        "USCCB Daily Readings ready (poll interval %s)",
        UPDATE_INTERVAL,
    )

    async def _refresh_after_midnight(_now: datetime) -> None:
        _LOGGER.info("Local midnight — refreshing USCCB daily readings")
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_time_change(
            hass, _refresh_after_midnight, hour=0, minute=0, second=5
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UsccbConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
