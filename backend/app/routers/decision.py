from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.decision_status import current_decision_status
from app.schemas import DecisionRequest, DecisionResult, DecisionStatus
from app.security import require_api_key

router = APIRouter(
    prefix="/api/v1/decision", tags=["decision"], dependencies=[Depends(require_api_key)]
)


@router.get("/status", response_model=DecisionStatus)
def decision_status(settings: Settings = Depends(get_settings)) -> DecisionStatus:
    return current_decision_status(settings)


@router.post("/run", response_model=DecisionResult)
def run_decision(
    req: DecisionRequest, settings: Settings = Depends(get_settings)
) -> DecisionResult:
    """Run Decider 2B tool selection for an incident.

    Returns 503 while the model adapter is unavailable. There is deliberately no
    fallback path: a non-model answer must never be presented as a Decider decision.
    """
    st = current_decision_status(settings)
    if not st.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Decider 2B unavailable: {st.reason}",
        )
    raise HTTPException(
        status_code=501, detail="Inference path not implemented."
    )  # pragma: no cover
