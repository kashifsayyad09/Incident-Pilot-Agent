from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.decision_service import load_incident
from app.deps import get_backend
from app.schemas import IncidentList, IncidentSummary
from app.security import require_api_key
from app.tools.base import DiagnosticBackend, DiagnosticsError, DiagnosticsUnavailable

router = APIRouter(
    prefix="/api/v1/incidents", tags=["incidents"], dependencies=[Depends(require_api_key)]
)


@router.get("", response_model=IncidentList)
def list_incidents(backend: DiagnosticBackend = Depends(get_backend)) -> IncidentList:
    try:
        incidents, notice = backend.list_incidents()
    except DiagnosticsUnavailable as e:
        return IncidentList(mode=backend.mode, incidents=[], notice=f"Diagnostics unavailable: {e}")
    except DiagnosticsError as e:
        raise HTTPException(status_code=502, detail=f"Diagnostics failed: {e}") from e
    return IncidentList(mode=backend.mode, incidents=incidents, notice=notice)


@router.get("/{incident_id}", response_model=IncidentSummary)
def get_incident(
    incident_id: str, backend: DiagnosticBackend = Depends(get_backend)
) -> IncidentSummary:
    return load_incident(incident_id, backend)[0]
