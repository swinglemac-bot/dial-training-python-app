from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import init_db
from app.routers.auth import router as auth_router
from app.routers.coach import router as coach_router
from app.routers.health import router as health_router
from app.routers.wearables import router as wearables_router

app = FastAPI(title="Dialed Python Copy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(wearables_router)
app.include_router(coach_router)
app.include_router(auth_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", None) or str(exc) or "Unexpected server error."
    return JSONResponse(status_code=status_code, content={"message": detail})
