from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Mode, Settings, get_settings
from app.decision_status import NOT_CONFIGURED, current_decision_status
from app.deps import get_decider_client
from app.incident_pattern import build_pattern
from app.schemas import (
    DecisionOutcome,
    DecisionRequest,
    DecisionResult,
    DecisionStatus,
    ToolOption,
)
from app.security import require_api_key
from app.simulation import catalog
from app.simulation.evidence import get_evidence
from app.state import render_state_text
from decision_patterns.tool_selection import (
    Action,
    DeciderClient,
    DeciderProtocolError,
    DeciderUnavailable,
)

router = APIRouter(
    prefix="/api/v1/decision", tags=["decision"], dependencies=[Depends(require_api_key)]
)

_OUTCOME = {
    Action.INVOKE_TOOL: DecisionOutcome.TOOL_SELECTED,
    Action.COLLECT_MORE_EVIDENCE: DecisionOutcome.EVIDENCE_REQUESTED,
    Action.HUMAN_REVIEW: DecisionOutcome.HUMAN_REVIEW,
}


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
    """Run real Decider 2B tool selection for an incident.

    There is deliberately no fallback: if the model server is unavailable this returns
    503, and if it answers badly this returns 502. A non-model answer is never returned.
    """
    if settings.mode is Mode.LIVE:
        raise HTTPException(status_code=501, detail="Live incident evidence arrives in Phase 4.")
    incident = catalog.get_scenario(req.incident_id)
    evidence = get_evidence(req.incident_id)
    if incident is None or evidence is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Decider 2B unavailable: {NOT_CONFIGURED}",
        )

    state_text = render_state_text(evidence)
    pattern = build_pattern(settings, client)
    try:
        d = pattern.decide(state_text)
    except DeciderUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Decider 2B unavailable: {e}"
        ) from e
    except DeciderProtocolError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    return DecisionResult(
        incident_id=incident.id,
        mode=Mode.SIMULATION,
        input_state=evidence.model_dump(mode="json"),
        state_text=state_text,
        question=pattern.question,
        options=[ToolOption(o) for o in pattern.options],
        selected=ToolOption(d.selected),
        confidence=d.confidence,
        probabilities=d.probabilities,
        model=d.model,
        latency_ms=d.latency_ms,
        roundtrip_ms=d.roundtrip_ms,
        confidence_threshold=d.threshold,
        meets_threshold=d.meets_threshold,
        outcome=_OUTCOME[d.action],
        reason=d.reason,
    )
