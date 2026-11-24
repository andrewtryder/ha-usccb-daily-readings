#!/usr/bin/env python3
"""Optional REST smoke test for the disposable Home Assistant Docker stack.

Uses onboarding/login-flow auth only against a local dev instance (default
http://127.0.0.1:8123). Tokens are written to scripts/artifacts/ (gitignored).

Environment variables (optional):
  HA_SMOKE_URL — base URL (default http://127.0.0.1:8123)
  HA_SMOKE_USER / HA_SMOKE_PASSWORD — dev credentials after onboarding
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

DEFAULT_URL = "http://127.0.0.1:8123"
TOKEN_FILE = Path(__file__).resolve().parent / "artifacts" / "ha_smoke_token.txt"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=60)


async def main(argv: list[str] | None = None) -> int:
    """Run onboarding, config flow, entity, and diagnostics smoke checks."""
    args = _parse_args(argv)
    ha_url = args.url.rstrip("/")
    username = args.username
    password = args.password

    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        token = await _resolve_token(session, ha_url, username, password)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        entry_id = await _ensure_integration(session, ha_url, headers)
        if entry_id is None:
            return 1

        await asyncio.sleep(5)
        ok = await _print_entity_smoke(session, ha_url, headers)
        if not ok:
            return 1

        if not await _print_diagnostics(session, ha_url, headers, entry_id):
            return 1

        if args.reload:
            async with session.post(
                f"{ha_url}/api/config/config_entries/entry/{entry_id}/reload",
                headers=headers,
            ) as resp:
                print("reload_status:", resp.status)

        if args.unload:
            await asyncio.sleep(2)
            async with session.delete(
                f"{ha_url}/api/config/config_entries/entry/{entry_id}",
                headers=headers,
            ) as resp:
                print("unload_status:", resp.status)

        return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("HA_SMOKE_URL", DEFAULT_URL))
    parser.add_argument(
        "--username",
        default=os.environ.get("HA_SMOKE_USER", "dev"),
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("HA_SMOKE_PASSWORD", "devdevdev"),
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Skip config entry reload",
    )
    parser.add_argument(
        "--no-unload",
        action="store_true",
        help="Skip config entry removal",
    )
    args = parser.parse_args(argv)
    args.reload = not args.no_reload
    args.unload = not args.no_unload
    return args


async def _resolve_token(
    session: aiohttp.ClientSession,
    ha_url: str,
    username: str,
    password: str,
) -> str:
    if TOKEN_FILE.is_file():
        cached = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if cached and await _token_valid(session, ha_url, cached):
            return cached

    _, text = await _get(session, ha_url, "/api/onboarding")
    steps = json.loads(text)
    need_user = not any(s["step"] == "user" and s["done"] for s in steps)

    if need_user:
        async with session.post(
            f"{ha_url}/api/onboarding/users",
            json={
                "name": "Dev",
                "username": username,
                "password": password,
                "client_id": f"{ha_url}/",
                "language": "en",
            },
        ) as resp:
            data = await resp.json()
        async with session.post(
            f"{ha_url}/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": data["auth_code"],
                "client_id": f"{ha_url}/",
            },
        ) as resp:
            token = (await resp.json())["access_token"]
    else:
        token = await _login_flow_token(session, ha_url, username, password)

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


async def _ensure_integration(
    session: aiohttp.ClientSession,
    ha_url: str,
    headers: dict[str, str],
) -> str | None:
    async with session.get(
        f"{ha_url}/api/config/config_entries/entry", headers=headers
    ) as resp:
        existing = [
            e for e in await resp.json() if e.get("domain") == "usccb_daily_readings"
        ]
    if existing:
        return existing[0]["entry_id"]

    async with session.post(
        f"{ha_url}/api/config/config_entries/flow",
        json={"handler": "usccb_daily_readings"},
        headers=headers,
    ) as resp:
        flow = await resp.json()
    if "flow_id" not in flow:
        print("config_flow_start_failed:", flow, file=sys.stderr)
        return None

    async with session.post(
        f"{ha_url}/api/config/config_entries/flow/{flow['flow_id']}",
        json={},
        headers=headers,
    ) as resp:
        result = await resp.json()
    if result.get("type") != "create_entry":
        print("config_flow_failed:", result, file=sys.stderr)
        return None
    return result["result"]["entry_id"]


async def _print_entity_smoke(
    session: aiohttp.ClientSession,
    ha_url: str,
    headers: dict[str, str],
) -> bool:
    async with session.get(f"{ha_url}/api/states", headers=headers) as resp:
        states = [
            st
            for st in await resp.json()
            if st["entity_id"].startswith("sensor.usccb_daily_readings")
        ]
    if len(states) != 6:
        print(f"expected 6 sensors, found {len(states)}", file=sys.stderr)
        return False
    states.sort(key=lambda s: s["entity_id"])
    leaked = False
    for state in states:
        attrs = state["attributes"]
        if "text" in attrs:
            leaked = True
        print(
            state["entity_id"],
            state["state"][:80],
            f"section_available={attrs.get('section_available')}",
        )
    if leaked:
        print("ERROR: text attribute must not be exposed", file=sys.stderr)
        return False
    return True


async def _print_diagnostics(
    session: aiohttp.ClientSession,
    ha_url: str,
    headers: dict[str, str],
    entry_id: str,
) -> bool:
    async with session.get(
        f"{ha_url}/api/diagnostics/config_entry/{entry_id}",
        headers=headers,
    ) as resp:
        body = await resp.text()
        if resp.status != 200:
            print("diagnostics_status:", resp.status, body[:200], file=sys.stderr)
            return False
    payload = json.loads(body)
    data = payload.get("data") or {}
    integration = (
        payload.get("custom_components", {})
        .get("usccb_daily_readings", {})
        .get("config_entries", {})
        .get(entry_id)
    )
    summary = integration or data
    print(
        "diagnostics:",
        {
            k: summary.get(k)
            for k in (
                "integration_version",
                "liturgical_date",
                "celebration",
                "section_types",
                "today_available",
                "last_update_success",
            )
            if k in summary
        },
    )
    if "Synthetic" in body:
        print(
            "ERROR: diagnostics must not include fixture reading text", file=sys.stderr
        )
        return False
    return True


async def _login_flow_token(
    session: aiohttp.ClientSession,
    ha_url: str,
    username: str,
    password: str,
) -> str:
    client_id = f"{ha_url}/"
    async with session.post(
        f"{ha_url}/auth/login_flow",
        json={
            "client_id": client_id,
            "handler": ["homeassistant", None],
            "redirect_uri": client_id,
        },
    ) as resp:
        flow_id = (await resp.json())["flow_id"]
    async with session.post(
        f"{ha_url}/auth/login_flow/{flow_id}",
        json={"username": username, "password": password, "client_id": client_id},
    ) as resp:
        result = await resp.json()
    if result.get("type") != "create_entry":
        raise RuntimeError(result)
    async with session.post(
        f"{ha_url}/auth/token",
        data={
            "grant_type": "authorization_code",
            "code": result["result"],
            "client_id": client_id,
        },
    ) as resp:
        data = await resp.json()
        if "access_token" not in data:
            raise RuntimeError(data)
        return data["access_token"]


async def _token_valid(session: aiohttp.ClientSession, ha_url: str, token: str) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{ha_url}/api/", headers=headers) as resp:
        return resp.status == 200


async def _get(
    session: aiohttp.ClientSession, ha_url: str, path: str
) -> tuple[int, str]:
    async with session.get(f"{ha_url}{path}") as resp:
        return resp.status, await resp.text()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
