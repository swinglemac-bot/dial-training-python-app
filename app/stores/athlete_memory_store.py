from __future__ import annotations

import json

from app.db import CONN
from app.utils import now_iso


def get_athlete_memory_record(athlete_id: str) -> dict:
    row = CONN.execute("SELECT * FROM athlete_memory WHERE athlete_id = ?", (athlete_id,)).fetchone()
    if not row:
        return {"athleteId": athlete_id, "summary": "", "updatedAt": None}
    return {
        "athleteId": row["athlete_id"],
        "summary": row["summary"],
        "updatedAt": row["updated_at"],
    }


def summarize_athlete_memory_record(record: dict | None) -> str:
    if not record or not record.get("summary"):
        return "No persistent athlete memory summary is available yet."
    return record["summary"]


def update_athlete_memory(payload: dict) -> None:
    athlete_id = str(payload.get("athleteId") or "local-athlete")
    prompt = str(payload.get("prompt") or "").strip()
    reply = payload.get("reply") or {}
    mode = str(payload.get("mode") or "Foundation")

    line = f"[{mode}] User: {prompt}\nCoach: {json.dumps(reply, ensure_ascii=True)}"

    existing = get_athlete_memory_record(athlete_id)
    summary = (existing.get("summary") or "").strip()
    summary = (summary + "\n\n" + line).strip() if summary else line
    if len(summary) > 8000:
        summary = summary[-8000:]

    CONN.execute(
        """
        INSERT INTO athlete_memory (athlete_id, summary, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(athlete_id)
        DO UPDATE SET summary = excluded.summary, updated_at = excluded.updated_at
        """,
        (athlete_id, summary, now_iso()),
    )
    CONN.commit()
