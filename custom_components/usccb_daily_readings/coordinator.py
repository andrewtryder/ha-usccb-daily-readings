"""Coordinator that fetches today's USCCB daily Mass readings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import USCCBClient, USCCBError
from .const import DOMAIN, UPDATE_INTERVAL
from .models import DailyMass
from .rss_parser import mass_for_date

_LOGGER = logging.getLogger(__name__)

type UsccbConfigEntry = ConfigEntry[DailyReadingsCoordinator]


@dataclass(frozen=True, slots=True)
class DailyReadingsState:
    """Coordinator payload with feed metadata."""

    mass: DailyMass
    feed_item_count: int
    feed_copyright: str
    last_refresh: datetime


class DailyReadingsCoordinator(DataUpdateCoordinator[DailyReadingsState]):
    """Fetches readings when the local calendar day changes."""

    config_entry: UsccbConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: UsccbConfigEntry,
        client: USCCBClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self.client = client

    @property
    def today(self) -> date:
        """Return today's date in the Home Assistant timezone."""
        return dt_util.now().date()

    async def _async_update_data(self) -> DailyReadingsState:
        """Return today's Mass readings, retrying until the feed publishes them."""
        today = self.today
        if self.data is not None and self.data.mass.date == today:
            return self.data
        try:
            feed = await self.client.fetch_feed()
        except USCCBError as err:
            raise UpdateFailed(str(err)) from err

        mass = mass_for_date(feed, today)
        if mass is None:
            raise UpdateFailed(
                f"Today's readings ({today.isoformat()}) are not yet available in the USCCB RSS feed"
            )

        return DailyReadingsState(
            mass=mass,
            feed_item_count=len(feed.items),
            feed_copyright=feed.copyright,
            last_refresh=dt_util.utcnow(),
        )
