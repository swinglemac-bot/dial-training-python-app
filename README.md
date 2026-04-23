# Dialed Training Python Copy

This is a **separate Python implementation** of the existing Dialed Training project.

- The original TypeScript/Node/React Native project is untouched.
- This folder provides Python equivalents for the backend routes and a Python UI scaffold.

## What is included

- `app/main.py`: FastAPI server entrypoint
- `app/routers/*`: Python API routes mirroring the original paths (`/api/auth/*`, `/api/team/*`, `/api/coach/*`, wearables, health)
- `app/stores/*`: SQLite-backed auth/team/admin stores + in-memory wearable store
- `app/services/*`: coach + proactive coach logic and Garmin auth scaffold
- `ui.py`: Streamlit-based Python UI shell replacing the original app shell in Python
- `assets/`, `docs/`: copied from the original project for continuity

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env template:

```bash
cp .env.example .env
```

4. Run API server:

```bash
python run.py
```

5. Run Python UI (separate terminal):

```bash
streamlit run ui.py
```

## Notes

- The backend route names are preserved so existing client integrations can be retargeted.
- Email delivery is currently `manual` (reset/verification links are returned in API responses when enabled).
- Garmin is scaffolded in mock mode, consistent with the existing project behavior.

## Streamlit Cloud settings

Use these in Streamlit Cloud `Secrets` if you want backend integration and login protection:

```toml
BACKEND_URL = "https://your-backend-domain"
APP_USERNAME = "admin"
APP_PASSWORD = "change-me"
```

- `BACKEND_URL` enables live coach replies via `/api/coach/respond`.
- If `APP_USERNAME` and `APP_PASSWORD` are both set, the app requires sign-in.
