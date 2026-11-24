"""Diagnostics for USCCB Daily Readings."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import FEED_URL, INTEGRATION_VERSION
from .coordinator import UsccbConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: UsccbConfigEntry
) -> dict[str, Any]:
    """Return non-sensitive diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    mass = data.mass if data else None
    section_types = [section.section_type for section in mass.sections] if mass else []
    return {
        "integration_version": INTEGRATION_VERSION,
        "feed_url": FEED_URL,
        "last_successful_refresh": data.last_refresh.isoformat() if data else None,
        "liturgical_date": mass.date.isoformat() if mass else None,
        "celebration": mass.celebration if mass else None,
        "section_types": section_types,
        "feed_item_count": data.feed_item_count if data else None,
        "today_available": mass is not None,
        "last_update_success": coordinator.last_update_success,
        "last_exception": (
            str(coordinator.last_exception) if coordinator.last_exception else None
        ),
    }
