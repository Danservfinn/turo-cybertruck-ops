#!/usr/bin/env python3
"""Confirmation-gated Tessie vehicle command executor for Aether.

This script can run in dry-run mode locally/CI without touching the vehicle.
Actual execution is intended to happen only inside GitHub Actions where the
TESSIE_API_TOKEN secret already exists, and only when the caller supplies the
explicit confirmation phrase.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

TESSIE_BASE = "https://api.tessie.com"
CONFIRM_PHRASE = "SEND TO AETHER"

# User asked to enable the full practical command surface. Keep it explicit and
# auditable instead of allowing arbitrary endpoint strings.
COMMANDS: dict[str, dict[str, Any]] = {
    # Navigation / share
    "navigate": {"endpoint": "share", "risk": "navigation", "query_from": "destination"},
    "share": {"endpoint": "share", "risk": "navigation", "query_from": "value"},
    # Access / closures
    "lock": {"endpoint": "lock", "risk": "medium"},
    "unlock": {"endpoint": "unlock", "risk": "high"},
    "front-trunk": {"endpoint": "activate_front_trunk", "risk": "high"},
    "rear-trunk": {"endpoint": "activate_rear_trunk", "risk": "high"},
    "open-tonneau": {"endpoint": "open_tonneau", "risk": "high"},
    "close-tonneau": {"endpoint": "close_tonneau", "risk": "medium"},
    "vent-windows": {"endpoint": "vent_windows", "risk": "high"},
    "close-windows": {"endpoint": "close_windows", "risk": "medium"},
    # Signals / media
    "flash": {"endpoint": "flash", "risk": "low"},
    "honk": {"endpoint": "honk", "risk": "medium"},
    "boombox": {"endpoint": "remote_boombox", "risk": "medium"},
    # Climate
    "start-climate": {"endpoint": "start_climate", "risk": "medium"},
    "stop-climate": {"endpoint": "stop_climate", "risk": "low"},
    "set-temperature": {"endpoint": "set_temperature", "risk": "medium", "body_fields": ("driver_temp", "passenger_temp")},
    "set-seat-heating": {"endpoint": "set_seat_heating", "risk": "medium", "body_fields": ("seat", "level")},
    "set-seat-cooling": {"endpoint": "set_seat_cooling", "risk": "medium", "body_fields": ("seat", "level")},
    "start-defrost": {"endpoint": "start_max_defrost", "risk": "medium"},
    "stop-defrost": {"endpoint": "stop_max_defrost", "risk": "low"},
    "start-steering-wheel-heater": {"endpoint": "start_steering_wheel_heater", "risk": "medium"},
    "stop-steering-wheel-heater": {"endpoint": "stop_steering_wheel_heater", "risk": "low"},
    "set-climate-keeper-mode": {"endpoint": "set_climate_keeper_mode", "risk": "medium", "body_fields": ("mode",)},
    # Charging
    "start-charging": {"endpoint": "start_charging", "risk": "medium"},
    "stop-charging": {"endpoint": "stop_charging", "risk": "medium"},
    "set-charge-limit": {"endpoint": "set_charge_limit", "risk": "medium", "body_fields": ("percent",)},
    "set-charging-amps": {"endpoint": "set_charging_amps", "risk": "medium", "body_fields": ("amps",)},
    "open-charge-port": {"endpoint": "open_charge_port", "risk": "medium"},
    "close-charge-port": {"endpoint": "close_charge_port", "risk": "medium"},
    # Security / drive-affecting
    "remote-start-drive": {"endpoint": "remote_start_drive", "risk": "critical", "body_fields": ("password",)},
    "enable-sentry-mode": {"endpoint": "enable_sentry_mode", "risk": "low"},
    "disable-sentry-mode": {"endpoint": "disable_sentry_mode", "risk": "medium"},
    "enable-valet-mode": {"endpoint": "enable_valet_mode", "risk": "medium", "body_fields": ("pin",)},
    "disable-valet-mode": {"endpoint": "disable_valet_mode", "risk": "medium", "body_fields": ("pin",)},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) <= 8:
        return "[REDACTED]"
    return f"{value[:4]}…{value[-4:]}"


def command_names() -> list[str]:
    return sorted(COMMANDS)


def parse_json_object(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SystemExit("--payload-json must be a JSON object")
    return value


def validate_confirmation(*, command: str, confirm: str | None) -> bool:
    if confirm != CONFIRM_PHRASE:
        raise SystemExit(
            f"Refusing to execute vehicle command '{command}'. "
            f"Re-run with --confirm {CONFIRM_PHRASE!r}."
        )
    return True


def build_command_request(
    *,
    command: str,
    destination: str | None = None,
    value: str | None = None,
    locale: str = "en-US",
    password: str | None = None,
    pin: str | None = None,
    percent: int | None = None,
    amps: int | None = None,
    driver_temp: float | None = None,
    passenger_temp: float | None = None,
    seat: int | None = None,
    level: int | None = None,
    mode: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if command not in COMMANDS:
        raise SystemExit(f"Unsupported command: {command}. Supported: {', '.join(command_names())}")
    spec = COMMANDS[command]
    payload = dict(payload or {})
    field_values = {
        "password": password,
        "pin": pin,
        "percent": percent,
        "amps": amps,
        "driver_temp": driver_temp,
        "passenger_temp": passenger_temp,
        "seat": seat,
        "level": level,
        "mode": mode,
    }
    body = {k: v for k, v in field_values.items() if v is not None}
    body.update(payload)
    query: dict[str, Any] = {"wait_for_completion": "true", "max_attempts": "3"}
    if spec.get("query_from"):
        query_value = destination if spec["query_from"] == "destination" else value
        if not query_value:
            raise SystemExit(f"Command {command} requires --destination/--value")
        query["value"] = query_value
        query["locale"] = locale
    return {
        "command": command,
        "endpoint": spec["endpoint"],
        "risk": spec["risk"],
        "query": query,
        "body": body,
        "requested_at": _now_iso(),
    }


def redact_receipt(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            key_l = str(key).lower()
            if any(secret in key_l for secret in ("token", "authorization", "password", "pin", "secret")):
                result[key] = "[REDACTED]"
            elif key_l == "vin":
                result["vin_suffix"] = str(child)[-4:]
            else:
                result[key] = redact_receipt(child)
        return result
    if isinstance(value, list):
        return [redact_receipt(item) for item in value]
    return value


def execute_command(*, token: str, vin: str, request: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    endpoint = request["endpoint"]
    query = urllib.parse.urlencode(request.get("query") or {})
    url = f"{TESSIE_BASE}/{urllib.parse.quote(vin, safe='')}/command/{endpoint}"
    if query:
        url += "?" + query
    receipt: dict[str, Any] = {
        "ok": True,
        "dry_run": dry_run,
        "command": request["command"],
        "endpoint": endpoint,
        "risk": request["risk"],
        "vin": vin,
        "sent_at": None,
        "response": None,
    }
    if dry_run:
        receipt["ok"] = True
        receipt["note"] = "dry run only; no vehicle command sent"
        return redact_receipt(receipt)

    body = json.dumps(request.get("body") or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "kublai-tessie-command/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:  # noqa: S310 - fixed HTTPS API URL
            payload = json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        receipt.update({"ok": False, "sent_at": _now_iso(), "response": {"http_status": exc.code, "detail": detail}})
        return redact_receipt(receipt)
    receipt.update({"sent_at": _now_iso(), "response": payload})
    return redact_receipt(receipt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Confirmation-gated Tessie command executor for Aether")
    parser.add_argument("command", nargs="?", choices=command_names())
    parser.add_argument("--list", action="store_true", help="list supported commands")
    parser.add_argument("--destination", help="address/destination for navigate")
    parser.add_argument("--value", help="raw share value for share command")
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--payload-json", help="advanced JSON payload object")
    parser.add_argument("--password", help="Tesla account password for remote-start-drive, if required")
    parser.add_argument("--pin", help="PIN for valet/speed-limit-style commands, if required")
    parser.add_argument("--percent", type=int)
    parser.add_argument("--amps", type=int)
    parser.add_argument("--driver-temp", type=float)
    parser.add_argument("--passenger-temp", type=float)
    parser.add_argument("--seat", type=int)
    parser.add_argument("--level", type=int)
    parser.add_argument("--mode")
    parser.add_argument("--dry-run", action="store_true", help="build receipt without sending the command")
    parser.add_argument("--confirm", help=f"required for execution: {CONFIRM_PHRASE}")
    parser.add_argument("--vin", default=os.environ.get("CYBERTRUCK_VIN", ""))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        print(json.dumps({"commands": command_names(), "confirm_phrase": CONFIRM_PHRASE}, indent=2))
        return 0
    if not args.command:
        raise SystemExit("command is required unless --list is used")
    token = os.environ.get("TESSIE_API_TOKEN", "")
    if not args.dry_run:
        validate_confirmation(command=args.command, confirm=args.confirm)
        if not token:
            raise SystemExit("TESSIE_API_TOKEN is required for execution")
        if not args.vin:
            raise SystemExit("CYBERTRUCK_VIN is required for execution")
    request = build_command_request(
        command=args.command,
        destination=args.destination,
        value=args.value,
        locale=args.locale,
        password=args.password,
        pin=args.pin,
        percent=args.percent,
        amps=args.amps,
        driver_temp=args.driver_temp,
        passenger_temp=args.passenger_temp,
        seat=args.seat,
        level=args.level,
        mode=args.mode,
        payload=parse_json_object(args.payload_json),
    )
    receipt = execute_command(token=token, vin=args.vin or "UNKNOWN", request=request, dry_run=args.dry_run)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
