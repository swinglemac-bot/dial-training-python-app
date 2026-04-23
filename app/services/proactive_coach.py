from __future__ import annotations

from typing import Any


def build_proactive_coach_state(payload: dict[str, Any]) -> dict[str, Any]:
    recent = payload.get("recentWorkouts") or []
    memory = str(payload.get("persistentSummary") or "")
    readiness = "train"

    if any(str(w.get("title", "")).lower().find("recovery") >= 0 for w in recent[:3]):
        readiness = "balanced"

    return {
        "readiness": readiness,
        "highlights": [
            "Maintain movement quality before increasing intensity.",
            "Avoid repeating the exact same top movement pattern every session.",
        ],
        "persistentSummary": memory,
    }
