from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.config import config

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def root() -> str:
    coach_mode = "mock" if config.coach_mock_mode or not config.openai_api_key else "openai"
    return f"""
    <html>
      <head><title>Dialed Backend (Python)</title></head>
      <body style='font-family:Arial;padding:30px;background:#070A10;color:#F3F4F6;'>
        <h1>Dialed Python Backend is live</h1>
        <p>Coach mode: <strong>{coach_mode}</strong></p>
        <p>Wearables mode: <strong>{'mock' if config.garmin_mock_mode else 'real'}</strong></p>
        <p><a href='/health' style='color:#AFFF2F'>Open health JSON</a></p>
      </body>
    </html>
    """


@router.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "mode": "mock" if config.garmin_mock_mode else "real",
        "coachMode": "mock" if config.coach_mock_mode or not config.openai_api_key else "openai",
        "service": "dialed-device-sync-server-python",
    }
