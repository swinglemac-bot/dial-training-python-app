from __future__ import annotations

from app.config import config


def begin_garmin_auth(redirect_uri: str) -> dict[str, str]:
    if redirect_uri:
        return {"returnUrl": redirect_uri}
    fallback = f"{config.app_scheme}://devices"
    return {"returnUrl": fallback}
