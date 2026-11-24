"""Config flow for USCCB Daily Readings."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_EXPOSE_FULL_TEXT,
    DEFAULT_EXPOSE_FULL_TEXT,
    DOMAIN,
    UNIQUE_ID,
    expose_full_text_enabled,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_EXPOSE_FULL_TEXT, default=DEFAULT_EXPOSE_FULL_TEXT
        ): cv.boolean,
    }
)


class UsccbDailyReadingsOptionsFlowHandler(OptionsFlow):
    """Handle USCCB Daily Readings options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage full-text exposure."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EXPOSE_FULL_TEXT,
                        default=expose_full_text_enabled(self._config_entry),
                    ): cv.boolean,
                }
            ),
        )


class UsccbDailyReadingsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single confirmation step; readings come from the official USCCB English RSS feed."""

    VERSION = 1

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UsccbDailyReadingsOptionsFlowHandler:
        """Return the options flow handler."""
        return UsccbDailyReadingsOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm setup."""
        await self.async_set_unique_id(UNIQUE_ID)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title="USCCB Daily Readings",
                data={},
                options={
                    CONF_EXPOSE_FULL_TEXT: user_input.get(
                        CONF_EXPOSE_FULL_TEXT, DEFAULT_EXPOSE_FULL_TEXT
                    )
                },
            )
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)
