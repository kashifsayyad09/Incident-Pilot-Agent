from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.decision_status import current_decision_status
from app.schemas import ComponentStatus, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    decision = current_decision_status(settings)
    return HealthResponse(
        mode=settings.mode,
        components=[
            ComponentStatus(name="api", available=True),
            ComponentStatus(
                name="decider_2b", available=decision.available, detail=decision.reason
            ),
            ComponentStatus(
                name="bedrock_agent",
                available=False,
                detail="Not implemented yet (Phase 3).",
            ),
            ComponentStatus(
                name="aws_diagnostics",
                available=False,
                detail="Not implemented yet (Phase 4).",
            ),
        ],
    )
