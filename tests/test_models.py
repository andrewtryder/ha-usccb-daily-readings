"""Tests for data models."""

from __future__ import annotations

from datetime import date

from custom_components.usccb_daily_readings.models import (
    DailyMass,
    ReadingSection,
    ScriptureCitation,
    SectionType,
    reading_number_from_header,
)


def _mass(sections: tuple[ReadingSection, ...]) -> DailyMass:
    return DailyMass(
        date=date(2026, 11, 24),
        celebration="Test",
        source_url="https://example.org",
        sections=sections,
        language="en",
        translation="NABRE",
        copyright="",
        attribution="USCCB",
    )


def test_reading_number_from_header() -> None:
    """Detect numbered readings in headers."""
    assert reading_number_from_header("Reading 1") == 1
    assert reading_number_from_header("Reading 2") == 2
    assert reading_number_from_header("Gospel") is None


def test_second_reading_selection() -> None:
    """Return only the second numbered reading."""
    sections = (
        ReadingSection(
            section_type=SectionType.READING,
            header="Reading 1",
            citations=(ScriptureCitation("Rom 1:1"),),
            text="",
            sequence=0,
        ),
        ReadingSection(
            section_type=SectionType.READING,
            header="Reading 2",
            citations=(ScriptureCitation("Rom 13:11"),),
            text="",
            sequence=1,
        ),
    )
    mass = _mass(sections)
    assert mass.second_reading() is not None
    assert mass.second_reading().citations[0].display == "Rom 13:11"
