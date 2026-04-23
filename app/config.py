from __future__ import annotations

import os
from dataclasses import dataclass
try:
    from dotenv import load_dotenv
except ImportError:  # Optional for environments without installed deps.
    def load_dotenv() -> bool:
        return False

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    return str(os.getenv(name, str(default).lower())).strip().lower() == "true"


@dataclass(frozen=True)
class Config:
    port: int = int(os.getenv("PORT", "4000"))
    app_url: str = os.getenv("APP_URL", "http://localhost:8501")
    app_scheme: str = os.getenv("APP_SCHEME", "dialed")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5")
    coach_mock_mode: bool = _env_bool("COACH_MOCK_MODE", True)
    auth_expose_reset_tokens: bool = _env_bool("AUTH_EXPOSE_RESET_TOKENS", True)
    admin_email: str = os.getenv("ADMIN_EMAIL", "frederick.swingle@westpoint.edu")
    auth_reset_web_url: str = os.getenv(
        "AUTH_RESET_WEB_URL", "http://localhost:4000/auth/password/reset"
    )
    auth_verification_web_url: str = os.getenv(
        "AUTH_VERIFICATION_WEB_URL", "http://localhost:4000/auth/verify-email"
    )
    garmin_mock_mode: bool = _env_bool("GARMIN_MOCK_MODE", True)
    auth_database_path: str = os.getenv("AUTH_DATABASE_PATH", "./app/data/dialed.sqlite")


config = Config()
