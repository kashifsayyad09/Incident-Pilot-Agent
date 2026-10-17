"""API contract models (Pydantic v2). Mirrored in frontend/src/lib/types.ts.

The Decider-related models define the contract now so the frontend can be built
against it; real inference arrives in Phase 2. Fields that come from a model
(confidence, latency) are Optional on purpose: absence means "not produced",
never "zero".
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.config import Mode

API_VERSION = "0.1.0"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ServiceKind(StrEnum):
    ALB = "alb"
    EC2 = "ec2"
    RDS = "rds"
    CLOUDWATCH = "cloudwatch"


class ToolOption(StrEnum):
    """The typed option set Decider 2B chooses from."""

    INVESTIGATE_LOAD_BALANCER = "investigate_load_balancer"
    INVESTIGATE_EC2 = "investigate_ec2"
    INVESTIGATE_DATABASE = "investigate_database"
    INVESTIGATE_CLOUDWATCH_LOGS = "investigate_cloudwatch_logs"
    COLLECT_MORE_EVIDENCE = "collect_more_evidence"


class DecisionOutcome(StrEnum):
    """What the agent did with the model's prediction."""

    TOOL_INVOKED = "tool_invoked"
    ESCALATED_LOW_CONFIDENCE = "escalated_low_confidence"
    UNAVAILABLE = "unavailable"


# ---- Health ---------------------------------------------------------------


class ComponentStatus(BaseModel):
    name: str
    available: bool
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = API_VERSION
    mode: Mode
    components: list[ComponentStatus]


# ---- Incidents ------------------------------------------------------------


class IncidentSummary(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    severity: Severity
    affected_services: list[ServiceKind]
    mode: Mode


class IncidentList(BaseModel):
    mode: Mode
    incidents: list[IncidentSummary]
    notice: str | None = None


# ---- Decision (Decider 2B) ------------------------------------------------


class DecisionStatus(BaseModel):
    available: bool
    adapter: str | None = None
    reason: str | None = Field(
        default=None, description="Why the model is unavailable, when available is false."
    )
    confidence_threshold: float
    options: list[ToolOption]


class DecisionRequest(BaseModel):
    incident_id: str


class DecisionResult(BaseModel):
    incident_id: str
    mode: Mode
    input_state: dict[str, object]
    question: str
    options: list[ToolOption]
    selected: ToolOption | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    latency_ms: float | None = Field(default=None, ge=0.0)
    confidence_threshold: float
    outcome: DecisionOutcome
    tool_invoked: str | None = None
    note: str | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
