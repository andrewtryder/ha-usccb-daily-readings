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
