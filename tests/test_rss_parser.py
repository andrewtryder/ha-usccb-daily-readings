"""Tests for RSS parsing."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from custom_components.usccb_daily_readings.models import (
    SectionType,
    section_type_from_header,
)
from custom_components.usccb_daily_readings.rss_parser import (
    USCCBParseError,
    mass_for_date,
    parse_feed,
    parse_link_date,
)
from tests.fixtures import load_fixture_bytes

FIXTURE = Path(__file__).parent / "fixtures" / "rss" / "weekday_sample.xml"


def test_parse_link_date() -> None:
    """Parse MMDDYY dates from readings URLs."""
    assert parse_link_date("https://bible.usccb.org/bible/readings/112426.cfm") == date(
        2026, 11, 24
    )


def test_section_type_from_header() -> None:
    """Classify acclamation before gospel."""
    assert section_type_from_header("Alleluia") == SectionType.ALLELUIA
    assert section_type_from_header("Gospel Acclamation") == SectionType.ALLELUIA
    assert section_type_from_header("Gospel") == SectionType.GOSPEL


def test_parse_weekday_feed() -> None:
    """Parse a synthetic weekday item without a second reading."""
    feed = parse_feed(load_fixture_bytes(FIXTURE))
    assert len(feed.items) == 2
    mass = mass_for_date(feed, date(2026, 11, 24))
    assert mass is not None
    assert mass.celebration == "Monday of the First Week"
    assert mass.second_reading() is None
    assert mass.first_reading() is not None
    assert mass.section_by_type(SectionType.GOSPEL) is not None


def test_parse_sunday_second_reading() -> None:
    """Parse a Sunday item with a second reading."""
    feed = parse_feed(load_fixture_bytes(FIXTURE))
    mass = mass_for_date(feed, date(2026, 11, 23))
    assert mass is not None
    assert mass.second_reading() is not None


def test_reject_unsafe_xml() -> None:
    """Reject entity expansion constructs."""
    payload = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe "x">]><rss/>'
    with pytest.raises(USCCBParseError, match="Unsafe XML"):
        parse_feed(payload)


def test_reject_invalid_root() -> None:
    """Require an RSS root element."""
    with pytest.raises(USCCBParseError, match="not an RSS feed"):
        parse_feed(b"<feed></feed>")


def test_acclamation_without_citation() -> None:
    """Accept seasonal acclamation labels without scripture links."""
    fixture = Path(__file__).parent / "fixtures" / "rss" / "acclamation_label_only.xml"
    feed = parse_feed(load_fixture_bytes(fixture))
    mass = mass_for_date(feed, date(2026, 11, 25))
    assert mass is not None
    alleluia = mass.section_by_type(SectionType.ALLELUIA)
    assert alleluia is not None
    assert alleluia.citations == ()


def test_mass_for_date_out_of_order_items() -> None:
    """Select readings by link date regardless of item order."""
    payload = load_fixture_bytes(FIXTURE)
    start = payload.find(b"<item>")
    second = payload.find(b"<item>", start + 1)
    end = payload.rfind(b"</item>") + len(b"</item>")
    item1 = payload[start:second]
    item2 = payload[second:end]
    channel_end = payload.rfind(b"</channel>")
    swapped = payload[:start] + item2 + item1 + payload[channel_end:]
    mass_forward = mass_for_date(parse_feed(payload), date(2026, 11, 24))
    mass_swapped = mass_for_date(parse_feed(swapped), date(2026, 11, 24))
    assert mass_forward and mass_swapped
    assert mass_forward.celebration == mass_swapped.celebration
