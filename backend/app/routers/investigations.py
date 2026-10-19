from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.analyzer import IncidentAnalyzer
from app.agent.report import IncidentReport
from app.agent.store import ReportStore
from app.agent.workflow import run_investigation
from app.config import Settings, get_settings
from app.deps import get_analyzer, get_decider_client, get_report_store
from app.security import require_api_key
from decision_patterns.tool_selection import DeciderClient

router = APIRouter(
    prefix="/api/v1", tags=["investigations"], dependencies=[Depends(require_api_key)]
)


class InvestigationRequest(BaseModel):
    incident_id: str
    require_decision: bool = True


@router.post("/investigations", response_model=IncidentReport)
def create_investigation(
    req: InvestigationRequest,
    settings: Settings = Depends(get_settings),
    decider: DeciderClient | None = Depends(get_decider_client),
    analyzer: IncidentAnalyzer | None = Depends(get_analyzer),
    store: ReportStore = Depends(get_report_store),
) -> IncidentReport:
    """Run the full pipeline and store the report.

    Decider 2B and Bedrock are both real calls. If either is unavailable the request fails
    (503/502); nothing is mocked. `require_decision=false` skips Decider and marks the
    report `analysis_only`.
    """
    return run_investigation(
        req.incident_id,
        settings=settings,
        decider=decider,
        analyzer=analyzer,
        store=store,
        require_decision=req.require_decision,
    )


@router.get("/reports", response_model=list[IncidentReport])
def list_reports(store: ReportStore = Depends(get_report_store)) -> list[IncidentReport]:
    return store.list()


@router.get("/reports/{report_id}", response_model=IncidentReport)
def get_report(report_id: str, store: ReportStore = Depends(get_report_store)) -> IncidentReport:
    report = store.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
