from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.decision_service import run_decision as _run
from app.decision_status import current_decision_status
from app.deps import get_decider_client
from app.schemas import DecisionRequest, DecisionResult, DecisionStatus
from app.security import require_api_key
from decision_patterns.tool_selection import DeciderClient

router = APIRouter(
    prefix="/api/v1/decision", tags=["decision"], dependencies=[Depends(require_api_key)]
)


@router.get("/status", response_model=DecisionStatus)
def decision_status(
    settings: Settings = Depends(get_settings),
    client: DeciderClient | None = Depends(get_decider_client),
) -> DecisionStatus:
    return current_decision_status(settings, client)


@router.post("/run", response_model=DecisionResult)
def run_decision(
    req: DecisionRequest,
    settings: Settings = Depends(get_settings),
    client: DeciderClient | None = Depends(get_decider_client),
) -> DecisionResult:
    """Run real Decider 2B tool selection. There is no fallback: 503 if the model server is
    unavailable, 502 if it answers invalidly."""
    return _run(req.incident_id, settings, client)
