"""Incident -> Decider 2B decision -> evidence -> Bedrock analysis -> grounded report."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.config import Settings
from app.decision_service import decide_for, load_incident
from app.schemas import DecisionOutcome, DecisionResult
from app.tools.base import DiagnosticBackend, DiagnosticsError, DiagnosticsUnavailable, ToolRun
from decision_patterns.tool_selection import DeciderClient

from .analyzer import AnalysisError, AnalysisUnavailable, IncidentAnalyzer
from .evidence import bundle_from_state, extend_with_tool
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
    backend: DiagnosticBackend,
    require_decision: bool = True,
) -> IncidentReport:
    incident, state = load_incident(incident_id, backend)

    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bedrock analysis unavailable: INCIDENTPILOT_BEDROCK_MODEL_ID is not set.",
        )

    decision: DecisionResult | None = None
    if require_decision:
        decision = decide_for(incident.id, state, settings, decider, backend.mode)  # 503/502

    bundle = bundle_from_state(state, backend.mode)

    # Only a confident Decider selection runs a tool. Low confidence / "collect more
    # evidence" / human review run nothing: the report says so instead of guessing.
    tool_run: ToolRun | None = None
    if decision is not None and decision.outcome is DecisionOutcome.TOOL_SELECTED:
        try:
            tool_run = backend.run_tool(decision.selected, state)
        except DiagnosticsUnavailable as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Diagnostic tool unavailable: {e}",
                headers={"Retry-After": "10"} if e.retryable else None,
            ) from e
        except DiagnosticsError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Diagnostic tool failed: {e}"
            ) from e
        bundle = extend_with_tool(bundle, tool_run.findings, tool_run.tool.value)
        decision = decision.model_copy(update={"tool_invoked": tool_run.tool.value})

    try:
        out = analyzer.analyze(bundle, decision, tool_run)
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
        mode=backend.mode,
        status=_STATUS[decision.outcome] if decision else ReportStatus.ANALYSIS_ONLY,
        incident=incident,
        decision=decision,
        tool_run=tool_run,
        evidence=bundle,
        analysis=analysis,
        grounding=grounding,
        generation=Generation(model_id=out.model_id, region=out.region, latency_ms=out.latency_ms),
    )
    store.save(report)
    return report
