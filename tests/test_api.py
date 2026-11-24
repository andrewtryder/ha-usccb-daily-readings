"""Tests for the USCCB HTTP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.usccb_daily_readings.api import (
    USCCBClient,
    USCCBOversizeError,
    USCCBResponseError,
)


@pytest.mark.asyncio
async def test_fetch_feed_success(hass, mock_usccb_feed) -> None:
    """Return a parsed feed on success."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    client = USCCBClient(async_get_clientsession(hass))
    feed = await client.fetch_feed()
    assert len(feed.items) == 2


@pytest.mark.asyncio
async def test_fetch_feed_wrong_content_type(hass, aioclient_mock) -> None:
    """Reject unexpected content types."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=200,
        content=b"not xml",
        headers={"Content-Type": "text/html"},
    )
    client = USCCBClient(async_get_clientsession(hass))
    with pytest.raises(USCCBResponseError, match="content type"):
        await client.fetch_feed()


@pytest.mark.asyncio
async def test_fetch_feed_oversize(hass, aioclient_mock) -> None:
    """Reject oversized payloads."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=200,
        content=b"x" * 300_000,
        headers={"Content-Type": "application/rss+xml"},
    )
    client = USCCBClient(async_get_clientsession(hass))
    with pytest.raises(USCCBOversizeError):
        await client.fetch_feed()


@pytest.mark.asyncio
async def test_fetch_feed_challenge_page(hass, aioclient_mock) -> None:
    """Treat bot challenge pages as failures."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=200,
        content=b"<html>Please enable JavaScript and Obolus</html>",
        headers={"Content-Type": "application/rss+xml"},
    )
    client = USCCBClient(async_get_clientsession(hass))
    with pytest.raises(USCCBResponseError, match="challenge"):
        await client.fetch_feed()


@pytest.mark.asyncio
async def test_fetch_feed_rate_limited(hass, aioclient_mock) -> None:
    """Include Retry-After details for HTTP 429 responses."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from custom_components.usccb_daily_readings.api import USCCBConnectionError

    aioclient_mock.get(
        "https://bible.usccb.org/readings.rss",
        status=429,
        headers={"Content-Type": "application/rss+xml", "Retry-After": "120"},
    )
    client = USCCBClient(async_get_clientsession(hass))
    with pytest.raises(USCCBConnectionError, match="Retry-After: 120"):
        await client.fetch_feed()


@pytest.mark.asyncio
async def test_client_does_not_close_session() -> None:
    """The client must not own the aiohttp session."""
    session = MagicMock()
    session.get = AsyncMock()
    USCCBClient(session)
    session.close.assert_not_called()
