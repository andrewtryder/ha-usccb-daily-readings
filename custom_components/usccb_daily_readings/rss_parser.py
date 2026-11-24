"""Parse the USCCB daily readings RSS feed."""

from __future__ import annotations

import html
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser

from .const import MANUFACTURER
from .models import (
    DailyMass,
    MemorialLink,
    ReadingSection,
    ScriptureCitation,
    section_type_from_header,
)

_LOGGER = logging.getLogger(__name__)

_READINGS_URL_RE = re.compile(
    r"/bible/readings/(?P<month>\d{2})(?P<day>\d{2})(?P<year>\d{2})",
    re.IGNORECASE,
)
_BIBLE_LINK_RE = re.compile(r"/bible/([^/?#]+)", re.IGNORECASE)
_ANCHOR_RE = re.compile(
    r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>',
    re.IGNORECASE | re.DOTALL,
)
_H4_RE = re.compile(r"<h4[^>]*>(.*?)</h4>", re.IGNORECASE | re.DOTALL)
_POETRY_RE = re.compile(
    r'<div[^>]*class="[^"]*poetry[^"]*"[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)


class USCCBParseError(Exception):
    """Raised when RSS or description content cannot be parsed."""


def parse_link_date(url: str) -> date | None:
    """Extract the liturgical date embedded in a readings page URL."""
    match = _READINGS_URL_RE.search(url)
    if not match:
        return None
    month = int(match.group("month"))
    day = int(match.group("day"))
    year = 2000 + int(match.group("year"))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def book_from_bible_url(url: str) -> str | None:
    """Resolve a display book name from a USCCB bible URL slug."""
    match = _BIBLE_LINK_RE.search(url)
    if not match:
        return None
    slug = match.group(1).replace("-", " ")
    return slug.title()


def _strip_tags(fragment: str) -> str:
    """Return plain text from a small HTML fragment."""
    parser = _PlainTextParser()
    parser.feed(fragment)
    parser.close()
    return parser.text


class _PlainTextParser(HTMLParser):
    """Collect text nodes from HTML, preserving line breaks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    @property
    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [line.strip() for line in raw.splitlines()]
        compact = "\n".join(line for line in lines if line)
        return re.sub(r"\n{3,}", "\n\n", compact).strip()

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p"}:
            self._parts.append("\n")


def _validate_xml_safe(xml_bytes: bytes) -> None:
    """Reject unsafe XML before parsing."""
    probe = xml_bytes[:8192].upper()
    if b"<!DOCTYPE" in probe or b"<!ENTITY" in probe:
        msg = "Unsafe XML constructs are not allowed"
        raise USCCBParseError(msg)


def _local_tag(tag: str) -> str:
    """Return the local element name without namespace."""
    if "}" in tag:
        return tag.rpartition("}")[2]
    return tag


def _channel_text(root: ET.Element, name: str) -> str:
    """Read text from the first child element under channel."""
    channel = root.find("channel")
    if channel is None:
        return ""
    for child in channel:
        if _local_tag(child.tag) == name:
            return (child.text or "").strip()
    return ""


def parse_pub_date(value: str) -> date | None:
    """Parse RSS pubDate to a calendar date."""
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
    ):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.date()
    return None


def _parse_citations(header_html: str) -> tuple[str, tuple[ScriptureCitation, ...]]:
    """Split the h4 header label from scripture citations."""
    citations: list[ScriptureCitation] = []
    label = _strip_tags(header_html)
    for href, text in _ANCHOR_RE.findall(header_html):
        display = html.unescape(text).strip()
        book = book_from_bible_url(href)
        citations.append(ScriptureCitation(display=display, url=href, book=book))
        label = label.replace(display, "").strip()
    label = re.sub(r"\s{2,}", " ", label).strip()
    return label, tuple(citations)


def _parse_memorial_links(description_html: str) -> tuple[MemorialLink, ...]:
    """Parse optional memorial links from the description preamble."""
    links: list[MemorialLink] = []
    for href, text in _ANCHOR_RE.findall(description_html):
        if "memorial" not in text.lower() and "memorial" not in href.lower():
            continue
        links.append(MemorialLink(title=html.unescape(text).strip(), url=href))
    return tuple(links)


def _parse_sections(description_html: str) -> tuple[ReadingSection, ...]:
    """Parse reading sections from escaped HTML in an RSS description."""
    decoded = html.unescape(description_html)
    headers = list(_H4_RE.finditer(decoded))
    sections: list[ReadingSection] = []
    for index, header_match in enumerate(headers):
        header_html = header_match.group(1)
        label, citations = _parse_citations(header_html)
        start = header_match.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(decoded)
        block = decoded[start:end]
        poetry_match = _POETRY_RE.search(block)
        body_html = poetry_match.group(1) if poetry_match else block
        text = _strip_tags(body_html)
        section = ReadingSection(
            section_type=section_type_from_header(label),
            header=label,
            citations=citations,
            text=text,
            sequence=index,
        )
        sections.append(section)
    return tuple(sections)


@dataclass(frozen=True, slots=True)
class UsccbFeed:
    """Parsed RSS channel metadata and daily Mass items."""

    copyright: str
    language: str
    translation: str
    items: tuple[DailyMass, ...]


def parse_feed(xml_bytes: bytes) -> UsccbFeed:
    """Parse the USCCB readings RSS envelope and items."""
    _validate_xml_safe(xml_bytes)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as err:
        raise USCCBParseError("Invalid RSS XML") from err

    if _local_tag(root.tag).lower() != "rss":
        msg = "Root element is not an RSS feed"
        raise USCCBParseError(msg)

    channel = root.find("channel")
    if channel is None:
        raise USCCBParseError("RSS channel is missing")

    copyright_text = ""
    language = "en"
    for child in channel:
        tag = _local_tag(child.tag).lower()
        if tag == "copyright":
            copyright_text = (child.text or "").strip()
        elif tag == "language":
            language = (child.text or "en").strip()

    translation = (
        _channel_text(root, "description") or "New American Bible Revised Edition"
    )
    masses: list[DailyMass] = []
    for child in channel:
        if _local_tag(child.tag).lower() != "item":
            continue
        item: dict[str, str] = {}
        for element in child:
            item[_local_tag(element.tag).lower()] = (element.text or "").strip()
        link = item.get("link", "")
        liturgical_date = parse_link_date(link)
        if liturgical_date is None and (pub := item.get("pubdate", "")):
            liturgical_date = parse_pub_date(pub)
        if liturgical_date is None:
            _LOGGER.debug("Skipping RSS item without a parseable date: %s", link)
            continue
        description = item.get("description", "")
        masses.append(
            DailyMass(
                date=liturgical_date,
                celebration=item.get("title", ""),
                source_url=link,
                sections=_parse_sections(description),
                language=language,
                translation=translation,
                copyright=copyright_text,
                attribution=MANUFACTURER,
                memorial_links=_parse_memorial_links(description),
            )
        )

    if not masses:
        raise USCCBParseError("RSS feed contains no readable daily items")

    return UsccbFeed(
        copyright=copyright_text,
        language=language,
        translation=translation,
        items=tuple(masses),
    )


def mass_for_date(feed: UsccbFeed, target: date) -> DailyMass | None:
    """Return the daily Mass matching a calendar date."""
    for mass in feed.items:
        if mass.date == target:
            return mass
    return None
