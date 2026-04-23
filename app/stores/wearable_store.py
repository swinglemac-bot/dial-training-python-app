from __future__ import annotations

from typing import Any

from app.utils import now_iso

connections: list[dict[str, Any]] = [
    {"provider": "Garmin", "status": "setup_required"},
    {"provider": "Apple Health", "status": "setup_required"},
    {"provider": "Whoop", "status": "setup_required"},
    {"provider": "Fitbit", "status": "setup_required"},
]

latest_metrics_by_provider: dict[str, dict[str, Any]] = {}


def list_connections() -> list[dict[str, Any]]:
    return connections


def upsert_connection(next_connection: dict[str, Any]) -> dict[str, Any]:
    for i, connection in enumerate(connections):
        if connection.get("provider") == next_connection.get("provider"):
            updated = {**connection, **next_connection}
            connections[i] = updated
            return updated
    connections.append(next_connection)
    return next_connection


def clear_connection(provider: str) -> dict[str, Any]:
    fallback = {
        "provider": provider,
        "status": "not_connected",
        "lastSyncAt": None,
        "accountLabel": None,
        "errorMessage": None,
    }
    upsert_connection(fallback)
    latest_metrics_by_provider.pop(provider, None)
    return fallback


def set_latest_metrics(provider: str, metrics: dict[str, Any]) -> dict[str, Any]:
    latest_metrics_by_provider[provider] = {
        "provider": provider,
        "syncedAt": now_iso(),
        "metrics": metrics,
    }
    return latest_metrics_by_provider[provider]


def get_latest_metrics(provider: str) -> dict[str, Any] | None:
    return latest_metrics_by_provider.get(provider)
