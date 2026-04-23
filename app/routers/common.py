from __future__ import annotations

from fastapi import Header, HTTPException

from app.stores.member_auth_store import get_member_from_session


def get_auth_token(authorization: str | None) -> str:
    value = str(authorization or "")
    if not value:
        return ""
    parts = value.split(" ", 1)
    if len(parts) != 2:
        return ""
    scheme, token = parts
    if scheme.lower() not in {"bearer", "dialedsession"}:
        return ""
    return token.strip()


def require_member(authorization: str | None = Header(default=None)) -> dict:
    token = get_auth_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    session = get_member_from_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    return {"token": token, **session}


def require_admin(auth: dict) -> dict:
    if auth["member"]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    return auth
