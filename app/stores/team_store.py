from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import HTTPException

from app.db import CONN
from app.utils import now_iso, token_hex

TEAM_ROLES = {"athlete", "coach", "team_admin"}
ASSIGNMENT_STATUSES = {"assigned", "started", "completed"}


def _normalize_team_role(role: str) -> str:
    return role if role in TEAM_ROLES else "athlete"


def _normalize_status(status: str) -> str:
    return status if status in ASSIGNMENT_STATUSES else "assigned"


def _member_is_admin(global_role: str) -> bool:
    return global_role == "admin"


def _require_team_role(team_id: str, member_id: str, allowed_roles: set[str], global_role: str) -> sqlite3.Row | None:
    if _member_is_admin(global_role):
        return None
    row = CONN.execute(
        "SELECT * FROM team_memberships WHERE team_id = ? AND member_id = ?", (team_id, member_id)
    ).fetchone()
    if not row or _normalize_team_role(row["role"]) not in allowed_roles:
        raise HTTPException(status_code=403, detail="Team access is required.")
    return row


def _sanitize_team_row(row: Any, my_role: str | None = None) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "organization": row["organization"] or None,
        "createdBy": row["created_by"],
        "createdAt": row["created_at"],
        "myRole": my_role,
    }


def create_team(payload: dict) -> dict:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="Team name is required.")

    team_id = token_hex(16)
    created_at = now_iso()
    created_by = payload["createdBy"]
    admin_member_id = payload.get("adminMemberId") or created_by

    CONN.execute(
        "INSERT INTO teams (id, name, organization, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (team_id, name, str(payload.get("organization", "")).strip() or None, created_by, created_at),
    )

    CONN.execute(
        "INSERT INTO team_memberships (id, team_id, member_id, role, joined_at) VALUES (?, ?, ?, 'team_admin', ?)",
        (token_hex(16), team_id, admin_member_id, created_at),
    )

    coach_ids = list(dict.fromkeys([m for m in payload.get("coachMemberIds", []) if m]))
    for coach_id in coach_ids:
        if coach_id == admin_member_id:
            continue
        CONN.execute(
            "INSERT OR IGNORE INTO team_memberships (id, team_id, member_id, role, joined_at) VALUES (?, ?, ?, 'coach', ?)",
            (token_hex(16), team_id, coach_id, created_at),
        )
    CONN.commit()

    team_row = CONN.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    return _sanitize_team_row(team_row, "team_admin")


def list_teams_for_member(member_id: str, global_role: str) -> list[dict]:
    if _member_is_admin(global_role):
        rows = CONN.execute("SELECT * FROM teams ORDER BY created_at DESC").fetchall()
        return [_sanitize_team_row(row, "team_admin") for row in rows]

    rows = CONN.execute(
        """
        SELECT teams.*, team_memberships.role AS my_role
        FROM team_memberships
        JOIN teams ON teams.id = team_memberships.team_id
        WHERE team_memberships.member_id = ?
        ORDER BY teams.created_at DESC
        """,
        (member_id,),
    ).fetchall()
    return [_sanitize_team_row(row, _normalize_team_role(row["my_role"])) for row in rows]


def list_team_roster(team_id: str, actor_member_id: str, actor_global_role: str) -> list[dict]:
    _require_team_role(team_id, actor_member_id, {"team_admin", "coach", "athlete"}, actor_global_role)
    rows = CONN.execute(
        """
        SELECT
          tm.id AS membership_id,
          tm.role AS team_role,
          m.id AS member_id,
          m.name,
          m.email,
          m.role,
          m.program_type,
          m.team_name,
          m.last_login_at,
          m.created_at,
          m.subscription_plan,
          m.subscription_status,
          m.subscription_started_at,
          m.subscription_renews_at
        FROM team_memberships tm
        JOIN members m ON m.id = tm.member_id
        WHERE tm.team_id = ?
        ORDER BY m.name ASC
        """,
        (team_id,),
    ).fetchall()

    return [
        {
            "id": row["member_id"],
            "teamMembershipId": row["membership_id"],
            "teamRole": _normalize_team_role(row["team_role"]),
            "name": row["name"],
            "email": row["email"],
            "globalRole": row["role"],
            "programType": row["program_type"],
            "teamName": row["team_name"],
            "subscription": {
                "plan": row["subscription_plan"],
                "status": row["subscription_status"],
                "startedAt": row["subscription_started_at"],
                "renewsAt": row["subscription_renews_at"],
            },
            "lastLoginAt": row["last_login_at"],
            "createdAt": row["created_at"],
        }
        for row in rows
    ]


def add_team_member_by_email(payload: dict) -> dict:
    team_id = payload["teamId"]
    _require_team_role(team_id, payload["actorMemberId"], {"team_admin", "coach"}, payload["actorGlobalRole"])

    member = CONN.execute(
        "SELECT * FROM members WHERE lower(trim(email)) = ?", (str(payload.get("email", "")).strip().lower(),)
    ).fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found for this email.")

    role = _normalize_team_role(payload.get("role", "athlete"))
    joined_at = now_iso()
    CONN.execute(
        "INSERT OR REPLACE INTO team_memberships (id, team_id, member_id, role, joined_at) VALUES (?, ?, ?, ?, ?)",
        (token_hex(16), team_id, member["id"], role, joined_at),
    )
    CONN.commit()

    return {
        "id": member["id"],
        "teamRole": role,
        "name": member["name"],
        "email": member["email"],
        "joinedAt": joined_at,
    }


def update_team_membership_role(payload: dict) -> dict:
    team_id = payload["teamId"]
    _require_team_role(team_id, payload["actorMemberId"], {"team_admin"}, payload["actorGlobalRole"])

    role = _normalize_team_role(payload.get("role", "athlete"))
    CONN.execute(
        "UPDATE team_memberships SET role = ? WHERE team_id = ? AND member_id = ?",
        (role, team_id, payload["memberId"]),
    )
    CONN.commit()

    member = CONN.execute("SELECT id, name, email FROM members WHERE id = ?", (payload["memberId"],)).fetchone()
    return {
        "id": member["id"],
        "teamRole": role,
        "name": member["name"],
        "email": member["email"],
    }


def create_team_workout_template(payload: dict) -> dict:
    team_id = payload["teamId"]
    _require_team_role(team_id, payload["actorMemberId"], {"team_admin", "coach"}, payload["actorGlobalRole"])

    template_id = token_hex(16)
    created_at = now_iso()
    CONN.execute(
        """
        INSERT INTO team_workout_templates (id, team_id, title, tier, category, payload_json, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            template_id,
            team_id,
            payload.get("title") or "Untitled template",
            payload.get("tier") or "Foundation",
            payload.get("category") or "General",
            json.dumps(payload.get("exercises") or []),
            payload["actorMemberId"],
            created_at,
        ),
    )
    CONN.commit()

    return {
        "id": template_id,
        "teamId": team_id,
        "title": payload.get("title") or "Untitled template",
        "tier": payload.get("tier") or "Foundation",
        "category": payload.get("category") or "General",
        "exercises": payload.get("exercises") or [],
        "createdBy": payload["actorMemberId"],
        "createdAt": created_at,
    }


def list_team_workout_templates(team_id: str, actor_member_id: str, actor_global_role: str) -> list[dict]:
    _require_team_role(team_id, actor_member_id, {"team_admin", "coach", "athlete"}, actor_global_role)
    rows = CONN.execute(
        "SELECT * FROM team_workout_templates WHERE team_id = ? ORDER BY created_at DESC", (team_id,)
    ).fetchall()
    return [
        {
            "id": row["id"],
            "teamId": row["team_id"],
            "title": row["title"],
            "tier": row["tier"],
            "category": row["category"],
            "exercises": json.loads(row["payload_json"] or "[]"),
            "createdBy": row["created_by"],
            "createdAt": row["created_at"],
        }
        for row in rows
    ]


def assign_team_workout_template(payload: dict) -> list[dict]:
    team_id = payload["teamId"]
    _require_team_role(team_id, payload["actorMemberId"], {"team_admin", "coach"}, payload["actorGlobalRole"])

    template = CONN.execute(
        "SELECT * FROM team_workout_templates WHERE id = ? AND team_id = ?",
        (payload.get("templateId"), team_id),
    ).fetchone()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    assigned_at = now_iso()
    created: list[dict] = []
    for member_id in payload.get("memberIds", []) or []:
        assignment_id = token_hex(16)
        CONN.execute(
            """
            INSERT INTO team_workout_assignments (id, team_id, template_id, member_id, assigned_by, assigned_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'assigned')
            """,
            (assignment_id, team_id, template["id"], member_id, payload["actorMemberId"], assigned_at),
        )
        created.append(
            {
                "id": assignment_id,
                "teamId": team_id,
                "templateId": template["id"],
                "memberId": member_id,
                "assignedBy": payload["actorMemberId"],
                "assignedAt": assigned_at,
                "status": "assigned",
            }
        )

    CONN.commit()
    return created


def list_team_workout_assignments(team_id: str, actor_member_id: str, actor_global_role: str) -> list[dict]:
    membership = _require_team_role(team_id, actor_member_id, {"team_admin", "coach", "athlete"}, actor_global_role)

    if _member_is_admin(actor_global_role) or (membership and _normalize_team_role(membership["role"]) in {"team_admin", "coach"}):
        rows = CONN.execute(
            """
            SELECT a.*, t.title AS template_title, m.name AS member_name
            FROM team_workout_assignments a
            JOIN team_workout_templates t ON t.id = a.template_id
            JOIN members m ON m.id = a.member_id
            WHERE a.team_id = ?
            ORDER BY a.assigned_at DESC
            """,
            (team_id,),
        ).fetchall()
    else:
        rows = CONN.execute(
            """
            SELECT a.*, t.title AS template_title, m.name AS member_name
            FROM team_workout_assignments a
            JOIN team_workout_templates t ON t.id = a.template_id
            JOIN members m ON m.id = a.member_id
            WHERE a.team_id = ? AND a.member_id = ?
            ORDER BY a.assigned_at DESC
            """,
            (team_id, actor_member_id),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "teamId": row["team_id"],
            "templateId": row["template_id"],
            "templateTitle": row["template_title"],
            "memberId": row["member_id"],
            "memberName": row["member_name"],
            "assignedBy": row["assigned_by"],
            "assignedAt": row["assigned_at"],
            "status": _normalize_status(row["status"]),
        }
        for row in rows
    ]


def get_team_dashboard(team_id: str, actor_member_id: str, actor_global_role: str) -> dict:
    teams = list_teams_for_member(actor_member_id, actor_global_role)
    team = next((t for t in teams if t["id"] == team_id), None)
    if not team and not _member_is_admin(actor_global_role):
        raise HTTPException(status_code=403, detail="Team access is required.")

    roster = list_team_roster(team_id, actor_member_id, actor_global_role)
    templates = list_team_workout_templates(team_id, actor_member_id, actor_global_role)
    assignments = list_team_workout_assignments(team_id, actor_member_id, actor_global_role)
    return {
        "team": team,
        "summary": {
            "memberCount": len(roster),
            "templateCount": len(templates),
            "assignmentCount": len(assignments),
        },
        "recentAssignments": assignments[:20],
        "templates": templates[:10],
    }
