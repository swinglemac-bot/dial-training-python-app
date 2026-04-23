from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.services.garmin_service import begin_garmin_auth
from app.stores.wearable_store import (
    clear_connection,
    get_latest_metrics,
    list_connections,
    set_latest_metrics,
    upsert_connection,
)
from app.utils import now_iso

router = APIRouter()


@router.get("/auth/garmin/start", response_class=HTMLResponse)
def auth_garmin_start(request: Request) -> str:
    redirect_uri = str(request.query_params.get("redirect_uri", ""))
    result = begin_garmin_auth(redirect_uri)
    return f"""
    <html><body style='font-family:Arial;padding:32px;background:#070A10;color:#F3F4F6;'>
      <h1>Garmin linked in mock mode (Python)</h1>
      <p>Return to Dialed and refresh device status.</p>
      <p><a href='{result['returnUrl']}' style='color:#95E11F;'>Return to Dialed</a></p>
    </body></html>
    """


@router.get("/auth/garmin/callback")
def auth_garmin_callback() -> dict:
    raise HTTPException(
        status_code=501,
        detail="Callback is scaffolded, but real Garmin token exchange is pending approval.",
    )


@router.get("/api/wearables/connections")
def get_connections() -> dict:
    return {"connections": list_connections()}


@router.get("/api/wearables/garmin/latest")
def get_garmin_latest() -> dict:
    latest = get_latest_metrics("Garmin")
    if not latest:
        raise HTTPException(status_code=404, detail="No Garmin metrics have been synced yet.")
    return latest


@router.post("/api/wearables/garmin/mock-sync")
def post_garmin_mock_sync(payload: dict | None = None) -> dict:
    payload = payload or {}
    metrics = {
        "source": "Garmin",
        "durationMinutes": str(payload.get("durationMinutes", "58")),
        "caloriesBurned": str(payload.get("caloriesBurned", "487")),
        "averageHeartRate": str(payload.get("averageHeartRate", "141")),
        "maxHeartRate": str(payload.get("maxHeartRate", "173")),
        "sleepHours": str(payload.get("sleepHours", "7.6")),
        "recoveryScore": str(payload.get("recoveryScore", "81")),
    }

    upsert_connection(
        {
            "provider": "Garmin",
            "status": "connected",
            "accountLabel": "mock-garmin-user",
            "lastSyncAt": now_iso(),
        }
    )
    return set_latest_metrics("Garmin", metrics)


@router.delete("/api/wearables/garmin")
def delete_garmin() -> dict:
    return {"connection": clear_connection("Garmin")}
