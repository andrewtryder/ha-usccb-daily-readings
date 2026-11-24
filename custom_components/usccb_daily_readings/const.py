"""Constants for the USCCB Daily Readings integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry

DOMAIN = "usccb_daily_readings"
UNIQUE_ID = "usccb_daily_readings"
MANUFACTURER = "United States Conference of Catholic Bishops"

FEED_URL = "https://bible.usccb.org/readings.rss"
DOCUMENTATION_URL = "https://github.com/andrewtryder/ha-usccb-daily-readings"

API_TIMEOUT = 30
MAX_RESPONSE_BYTES = 256 * 1024
UPDATE_INTERVAL = timedelta(hours=1)

CONF_EXPOSE_FULL_TEXT = "expose_full_text"
DEFAULT_EXPOSE_FULL_TEXT = False

ATTR_DATE = "date"
ATTR_REFERENCE = "reference"
ATTR_CITATIONS = "citations"
ATTR_SOURCE_URL = "source_url"
ATTR_SECTION_TYPE = "section_type"
ATTR_SECTION_AVAILABLE = "section_available"
ATTR_TRANSLATION = "translation"
ATTR_COPYRIGHT = "copyright"
ATTR_ATTRIBUTION = "attribution"
ATTR_TEXT = "text"
ATTR_ALTERNATIVES = "alternatives"
ATTR_MEMORIAL_LINKS = "memorial_links"
ATTR_SECTIONS = "sections"

INTEGRATION_VERSION = "0.1.0"


def expose_full_text_enabled(entry: ConfigEntry) -> bool:
    """Return whether full reading text should appear in sensor attributes."""
    if CONF_EXPOSE_FULL_TEXT in entry.options:
        return bool(entry.options[CONF_EXPOSE_FULL_TEXT])
    if CONF_EXPOSE_FULL_TEXT in entry.data:
        return bool(entry.data[CONF_EXPOSE_FULL_TEXT])
    return DEFAULT_EXPOSE_FULL_TEXT


def user_agent() -> str:
    """Return the HTTP User-Agent for USCCB feed requests."""
    return (
        "USCCB-Daily-Readings-Home-Assistant/"
        f"{INTEGRATION_VERSION} (+{DOCUMENTATION_URL})"
    )
