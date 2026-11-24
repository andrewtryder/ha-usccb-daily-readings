"""Config flow for USCCB Daily Readings."""

from __future__ import annotations

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, UNIQUE_ID


class UsccbDailyReadingsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single confirmation step; readings come from the official USCCB English RSS feed."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Confirm setup."""
        await self.async_set_unique_id(UNIQUE_ID)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title="USCCB Daily Readings",
                data={},
            )
        return self.async_show_form(step_id="user")
