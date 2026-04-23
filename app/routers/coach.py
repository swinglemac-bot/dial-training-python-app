from __future__ import annotations

from fastapi import APIRouter

from app.config import config
from app.services.coach_service import build_coach_reply
from app.services.proactive_coach import build_proactive_coach_state
from app.stores.athlete_memory_store import (
    get_athlete_memory_record,
    summarize_athlete_memory_record,
    update_athlete_memory,
)

router = APIRouter()


@router.post("/api/coach/proactive")
def proactive(payload: dict | None = None) -> dict:
    payload = payload or {}
    athlete_id = str(payload.get("athleteId") or "local-athlete")
    memory_record = get_athlete_memory_record(athlete_id)
    persistent_summary = summarize_athlete_memory_record(memory_record)

    return build_proactive_coach_state(
        {
            "athleteMemory": payload.get("athleteMemory") if isinstance(payload.get("athleteMemory"), dict) else None,
            "foundationProfile": payload.get("foundationProfile") if isinstance(payload.get("foundationProfile"), dict) else None,
            "recentWorkouts": payload.get("recentWorkouts") if isinstance(payload.get("recentWorkouts"), list) else [],
            "persistentSummary": persistent_summary,
        }
    )


@router.post("/api/coach/respond")
def respond(payload: dict | None = None) -> dict:
    payload = payload or {}
    athlete_id = str(payload.get("athleteId") or "local-athlete")
    existing = get_athlete_memory_record(athlete_id)
    persistent = summarize_athlete_memory_record(existing)

    normalized_payload = {
        "mode": str(payload.get("mode") or "Foundation"),
        "prompt": str(payload.get("prompt") or ""),
        "contextSummary": str(payload.get("contextSummary") or ""),
        "conversationHistory": payload.get("conversationHistory") if isinstance(payload.get("conversationHistory"), list) else [],
        "athleteMemory": payload.get("athleteMemory") if isinstance(payload.get("athleteMemory"), dict) else None,
        "persistentMemorySummary": persistent,
        "foundationProfile": payload.get("foundationProfile") if isinstance(payload.get("foundationProfile"), dict) else None,
        "recentWorkouts": payload.get("recentWorkouts") if isinstance(payload.get("recentWorkouts"), list) else [],
    }

    reply = build_coach_reply(normalized_payload, config)
    update_athlete_memory(
        {
            "athleteId": athlete_id,
            "athleteMemory": normalized_payload.get("athleteMemory"),
            "mode": normalized_payload["mode"],
            "prompt": normalized_payload["prompt"],
            "reply": reply,
        }
    )
    return reply
