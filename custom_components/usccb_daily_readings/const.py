"""Constants for the USCCB Daily Readings integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "usccb_daily_readings"
UNIQUE_ID = "usccb_daily_readings"
MANUFACTURER = "United States Conference of Catholic Bishops"

FEED_URL = "https://bible.usccb.org/readings.rss"
DOCUMENTATION_URL = "https://github.com/andrewtryder/ha-usccb-daily-readings"

API_TIMEOUT = 30
MAX_RESPONSE_BYTES = 256 * 1024
UPDATE_INTERVAL = timedelta(hours=1)

# Parsed internally; omit from public state attributes unless explicitly enabled.
EXPOSE_FULL_TEXT = False

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


def user_agent() -> str:
    """Return the HTTP User-Agent for USCCB feed requests."""
    return (
        "USCCB-Daily-Readings-Home-Assistant/"
        f"{INTEGRATION_VERSION} (+{DOCUMENTATION_URL})"
    )
