"""Data models for USCCB daily Mass readings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class SectionType(StrEnum):
    """Liturgical section classification."""

    UNKNOWN = "unknown"
    ALLELUIA = "alleluia"
    ALTERNATIVE = "alternative"
    GOSPEL = "gospel"
    PSALM = "psalm"
    READING = "reading"
    SEQUENCE = "sequence"


ACCLAMATION_PATTERNS = (
    "alleluia",
    "verse before the gospel",
    "gospel acclamation",
    "acclamation",
    "praise to you, lord jesus christ",
    "glory and praise to you",
    "glory to you, word of god",
)


def section_type_from_header(header: str) -> SectionType:
    """Classify a section from its USCCB header label."""
    lower = header.strip().lower()
    if any(pattern in lower for pattern in ACCLAMATION_PATTERNS):
        return SectionType.ALLELUIA
    if "gospel" in lower:
        return SectionType.GOSPEL
    if "psalm" in lower:
        return SectionType.PSALM
    if "sequence" in lower:
        return SectionType.SEQUENCE
    if "reading" in lower or "epistle" in lower:
        return SectionType.READING
    if "alternative" in lower or " or " in f" {lower} ":
        return SectionType.ALTERNATIVE
    return SectionType.UNKNOWN


def reading_number_from_header(header: str) -> int | None:
    """Extract Reading 1 / Reading 2 style numbering when present."""
    lower = header.lower()
    for marker in ("reading 1", "reading i", "reading one"):
        if marker in lower:
            return 1
    for marker in ("reading 2", "reading ii", "reading two"):
        if marker in lower:
            return 2
    return None


@dataclass(frozen=True, slots=True)
class ScriptureCitation:
    """A scripture reference with an optional USCCB link."""

    display: str
    url: str | None = None
    book: str | None = None


@dataclass(frozen=True, slots=True)
class ReadingSection:
    """One liturgical section within a daily Mass."""

    section_type: SectionType
    header: str
    citations: tuple[ScriptureCitation, ...]
    text: str
    sequence: int
    alternatives: tuple[ReadingSection, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MemorialLink:
    """Optional memorial variant linked from the RSS description."""

    title: str
    url: str


@dataclass(frozen=True, slots=True)
class DailyMass:
    """Readings for one liturgical day."""

    date: date
    celebration: str
    source_url: str
    sections: tuple[ReadingSection, ...]
    language: str
    translation: str
    copyright: str
    attribution: str
    memorial_links: tuple[MemorialLink, ...] = field(default_factory=tuple)

    def section_by_type(
        self, section_type: SectionType, *, reading_number: int | None = None
    ) -> ReadingSection | None:
        """Return the first matching section, optionally by reading number."""
        for section in self.sections:
            if section.section_type != section_type:
                continue
            if reading_number is not None and section_type == SectionType.READING:
                number = reading_number_from_header(section.header)
                if number != reading_number:
                    continue
            return section
        return None

    def first_reading(self) -> ReadingSection | None:
        """Return the first reading section."""
        return self.section_by_type(SectionType.READING, reading_number=1) or next(
            (
                section
                for section in self.sections
                if section.section_type == SectionType.READING
            ),
            None,
        )

    def second_reading(self) -> ReadingSection | None:
        """Return the second reading section when present."""
        return self.section_by_type(SectionType.READING, reading_number=2)

    def primary_citation(self, section: ReadingSection | None) -> str | None:
        """Return a display citation for a section."""
        if section is None or not section.citations:
            return None
        return section.citations[0].display
