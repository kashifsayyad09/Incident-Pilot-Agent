from __future__ import annotations

from app.config import Mode, Settings
from app.schemas import IncidentSummary, ToolOption
from app.state import IncidentState

from .base import DiagnosticBackend, DiagnosticsUnavailable, ToolRun
from .simulation import SimulationBackend

LIVE_NOT_CONFIGURED = (
    "Live mode needs at least one target: INCIDENTPILOT_LIVE_TARGET_GROUP_ARN, "
    "INCIDENTPILOT_LIVE_DB_INSTANCE_ID or INCIDENTPILOT_LIVE_LOG_GROUP."
)


class UnavailableBackend:
    """Stands in for a backend that cannot be used. It never returns data."""

    mode = Mode.LIVE

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def list_incidents(self) -> tuple[list[IncidentSummary], str | None]:
        return [], self.reason

    def get_incident(self, incident_id: str) -> tuple[IncidentSummary, IncidentState] | None:
        raise DiagnosticsUnavailable(self.reason)

    def run_tool(self, tool: ToolOption, state: IncidentState) -> ToolRun:
        raise DiagnosticsUnavailable(self.reason)


def build_backend(settings: Settings) -> DiagnosticBackend:
    if settings.mode is Mode.SIMULATION:
        return SimulationBackend()
    if not settings.live_configured:
        return UnavailableBackend(LIVE_NOT_CONFIGURED)
    from .aws import AwsBackend

    return AwsBackend(settings)


def diagnostics_status(settings: Settings) -> tuple[bool, str]:
    """(available, detail). Live availability means configured + credentials found; it is not a
    probe, and access is only proven by a real call."""
    if settings.mode is Mode.SIMULATION:
        return True, "Simulation backend: bundled sample data, no AWS calls."
    if not settings.live_configured:
        return False, LIVE_NOT_CONFIGURED
    try:
        import boto3

        creds = boto3.Session().get_credentials()
    except Exception as e:  # noqa: BLE001
        return False, f"Could not initialise AWS session ({type(e).__name__})."
    if creds is None:
        return False, "No AWS credentials found (IAM role, SSO profile or environment)."
    return True, "Live read-only AWS diagnostics configured; credentials found. Not probed."
