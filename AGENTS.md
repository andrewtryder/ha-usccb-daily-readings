# Repository instructions

- Integration domain: `usccb_daily_readings` at `custom_components/usccb_daily_readings`.
- Runtime dependencies: none (`requirements: []` in `manifest.json`); use aiohttp via Home Assistant and stdlib parsing only.
- Tests pin `pytest-homeassistant==2026.11.3`; maintain at least 90% coverage on the integration package.
- Default public exposure is citations and metadata only (`EXPOSE_FULL_TEXT = False`).
- Run `./scripts/validate-local.sh` before merging; PR titles use Conventional Commits.
- Do not commit copyrighted lectionary full text in fixtures, diagnostics, or logs.
