"""Async HTTP client for the USCCB readings RSS feed."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from aiohttp import ClientError, ClientResponseError, ContentTypeError

from .const import API_TIMEOUT, FEED_URL, MAX_RESPONSE_BYTES, user_agent
from .rss_parser import UsccbFeed, USCCBParseError, parse_feed

if TYPE_CHECKING:
    from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

_CHALLENGE_HINTS = re.compile(
    r"(obolus|access denied|captcha|please enable javascript)",
    re.IGNORECASE,
)
_ALLOWED_CONTENT_TYPES = (
    "application/rss+xml",
    "application/xml",
    "text/xml",
    "application/atom+xml",
)


class USCCBError(Exception):
    """Base error for USCCB feed access."""


class USCCBConnectionError(USCCBError):
    """Connection or transport error."""


class USCCBResponseError(USCCBError):
    """Unexpected HTTP response."""


class USCCBOversizeError(USCCBError):
    """Response exceeded the configured size limit."""


class USCCBClient:
    """Fetch and validate the USCCB daily readings RSS feed."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize with a Home Assistant-managed aiohttp session."""
        self._session = session

    async def fetch_feed(self) -> UsccbFeed:
        """Retrieve and parse the official RSS feed."""
        try:
            async with asyncio.timeout(API_TIMEOUT):
                async with self._session.get(
                    FEED_URL,
                    headers={"User-Agent": user_agent()},
                ) as response:
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "unknown")
                        msg = f"USCCB feed rate limited (Retry-After: {retry_after})"
                        raise USCCBConnectionError(msg)
                    response.raise_for_status()
                    content_type = (response.headers.get("Content-Type") or "").lower()
                    if not any(
                        allowed in content_type for allowed in _ALLOWED_CONTENT_TYPES
                    ):
                        msg = f"Unexpected content type: {content_type or 'unknown'}"
                        raise USCCBResponseError(msg)
                    raw = await response.read()
        except TimeoutError as err:
            raise USCCBConnectionError("USCCB feed request timed out") from err
        except ClientResponseError as err:
            raise USCCBResponseError(f"USCCB feed HTTP error: {err.status}") from err
        except ContentTypeError as err:
            raise USCCBResponseError("USCCB feed response could not be read") from err
        except ClientError as err:
            raise USCCBConnectionError("USCCB feed connection failed") from err

        if len(raw) > MAX_RESPONSE_BYTES:
            raise USCCBOversizeError(
                f"USCCB feed exceeded {MAX_RESPONSE_BYTES} bytes ({len(raw)})"
            )

        preview = raw[:2048].decode("utf-8", errors="ignore")
        if _CHALLENGE_HINTS.search(preview):
            raise USCCBResponseError("USCCB feed returned a challenge page")

        try:
            return parse_feed(raw)
        except USCCBParseError as err:
            raise USCCBResponseError(str(err)) from err
