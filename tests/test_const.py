"""Tests for integration constants helpers."""

from __future__ import annotations

from pytest_homeassistant.common import MockConfigEntry

from custom_components.usccb_daily_readings.const import (
    CONF_EXPOSE_FULL_TEXT,
    DEFAULT_EXPOSE_FULL_TEXT,
    DOMAIN,
    expose_full_text_enabled,
)


def test_expose_full_text_defaults_when_missing() -> None:
    """Missing options and data default to disabled."""
    entry = MockConfigEntry(domain=DOMAIN, title="USCCB", data={}, unique_id="usccb")
    assert expose_full_text_enabled(entry) is DEFAULT_EXPOSE_FULL_TEXT


def test_expose_full_text_reads_options() -> None:
    """Options take precedence for the runtime preference."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB",
        data={CONF_EXPOSE_FULL_TEXT: False},
        options={CONF_EXPOSE_FULL_TEXT: True},
        unique_id="usccb",
    )
    assert expose_full_text_enabled(entry) is True


def test_expose_full_text_reads_legacy_data() -> None:
    """Legacy data-only preference is honored."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="USCCB",
        data={CONF_EXPOSE_FULL_TEXT: True},
        unique_id="usccb",
    )
    assert expose_full_text_enabled(entry) is True
