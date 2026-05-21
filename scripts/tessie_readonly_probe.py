#!/usr/bin/env python3
"""Read-only Tessie telemetry probe for Aether.

This script is intentionally narrow:
- reads only Tessie state/drives/charges endpoints
- never prints API tokens
- strips location/GPS fields from generated reports
- can run against fixtures for tests or live via TESSIE_API_TOKEN/CYBERTRUCK_VIN
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TESSIE_BASE = "https://api.tessie.com"
ENDPOINTS = ("state", "drives", "charges")
LOCATION_KEYS = {
    "latitude",
    "longitude",
    "lat",
    "lon",
    "location",
    "location_name",
    "gps_as_of",
    "native_latitude",
    "native_longitude",
    "heading",
}
SECRETISH_KEYS = {"token", "authorization", "api_key", "apikey", "secret"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _round_float(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 2)
    return value


def redact_report(value: Any) -> Any:
    """Recursively remove location and secret-like fields from a report."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_l = str(key).lower()
            if key_l in LOCATION_KEYS or any(secret in key_l for secret in SECRETISH_KEYS):
                continue
            redacted[key] = redact_report(child)
        return redacted
    if isinstance(value, list):
        return [redact_report(item) for item in value]
    return _round_float(value)


def load_fixture_responses(fixture_dir: Path) -> dict[str, Any]:
    responses: dict[str, Any] = {}
    for endpoint in ENDPOINTS:
        path = fixture_dir / f"{endpoint}.json"
        with path.open("r", encoding="utf-8") as fh:
            responses[endpoint] = json.load(fh)
    return responses


def fetch_tessie(endpoint: str, *, token: str, vin: str, timeout: int = 20) -> Any:
    url = f"{TESSIE_BASE}/{vin}/{endpoint}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "kublai-tessie-readonly-probe/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS API URL
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Tessie {endpoint} returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Tessie {endpoint} request failed: {exc.reason}") from exc
    return json.loads(body)


def fetch_live_responses(*, token: str, vin: str) -> dict[str, Any]:
    return {endpoint: fetch_tessie(endpoint, token=token, vin=vin) for endpoint in ENDPOINTS}


def _count_results(payload: Any) -> int | None:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return len(payload["results"])
    if isinstance(payload, list):
        return len(payload)
    return None


def build_report(*, vin: str, responses: dict[str, Any]) -> dict[str, Any]:
    state_payload = responses.get("state") or {}
    charge_state = state_payload.get("charge_state", {}) if isinstance(state_payload, dict) else {}
    vehicle_state = state_payload.get("vehicle_state", {}) if isinstance(state_payload, dict) else {}
    drive_state = state_payload.get("drive_state", {}) if isinstance(state_payload, dict) else {}

    report = {
        "generated_at": _now_iso(),
        "source": "tessie",
        "read_only": True,
        "vehicle": {
            "vin_suffix": vin[-4:] if vin else None,
            "vin_present": bool(vin),
        },
        "state": {
            "online_state": state_payload.get("state") if isinstance(state_payload, dict) else None,
            "shift_state": drive_state.get("shift_state") if isinstance(drive_state, dict) else None,
            "odometer_miles": vehicle_state.get("odometer") if isinstance(vehicle_state, dict) else None,
            "battery_level_pct": charge_state.get("battery_level") if isinstance(charge_state, dict) else None,
            "charging_state": charge_state.get("charging_state") if isinstance(charge_state, dict) else None,
            "plugged_in": charge_state.get("plugged_in") if isinstance(charge_state, dict) else None,
        },
        "source_counts": {
            "drives": _count_results(responses.get("drives")),
            "charges": _count_results(responses.get("charges")),
        },
        "capabilities": {
            "vehicle_commands_supported": False,
            "location_exported": False,
            "raw_token_exported": False,
        },
        "health": {
            "state_endpoint_ok": "state" in responses,
            "drives_endpoint_ok": "drives" in responses,
            "charges_endpoint_ok": "charges" in responses,
        },
    }
    return redact_report(report)


def write_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a redacted read-only Tessie telemetry report.")
    parser.add_argument("--fixture-dir", type=Path, help="Directory containing state.json/drives.json/charges.json")
    parser.add_argument("--output", type=Path, default=Path("reports/tessie-readonly-report.json"))
    parser.add_argument("--vin", default=os.environ.get("CYBERTRUCK_VIN", ""))
    args = parser.parse_args(argv)

    if args.fixture_dir:
        responses = load_fixture_responses(args.fixture_dir)
    else:
        token = os.environ.get("TESSIE_API_TOKEN")
        if not token:
            print("TESSIE_API_TOKEN is required for live probe", file=sys.stderr)
            return 2
        if not args.vin:
            print("CYBERTRUCK_VIN is required for live probe", file=sys.stderr)
            return 2
        responses = fetch_live_responses(token=token, vin=args.vin)

    report = build_report(vin=args.vin, responses=responses)
    write_report(report, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
