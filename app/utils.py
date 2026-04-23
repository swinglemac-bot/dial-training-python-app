from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_days(iso_value: str, days: int) -> str:
    return (datetime.fromisoformat(iso_value) + timedelta(days=days)).isoformat()


def add_hours(iso_value: str, hours: int) -> str:
    return (datetime.fromisoformat(iso_value) + timedelta(hours=hours)).isoformat()


def add_minutes(iso_value: str, minutes: int) -> str:
    return (datetime.fromisoformat(iso_value) + timedelta(minutes=minutes)).isoformat()


def token_hex(nbytes: int) -> str:
    return secrets.token_hex(nbytes)
