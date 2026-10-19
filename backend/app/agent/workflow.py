"""Incident -> Decider 2B decision -> evidence -> Bedrock analysis -> grounded report."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.config import Mode, Settings
from app.decision_service import decide_for, load_incident
from app.schemas import DecisionOutcome, DecisionResult
from decision_patterns.tool_selection import DeciderClient

from .analyzer import AnalysisError, AnalysisUnavailable, IncidentAnalyzer
from .evidence import bundle_from_state
from .grounding import ground
from .report import Generation, IncidentReport, ReportStatus
from .store import ReportStore

_STATUS = {
    DecisionOutcome.TOOL_SELECTED: ReportStatus.COMPLETE,
    DecisionOutcome.EVIDENCE_REQUESTED: ReportStatus.NEEDS_MORE_EVIDENCE,
    DecisionOutcome.HUMAN_REVIEW: ReportStatus.NEEDS_HUMAN_REVIEW,
}


def run_investigation(
    incident_id: str,
    *,
    settings: Settings,
    decider: DeciderClient | None,
    analyzer: IncidentAnalyzer | None,
    store: ReportStore,
    require_decision: bool = True,
) -> IncidentReport:
    incident, state = load_incident(incident_id, settings)

    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bedrock analysis unavailable: INCIDENTPILOT_BEDROCK_MODEL_ID is not set.",
        )

    decision: DecisionResult | None = None
    if require_decision:
        decision = decide_for(incident.id, state, settings, decider)  # 503/502 propagate

    bundle = bundle_from_state(state, Mode.SIMULATION)
    try:
        out = analyzer.analyze(bundle, decision)
    except AnalysisUnavailable as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Bedrock analysis unavailable: {e}",
            headers={"Retry-After": "10"} if e.retryable else None,
        ) from e
    except AnalysisError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Bedrock analysis failed: {e}"
        ) from e

    analysis, grounding = ground(out.analysis, bundle)
    report = IncidentReport(
        id=f"rpt_{uuid.uuid4().hex}",
        created_at=datetime.now(UTC),
        mode=Mode.SIMULATION,
        status=_STATUS[decision.outcome] if decision else ReportStatus.ANALYSIS_ONLY,
        incident=incident,
        decision=decision,
        evidence=bundle,
        analysis=analysis,
        grounding=grounding,
        generation=Generation(model_id=out.model_id, region=out.region, latency_ms=out.latency_ms),
    )
    store.save(report)
    return report
