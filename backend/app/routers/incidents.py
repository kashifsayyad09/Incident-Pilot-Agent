from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import Mode, Settings, get_settings
from app.schemas import IncidentList, IncidentSummary
from app.security import require_api_key
from app.simulation import catalog

router = APIRouter(
    prefix="/api/v1/incidents", tags=["incidents"], dependencies=[Depends(require_api_key)]
)


@router.get("", response_model=IncidentList)
def list_incidents(settings: Settings = Depends(get_settings)) -> IncidentList:
    if settings.mode is Mode.LIVE:
        return IncidentList(
            mode=Mode.LIVE,
            incidents=[],
            notice="Live AWS incident discovery is implemented in Phase 4.",
        )
    return IncidentList(mode=Mode.SIMULATION, incidents=catalog.list_scenarios())


@router.get("/{incident_id}", response_model=IncidentSummary)
def get_incident(incident_id: str, settings: Settings = Depends(get_settings)) -> IncidentSummary:
    if settings.mode is Mode.LIVE:
        raise HTTPException(status_code=501, detail="Live incidents arrive in Phase 4.")
    scenario = catalog.get_scenario(incident_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return scenario
