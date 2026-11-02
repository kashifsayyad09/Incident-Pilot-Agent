"""Diagnostic tool contract shared by the simulation and live AWS backends."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field

from app.config import Mode
from app.schemas import IncidentSummary, ToolOption
from app.state import IncidentState

# Decider option -> diagnostic tool. `collect_more_evidence` runs nothing by design.
RUNNABLE_TOOLS: tuple[ToolOption, ...] = (
    ToolOption.INVESTIGATE_LOAD_BALANCER,
    ToolOption.INVESTIGATE_EC2,
    ToolOption.INVESTIGATE_DATABASE,
    ToolOption.INVESTIGATE_CLOUDWATCH_LOGS,
)


class DiagnosticsUnavailable(Exception):
    """The backend cannot be used (not configured, no credentials, access denied, network)."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class DiagnosticsError(Exception):
    """The backend answered but the result is unusable."""


class ToolRun(BaseModel):
    """What a diagnostic tool actually did and returned. Recorded in the report."""

    tool: ToolOption
    mode: Mode
    backend: str = Field(description="'simulation' or 'aws-readonly'")
    findings: list[str] = Field(description="Plain-text findings; each becomes an evidence item.")
    api_calls: list[str] = Field(
        default_factory=list,
        description="Read-only AWS operations performed, e.g. 'elbv2:DescribeTargetHealth'. "
        "Empty in simulation.",
    )
    duration_ms: float = Field(ge=0.0)
    executed_at: datetime


class DiagnosticBackend(Protocol):
    mode: Mode

    def list_incidents(self) -> tuple[list[IncidentSummary], str | None]:
        """(incidents, notice)."""

    def get_incident(self, incident_id: str) -> tuple[IncidentSummary, IncidentState] | None:
        """None if unknown. May raise DiagnosticsUnavailable / DiagnosticsError."""

    def run_tool(self, tool: ToolOption, state: IncidentState) -> ToolRun:
        """Run one read-only diagnostic."""
