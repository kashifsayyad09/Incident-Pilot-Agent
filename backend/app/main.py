from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import decision, health, incidents, investigations
from app.schemas import API_VERSION


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IncidentPilot AI API",
        version=API_VERSION,
        description="Read-only AWS incident investigation with Strands Decider 2B tool selection.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    app.include_router(health.router)
    app.include_router(incidents.router)
    app.include_router(decision.router)
    app.include_router(investigations.router)
    return app


app = create_app()
