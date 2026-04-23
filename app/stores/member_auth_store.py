from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.config import config
from app.db import CONN
from app.security import create_password_hash, verify_password
from app.utils import add_days, add_hours, add_minutes, now_iso, token_hex

DEFAULT_PLAN = "Performance"
SESSION_TTL_DAYS = 30
RESET_TTL_MINUTES = 30
VERIFICATION_TTL_HOURS = 24


def _normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def _member_role(email: str) -> str:
    return "admin" if _normalize_email(email) == _normalize_email(config.admin_email) else "member"


def _sanitize_member(row: Any) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "programType": row["program_type"],
        "teamName": row["team_name"] or None,
        "age": row["age"],
        "heightInches": row["height_inches"],
        "weightLbs": row["weight_lbs"],
        "activityLevel": row["activity_level"] or None,
        "emailVerified": bool(row["email_verified_at"]),
        "emailVerifiedAt": row["email_verified_at"],
        "createdAt": row["created_at"],
        "lastLoginAt": row["last_login_at"],
        "subscription": {
            "plan": row["subscription_plan"],
            "status": row["subscription_status"],
            "startedAt": row["subscription_started_at"],
            "renewsAt": row["subscription_renews_at"],
        },
    }


def _is_expired(iso_value: str) -> bool:
    return datetime.fromisoformat(iso_value) <= datetime.now(timezone.utc)


def _clean_expired() -> None:
    now = now_iso()
    CONN.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
    CONN.execute("DELETE FROM reset_tokens WHERE expires_at <= ?", (now,))
    CONN.execute("DELETE FROM verification_tokens WHERE expires_at <= ?", (now,))
    CONN.commit()


def register_member(payload: dict) -> dict:
    name = str(payload.get("name", "")).strip()
    email = _normalize_email(payload.get("email", ""))
    password = str(payload.get("password", "")).strip()

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required.")

    existing = CONN.execute("SELECT id FROM members WHERE email = ?", (email,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    now = now_iso()
    member_id = token_hex(16)
    CONN.execute(
        """
        INSERT INTO members (
          id, name, email, role, program_type, team_name, age, height_inches, weight_lbs, activity_level,
          email_verified_at, password_hash, created_at, last_login_at,
          subscription_plan, subscription_status, subscription_started_at, subscription_renews_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            member_id,
            name,
            email,
            _member_role(email),
            "team" if payload.get("programType") == "team" else "individual",
            payload.get("teamName") if payload.get("programType") == "team" else None,
            payload.get("age"),
            payload.get("heightInches"),
            payload.get("weightLbs"),
            payload.get("activityLevel"),
            None,
            create_password_hash(password),
            now,
            now,
            payload.get("plan") or DEFAULT_PLAN,
            "trial",
            now,
            None,
        ),
    )

    verification_token = token_hex(24)
    CONN.execute("DELETE FROM verification_tokens WHERE member_id = ?", (member_id,))
    CONN.execute(
        "INSERT INTO verification_tokens (token, member_id, issued_at, expires_at) VALUES (?, ?, ?, ?)",
        (verification_token, member_id, now, add_hours(now, VERIFICATION_TTL_HOURS)),
    )
    CONN.commit()

    member = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    return {
        "member": _sanitize_member(member),
        "verificationToken": {
            "token": verification_token,
            "expiresAt": add_hours(now, VERIFICATION_TTL_HOURS),
        },
    }


def login_member(payload: dict) -> dict:
    email = _normalize_email(payload.get("email", ""))
    password = str(payload.get("password", ""))
    row = CONN.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not row["email_verified_at"]:
        raise HTTPException(status_code=403, detail="Verify your email before signing in.")

    issued_at = now_iso()
    token = token_hex(32)
    expires_at = add_days(issued_at, SESSION_TTL_DAYS)
    CONN.execute(
        "INSERT INTO sessions (token, member_id, issued_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, row["id"], issued_at, expires_at),
    )
    CONN.execute("UPDATE members SET last_login_at = ? WHERE id = ?", (issued_at, row["id"]))
    CONN.commit()

    member = CONN.execute("SELECT * FROM members WHERE id = ?", (row["id"],)).fetchone()
    return {
        "member": _sanitize_member(member),
        "session": {"token": token, "memberId": row["id"], "issuedAt": issued_at, "expiresAt": expires_at},
    }


def get_member_from_session(token: str) -> dict | None:
    _clean_expired()
    session = CONN.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    if not session:
        return None
    if _is_expired(session["expires_at"]):
        CONN.execute("DELETE FROM sessions WHERE token = ?", (token,))
        CONN.commit()
        return None
    member = CONN.execute("SELECT * FROM members WHERE id = ?", (session["member_id"],)).fetchone()
    if not member:
        return None
    return {
        "member": _sanitize_member(member),
        "session": {
            "token": session["token"],
            "memberId": session["member_id"],
            "issuedAt": session["issued_at"],
            "expiresAt": session["expires_at"],
        },
    }


def logout_member(token: str) -> None:
    CONN.execute("DELETE FROM sessions WHERE token = ?", (token,))
    CONN.commit()


def clear_member_sessions(member_id: str) -> None:
    CONN.execute("DELETE FROM sessions WHERE member_id = ?", (member_id,))
    CONN.commit()


def _request_verification_for_member(member_id: str) -> dict:
    member = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        return {"member": None, "alreadyVerified": False, "verificationToken": None}
    if member["email_verified_at"]:
        return {"member": _sanitize_member(member), "alreadyVerified": True, "verificationToken": None}

    issued_at = now_iso()
    token = token_hex(24)
    expires_at = add_hours(issued_at, VERIFICATION_TTL_HOURS)
    CONN.execute("DELETE FROM verification_tokens WHERE member_id = ?", (member_id,))
    CONN.execute(
        "INSERT INTO verification_tokens (token, member_id, issued_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, member_id, issued_at, expires_at),
    )
    CONN.commit()
    return {
        "member": _sanitize_member(member),
        "alreadyVerified": False,
        "verificationToken": {"token": token, "expiresAt": expires_at},
    }


def request_email_verification(email: str) -> dict:
    row = CONN.execute("SELECT id FROM members WHERE email = ?", (_normalize_email(email),)).fetchone()
    if not row:
        return {"member": None, "alreadyVerified": False, "verificationToken": None}
    return _request_verification_for_member(row["id"])


def request_email_verification_for_member_id(member_id: str) -> dict:
    return _request_verification_for_member(member_id)


def verify_member_email_with_token(token: str) -> dict:
    row = CONN.execute("SELECT * FROM verification_tokens WHERE token = ?", (token,)).fetchone()
    if not row or _is_expired(row["expires_at"]):
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired.")

    now = now_iso()
    CONN.execute("UPDATE members SET email_verified_at = ? WHERE id = ?", (now, row["member_id"]))
    CONN.execute("DELETE FROM verification_tokens WHERE member_id = ?", (row["member_id"],))
    CONN.commit()

    member = CONN.execute("SELECT * FROM members WHERE id = ?", (row["member_id"],)).fetchone()
    return _sanitize_member(member)


def _request_reset_for_member(member_id: str) -> dict:
    member = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        return {"member": None, "resetToken": None}

    issued_at = now_iso()
    token = token_hex(24)
    expires_at = add_minutes(issued_at, RESET_TTL_MINUTES)
    CONN.execute("DELETE FROM reset_tokens WHERE member_id = ?", (member_id,))
    CONN.execute(
        "INSERT INTO reset_tokens (token, member_id, issued_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, member_id, issued_at, expires_at),
    )
    CONN.commit()

    return {
        "member": _sanitize_member(member),
        "resetToken": {"token": token, "expiresAt": expires_at},
    }


def request_password_reset(email: str) -> dict:
    row = CONN.execute("SELECT id FROM members WHERE email = ?", (_normalize_email(email),)).fetchone()
    if not row:
        return {"member": None, "resetToken": None}
    return _request_reset_for_member(row["id"])


def request_password_reset_for_member_id(member_id: str) -> dict:
    return _request_reset_for_member(member_id)


def reset_password_with_token(token: str, next_password: str) -> dict:
    reset = CONN.execute("SELECT * FROM reset_tokens WHERE token = ?", (str(token or "").strip(),)).fetchone()
    if not reset or _is_expired(reset["expires_at"]):
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired.")

    if len(str(next_password or "").strip()) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    CONN.execute(
        "UPDATE members SET password_hash = ? WHERE id = ?",
        (create_password_hash(next_password.strip()), reset["member_id"]),
    )
    CONN.execute("DELETE FROM reset_tokens WHERE member_id = ?", (reset["member_id"],))
    CONN.execute("DELETE FROM sessions WHERE member_id = ?", (reset["member_id"],))
    CONN.commit()
    row = CONN.execute("SELECT * FROM members WHERE id = ?", (reset["member_id"],)).fetchone()
    return _sanitize_member(row)


def list_members_for_admin() -> list[dict]:
    rows = CONN.execute("SELECT * FROM members ORDER BY created_at DESC").fetchall()
    return [_sanitize_member(row) for row in rows]


def update_member_subscription(member_id: str, payload: dict) -> dict:
    row = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    plan = payload.get("plan") or row["subscription_plan"]
    status = payload.get("status") or row["subscription_status"]
    CONN.execute(
        "UPDATE members SET subscription_plan = ?, subscription_status = ? WHERE id = ?",
        (plan, status, member_id),
    )
    CONN.commit()
    return _sanitize_member(CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone())


def update_member_profile(member_id: str, payload: dict) -> dict:
    row = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    program_type = "team" if payload.get("programType") == "team" else (payload.get("programType") or row["program_type"])
    team_name = payload.get("teamName") if program_type == "team" else None

    CONN.execute(
        """
        UPDATE members
        SET program_type = ?, team_name = ?, age = ?, height_inches = ?, weight_lbs = ?, activity_level = ?
        WHERE id = ?
        """,
        (
            program_type,
            team_name,
            payload.get("age", row["age"]),
            payload.get("heightInches", row["height_inches"]),
            payload.get("weightLbs", row["weight_lbs"]),
            payload.get("activityLevel", row["activity_level"]),
            member_id,
        ),
    )
    CONN.commit()
    return _sanitize_member(CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone())


def update_member_password(member_id: str, current_password: str, next_password: str, active_token: str) -> dict:
    row = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    if not verify_password(str(current_password or ""), row["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if len(str(next_password or "").strip()) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    CONN.execute(
        "UPDATE members SET password_hash = ? WHERE id = ?",
        (create_password_hash(next_password.strip()), member_id),
    )
    CONN.execute("DELETE FROM sessions WHERE member_id = ? AND token <> ?", (member_id, active_token))
    CONN.commit()
    return _sanitize_member(CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone())


def grant_admin_by_email(email: str) -> dict:
    row = CONN.execute("SELECT * FROM members WHERE email = ?", (_normalize_email(email),)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")
    CONN.execute("UPDATE members SET role = 'admin' WHERE id = ?", (row["id"],))
    CONN.commit()
    return _sanitize_member(CONN.execute("SELECT * FROM members WHERE id = ?", (row["id"],)).fetchone())


def update_member_by_admin(member_id: str, payload: dict) -> dict:
    row = CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    role = payload.get("role") if payload.get("role") in {"member", "admin"} else row["role"]
    program_type = "team" if payload.get("programType") == "team" else (payload.get("programType") or row["program_type"])
    team_name = payload.get("teamName") if program_type == "team" else None

    CONN.execute(
        """
        UPDATE members
        SET role = ?, subscription_plan = ?, subscription_status = ?, program_type = ?, team_name = ?
        WHERE id = ?
        """,
        (
            role,
            payload.get("plan", row["subscription_plan"]),
            payload.get("status", row["subscription_status"]),
            program_type,
            team_name,
            member_id,
        ),
    )
    CONN.commit()
    return _sanitize_member(CONN.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone())
