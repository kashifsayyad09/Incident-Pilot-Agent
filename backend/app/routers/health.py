from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agent.analyzer import bedrock_status
from app.config import Settings, get_settings
from app.decision_status import current_decision_status
from app.deps import get_decider_client
from app.schemas import ComponentStatus, HealthResponse
from app.tools.factory import diagnostics_status
from decision_patterns.tool_selection import DeciderClient

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    settings: Settings = Depends(get_settings),
    client: DeciderClient | None = Depends(get_decider_client),
) -> HealthResponse:
    decision = current_decision_status(settings, client)
    bedrock_ok, bedrock_detail = bedrock_status(settings)
    diag_ok, diag_detail = diagnostics_status(settings)
    return HealthResponse(
        mode=settings.mode,
        components=[
            ComponentStatus(name="api", available=True),
            ComponentStatus(
                name="decider_2b", available=decision.available, detail=decision.reason
            ),
            ComponentStatus(name="bedrock_agent", available=bedrock_ok, detail=bedrock_detail),
            ComponentStatus(name="aws_diagnostics", available=diag_ok, detail=diag_detail),
        ],
    )
