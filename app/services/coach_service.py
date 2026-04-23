from __future__ import annotations

import re
from typing import Any


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _normalize_intent_text(text: str) -> str:
    value = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    substitutions = {
        "loose": "lose",
        "wieght": "weight",
        "protien": "protein",
        "calroies": "calories",
        "reivew": "review",
        "sesh": "session",
        "ragner": "ranger",
    }
    for source, target in substitutions.items():
        value = value.replace(source, target)
    return re.sub(r"\s+", " ", value).strip()


def _recent_workout_summary(recent_workouts: list[dict]) -> str:
    if not recent_workouts:
        return "No saved workout history is available yet."
    lines: list[str] = []
    for i, workout in enumerate(recent_workouts[:5]):
        exercises = _safe_list(workout.get("exercises"))
        completed = len([x for x in exercises if x and x.get("completed")])
        lines.append(
            f"{i + 1}. {workout.get('title', 'Session')} ({workout.get('tier', 'N/A')}) on {workout.get('date', 'unknown')} with {len(exercises)} exercises and {completed} marked complete."
        )
    return "\n".join(lines)


def build_coach_reply(payload: dict, _config: Any = None) -> dict:
    mode = str(payload.get("mode") or "Foundation")
    prompt = str(payload.get("prompt") or "")
    lower = _normalize_intent_text(prompt)
    recent_workouts = _safe_list(payload.get("recentWorkouts"))

    recommendation = "Stay consistent with your plan and progress one variable at a time this week."
    if any(k in lower for k in ["lose weight", "calories", "body fat", "macro", "nutrition"]):
        recommendation = "Target a moderate calorie deficit, keep protein high, and maintain 3-4 strength sessions each week."
    elif any(k in lower for k in ["knee", "pain", "injury", "hurt"]):
        recommendation = "Reduce painful movements, train pain-free ranges, and prioritize technique plus recovery for 7-10 days."
    elif any(k in lower for k in ["recover", "underslept", "sore", "fatigued", "run down"]):
        recommendation = "Take a lower-intensity recovery day and return to hard sessions once sleep and soreness improve."
    elif any(k in lower for k in ["deadlift", "squat", "bench", "technique"]):
        recommendation = "Use submaximal sets, film one top set, and make one technical improvement each session."

    return {
        "mode": mode,
        "summary": recommendation,
        "nextActions": [
            "Log your next session with exact loads and RPE.",
            "Report sleep quality and soreness tomorrow.",
            "Reassess after 3 sessions and adjust volume by 10-15% if needed.",
        ],
        "context": {
            "prompt": prompt,
            "recentWorkoutSummary": _recent_workout_summary(recent_workouts),
            "persistentMemorySummary": payload.get("persistentMemorySummary") or "",
        },
    }
