# USCCB Daily Readings for Home Assistant

<img src="custom_components/usccb_daily_readings/brand/icon.png" alt="USCCB Daily Readings" width="100">

Daily Mass reading citations from the official USCCB English RSS feed—pure Python, no API key, no browser, no separate service.

[![Validation on main](https://img.shields.io/github/actions/workflow/status/andrewtryder/ha-usccb-daily-readings/validate.yml?branch=main&style=flat-square&label=validation)](https://github.com/andrewtryder/ha-usccb-daily-readings/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/andrewtryder/ha-usccb-daily-readings?style=flat-square)](LICENSE)
[![HACS custom integration](https://img.shields.io/badge/HACS-Custom-orange?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrewtryder&repository=ha-usccb-daily-readings&category=integration)

## Features

- Official source: [USCCB daily readings RSS](https://bible.usccb.org/readings.rss)
- One service device with six sensors (celebration, readings, psalm, acclamation, gospel)
- Citations and links in sensor states; fuller metadata in attributes
- Refreshes at local midnight and retries hourly until today's readings appear
- No account, credentials, or extra Python packages at runtime

## Requirements

- Home Assistant **2025.2.0** or newer
- HACS, or the Home Assistant **Marketplace** on **2026.11+**

## Install with HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrewtryder&repository=ha-usccb-daily-readings&category=integration)

1. Add this repository as a custom integration in HACS (Integration category).
2. Install **USCCB Daily Readings** and restart Home Assistant.

Manual install: copy `custom_components/usccb_daily_readings` into your configuration directory and restart.

## Setup

[![Open your Home Assistant instance and start setting up USCCB Daily Readings.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=usccb_daily_readings)

1. **Settings → Devices & services → Add integration**
2. Search for **USCCB Daily Readings**
3. Confirm—no further options in v0.1.0

## Sensors

| Entity | State |
|--------|--------|
| Daily Mass | Celebration title |
| First Reading | Scripture citation |
| Responsorial Psalm | Psalm citation |
| Second Reading | Citation (or `unknown` when absent) |
| Gospel Acclamation | Citation or section label |
| Gospel | Scripture citation |

Attributes include date, source URL, section type, translation, copyright, and memorial links when present. Full reading text is parsed internally but **not** exposed in attributes by default (see [Copyright](#copyright-and-attribution)).

### Entity IDs (default install)

After setup, entities use the `usccb_daily_readings` slug and these keys:

| Entity ID | Friendly name (typical) |
|-----------|-------------------------|
| `sensor.usccb_daily_readings_daily_mass` | Daily Mass |
| `sensor.usccb_daily_readings_first_reading` | First Reading |
| `sensor.usccb_daily_readings_responsorial_psalm` | Responsorial Psalm |
| `sensor.usccb_daily_readings_second_reading` | Second Reading |
| `sensor.usccb_daily_readings_gospel_acclamation` | Gospel Acclamation |
| `sensor.usccb_daily_readings_gospel` | Gospel |

Useful attributes on reading sensors (v0.1.0 defaults): `date`, `reference`, `citations`, `source_url`, `section_type`, `section_available`, `translation`, `copyright`, `attribution`. The `text` attribute is omitted unless full-text exposure is explicitly enabled in code (`EXPOSE_FULL_TEXT`).

### Dashboard example

```yaml
type: entities
title: Today's Mass
entities:
  - entity: sensor.usccb_daily_readings_daily_mass
  - entity: sensor.usccb_daily_readings_first_reading
  - entity: sensor.usccb_daily_readings_responsorial_psalm
  - entity: sensor.usccb_daily_readings_second_reading
  - entity: sensor.usccb_daily_readings_gospel_acclamation
  - entity: sensor.usccb_daily_readings_gospel
```

## Update behavior

Readings are selected using Home Assistant's configured time zone. The integration matches today's liturgical date to the feed item link (`MMDDYY`). If today's readings are not yet in the RSS window, sensors stay **unavailable** until the next hourly retry—yesterday's text is never shown as today's.

Publication timing varies; do not rely on a fixed early-morning Eastern schedule.

## RSS limitations

The feed contains roughly the ten most recent days—not a full lectionary archive. Historical and future dates outside the feed are not supported in v0.1.0.

## Copyright and attribution

Text in the USCCB feed is copyrighted (NABRE / Lectionary for Mass). This project is **not affiliated with or endorsed by** the USCCB. Sensors emphasize citations and links to the official site. Enabling full text in Home Assistant attributes requires appropriate permissions from the copyright holders.

## Development

```bash
uv sync --locked
uv run --locked pytest
./scripts/validate-local.sh
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE). USCCB reading text remains subject to USCCB copyright.
