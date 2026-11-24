# Contributing to USCCB Daily Readings

## Prerequisites

- Python 3.14
- Git
- [uv](https://docs.astral.sh/uv/)

## Local setup

```bash
uv sync --locked
uv run --locked pre-commit install
```

## Validation

Run the full local contract:

```bash
./scripts/validate-local.sh
```

Individual checks:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest --disable-socket --allow-unix-socket -p no:cacheprovider
```

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) (lowercase type). Release Please owns version bumps and `CHANGELOG.md`.

## Releases

The `Release Please` workflow needs a repository secret `RELEASE_PLEASE_TOKEN` (fine-grained PAT with `contents` and `pull-requests` on this repo). You can reuse the same token as other `ha-*` integrations; keep it in a local `.env` (never commit).

After creating the GitHub repository:

```bash
gh secret set RELEASE_PLEASE_TOKEN --repo andrewtryder/ha-usccb-daily-readings \
  < <(grep '^RELEASE_PLEASE_TOKEN=' /path/to/.env | cut -d= -f2-)
```

## Brand assets

Requires `rsvg-convert` on your PATH (`brew install librsvg` on macOS).

```bash
uv run python scripts/prepare_brand_assets.py
```

Sources: `custom_components/usccb_daily_readings/brand/icon.svg` → `icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`.
