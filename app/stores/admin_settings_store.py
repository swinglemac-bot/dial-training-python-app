from __future__ import annotations

from app.db import CONN
from app.utils import now_iso

SETTINGS_ID = "global"


def _ensure_settings() -> None:
    row = CONN.execute("SELECT id FROM app_settings WHERE id = ?", (SETTINGS_ID,)).fetchone()
    if row:
        return
    CONN.execute(
        """
        INSERT INTO app_settings (
          id, allow_registration, announcement_enabled, announcement_message,
          maintenance_mode, maintenance_message, updated_at
        ) VALUES (?, 1, 0, NULL, 0, NULL, ?)
        """,
        (SETTINGS_ID, now_iso()),
    )
    CONN.commit()


def get_admin_settings() -> dict:
    _ensure_settings()
    row = CONN.execute("SELECT * FROM app_settings WHERE id = ?", (SETTINGS_ID,)).fetchone()
    return {
        "allowRegistration": bool(row["allow_registration"]),
        "announcementEnabled": bool(row["announcement_enabled"]),
        "announcementMessage": row["announcement_message"] or "",
        "maintenanceMode": bool(row["maintenance_mode"]),
        "maintenanceMessage": row["maintenance_message"] or "",
        "updatedAt": row["updated_at"],
    }


def update_admin_settings(payload: dict) -> dict:
    _ensure_settings()
    existing = get_admin_settings()
    next_settings = {
        "allowRegistration": payload.get("allowRegistration", existing["allowRegistration"]),
        "announcementEnabled": payload.get("announcementEnabled", existing["announcementEnabled"]),
        "announcementMessage": payload.get("announcementMessage", existing["announcementMessage"]),
        "maintenanceMode": payload.get("maintenanceMode", existing["maintenanceMode"]),
        "maintenanceMessage": payload.get("maintenanceMessage", existing["maintenanceMessage"]),
    }

    CONN.execute(
        """
        UPDATE app_settings
        SET allow_registration = ?, announcement_enabled = ?, announcement_message = ?,
            maintenance_mode = ?, maintenance_message = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            int(bool(next_settings["allowRegistration"])),
            int(bool(next_settings["announcementEnabled"])),
            next_settings["announcementMessage"] or None,
            int(bool(next_settings["maintenanceMode"])),
            next_settings["maintenanceMessage"] or None,
            now_iso(),
            SETTINGS_ID,
        ),
    )
    CONN.commit()
    return get_admin_settings()
