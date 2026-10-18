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
    """What the confidence gate decided to do with the model's selection."""

    TOOL_SELECTED = "tool_selected"  # confident; the tool is run in Phase 4
    EVIDENCE_REQUESTED = "evidence_requested"  # gather more evidence, then ask again
    HUMAN_REVIEW = "human_review"  # still unsure; a person decides


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
    """One real Decider 2B inference. `confidence` and `probabilities` are the model's own
    numbers, unmodified. `latency_ms` is the server-reported inference time (null if the
    server did not report it); `roundtrip_ms` is measured by this API."""

    incident_id: str
    mode: Mode
    input_state: dict[str, object]
    state_text: str = Field(description="The exact text the model read.")
    question: str
    options: list[ToolOption]
    selected: ToolOption
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float]
    model: str | None = None
    latency_ms: float | None = Field(default=None, ge=0.0)
    roundtrip_ms: float = Field(ge=0.0)
    confidence_threshold: float
    meets_threshold: bool
    outcome: DecisionOutcome
    reason: str
    tool_invoked: str | None = Field(
        default=None, description="Always null until diagnostic tools exist (Phase 4)."
    )


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
