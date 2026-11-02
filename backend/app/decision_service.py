"""Run one real Decider 2B tool selection for a simulation incident."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.config import Mode, Settings
from app.decision_status import NOT_CONFIGURED
from app.incident_pattern import build_pattern
from app.schemas import DecisionOutcome, DecisionResult, ToolOption
from app.state import IncidentState, render_state_text
from app.tools.base import DiagnosticBackend, DiagnosticsError, DiagnosticsUnavailable
from decision_patterns.tool_selection import (
    Action,
    DeciderClient,
    DeciderProtocolError,
    DeciderUnavailable,
)

_OUTCOME = {
    Action.INVOKE_TOOL: DecisionOutcome.TOOL_SELECTED,
    Action.COLLECT_MORE_EVIDENCE: DecisionOutcome.EVIDENCE_REQUESTED,
    Action.HUMAN_REVIEW: DecisionOutcome.HUMAN_REVIEW,
}


def load_incident(incident_id: str, backend: DiagnosticBackend):
    """Return (summary, state). 404 unknown, 503 backend unavailable, 502 backend error."""
    try:
        found = backend.get_incident(incident_id)
    except DiagnosticsUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Diagnostics unavailable: {e}",
            headers={"Retry-After": "10"} if e.retryable else None,
        ) from e
    except DiagnosticsError as e:
        raise HTTPException(status_code=502, detail=f"Diagnostics failed: {e}") from e
    if found is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return found


def run_decision(
    incident_id: str,
    settings: Settings,
    client: DeciderClient | None,
    backend: DiagnosticBackend,
) -> DecisionResult:
    """No fallback: unavailable -> 503, invalid server answer -> 502."""
    incident, evidence = load_incident(incident_id, backend)
    return decide_for(incident.id, evidence, settings, client, backend.mode)


def decide_for(
    incident_id: str,
    evidence: IncidentState,
    settings: Settings,
    client: DeciderClient | None,
    mode: Mode = Mode.SIMULATION,
) -> DecisionResult:
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
        incident_id=incident_id,
        mode=mode,
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
