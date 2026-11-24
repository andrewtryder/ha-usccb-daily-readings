"""Sensors for USCCB daily Mass readings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ATTRIBUTION,
    ATTR_CITATIONS,
    ATTR_COPYRIGHT,
    ATTR_DATE,
    ATTR_MEMORIAL_LINKS,
    ATTR_REFERENCE,
    ATTR_SECTION_AVAILABLE,
    ATTR_SECTION_TYPE,
    ATTR_SECTIONS,
    ATTR_SOURCE_URL,
    ATTR_TEXT,
    ATTR_TRANSLATION,
    DOMAIN,
    EXPOSE_FULL_TEXT,
    MANUFACTURER,
)
from .coordinator import DailyReadingsCoordinator, UsccbConfigEntry
from .models import DailyMass, ReadingSection, SectionType


@dataclass(frozen=True, kw_only=True)
class UsccbSensorDescription(SensorEntityDescription):
    """Entity description with a section resolver."""

    resolve: Callable[[DailyMass], ReadingSection | None]
    state_from_mass: Callable[[DailyMass], str | None] | None = None


def _citations(section: ReadingSection | None) -> list[str]:
    if section is None:
        return []
    return [citation.display for citation in section.citations]


def _section_attrs(section: ReadingSection | None) -> dict[str, Any]:
    if section is None:
        return {
            ATTR_SECTION_AVAILABLE: False,
            ATTR_REFERENCE: None,
            ATTR_CITATIONS: [],
            ATTR_SECTION_TYPE: None,
        }
    attrs: dict[str, Any] = {
        ATTR_SECTION_AVAILABLE: True,
        ATTR_REFERENCE: section.citations[0].display if section.citations else None,
        ATTR_CITATIONS: _citations(section),
        ATTR_SECTION_TYPE: section.section_type,
    }
    if EXPOSE_FULL_TEXT and section.text:
        attrs[ATTR_TEXT] = section.text
    return attrs


SENSOR_DESCRIPTIONS: tuple[UsccbSensorDescription, ...] = (
    UsccbSensorDescription(
        key="daily_mass",
        translation_key="daily_mass",
        icon="mdi:church",
        resolve=lambda mass: None,
        state_from_mass=lambda mass: mass.celebration,
    ),
    UsccbSensorDescription(
        key="first_reading",
        translation_key="first_reading",
        icon="mdi:book-open-page-variant",
        resolve=lambda mass: mass.first_reading(),
    ),
    UsccbSensorDescription(
        key="responsorial_psalm",
        translation_key="responsorial_psalm",
        icon="mdi:music-note",
        resolve=lambda mass: mass.section_by_type(SectionType.PSALM),
    ),
    UsccbSensorDescription(
        key="second_reading",
        translation_key="second_reading",
        icon="mdi:book-open-page-variant-outline",
        resolve=lambda mass: mass.second_reading(),
    ),
    UsccbSensorDescription(
        key="gospel_acclamation",
        translation_key="gospel_acclamation",
        icon="mdi:format-quote-close",
        resolve=lambda mass: mass.section_by_type(SectionType.ALLELUIA),
        state_from_mass=lambda mass: (
            mass.primary_citation(mass.section_by_type(SectionType.ALLELUIA))
            or "Gospel Acclamation"
        ),
    ),
    UsccbSensorDescription(
        key="gospel",
        translation_key="gospel",
        icon="mdi:book-cross",
        resolve=lambda mass: mass.section_by_type(SectionType.GOSPEL),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UsccbConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up USCCB reading sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        UsccbReadingSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class UsccbReadingSensor(CoordinatorEntity[DailyReadingsCoordinator], SensorEntity):
    """Sensor for one liturgical reading section or celebration title."""

    _attr_has_entity_name = True
    entity_description: UsccbSensorDescription

    def __init__(
        self,
        coordinator: DailyReadingsCoordinator,
        description: UsccbSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="USCCB Daily Readings",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://bible.usccb.org/bible/readings",
        )

    @property
    def available(self) -> bool:
        """Return False when today's readings failed to load."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def native_value(self) -> str | None:
        """Return the sensor state."""
        if not self.available:
            return None
        mass = self.coordinator.data.mass
        if self.entity_description.state_from_mass is not None:
            value = self.entity_description.state_from_mass(mass)
            return value or STATE_UNKNOWN
        section = self.entity_description.resolve(mass)
        if section is None:
            return STATE_UNKNOWN
        return mass.primary_citation(section) or section.header or STATE_UNKNOWN

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return reading metadata without copyrighted text by default."""
        if not self.available:
            return {}
        mass = self.coordinator.data.mass
        section = self.entity_description.resolve(mass)
        attrs: dict[str, Any] = {
            ATTR_DATE: mass.date.isoformat(),
            ATTR_SOURCE_URL: mass.source_url,
            ATTR_TRANSLATION: mass.translation,
            ATTR_COPYRIGHT: mass.copyright,
            ATTR_ATTRIBUTION: mass.attribution,
            **_section_attrs(section),
        }
        if self.entity_description.key == "daily_mass":
            attrs[ATTR_SECTIONS] = [
                {
                    "header": item.header,
                    "type": item.section_type,
                    "citations": _citations(item),
                }
                for item in mass.sections
            ]
            attrs[ATTR_MEMORIAL_LINKS] = [
                {"title": link.title, "url": link.url} for link in mass.memorial_links
            ]
        return attrs
