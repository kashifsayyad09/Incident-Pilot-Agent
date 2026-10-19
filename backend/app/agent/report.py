"""Report schemas.

`IncidentAnalysis` is what the Bedrock model is asked to produce (structured output).
`IncidentReport` is the stored, API-facing record: analysis plus the evidence it was
based on, the Decider decision, the grounding result, and provenance.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.config import Mode
from app.schemas import DecisionResult, IncidentSummary

from .evidence import EvidenceBundle

ADVISORY_NOTICE = (
    "AI-generated, advisory only. IncidentPilot is read-only and never changes AWS "
    "resources. A person must review and carry out any change."
)


class Fact(BaseModel):
    statement: str = Field(
        description="A fact stated directly by the cited evidence. Do not compute or infer."
    )
    evidence_ids: list[str] = Field(description="Ids of the evidence items stating it, e.g. E2.")


class Hypothesis(BaseModel):
    statement: str = Field(
        description="A possible explanation that the evidence suggests but does not prove."
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence consistent with it."
    )
    what_would_confirm: str = Field(
        description="The specific check or data that would confirm or refute it."
    )
    plausibility: Literal["leading", "possible", "unlikely"]


class RootCause(BaseModel):
    description: str
    basis: Literal["confirmed", "hypothesis"] = Field(
        description="'confirmed' only if the cited evidence directly establishes it."
    )
    evidence_ids: list[str] = Field(default_factory=list)


class Action(BaseModel):
    description: str = Field(description="What a human operator should do.")
    kind: Literal["read_only_check", "human_executed_change"] = Field(
        description=(
            "read_only_check inspects only; human_executed_change alters something "
            "and needs a person."
        )
    )
    risk: Literal["low", "medium", "high"]
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class IncidentAnalysis(BaseModel):
    summary: str = Field(description="Two or three sentences for an on-call engineer.")
    confirmed_facts: list[Fact]
    hypotheses: list[Hypothesis]
    probable_root_causes: list[RootCause]
    recommended_actions: list[Action] = Field(description="Ordered; read-only checks first.")
    impact_assessment: str = Field(
        description="Only impact the evidence supports, otherwise exactly: "
        "'Not determinable from the available evidence.'"
    )
    evidence_gaps: list[str] = Field(
        description="Data that is missing or not measured and would help."
    )


class GroundingReport(BaseModel):
    facts_kept: int = 0
    facts_demoted: int = 0
    root_causes_demoted: int = 0
    evidence_ids_removed: int = 0
    warnings: list[str] = Field(default_factory=list)


class Generation(BaseModel):
    ai_generated: bool = True
    provider: str = "Amazon Bedrock via Strands Agents SDK"
    model_id: str
    region: str
    latency_ms: float = Field(ge=0.0)


class ReportStatus(StrEnum):
    COMPLETE = "complete"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"  # Decider asked for more evidence
    NEEDS_HUMAN_REVIEW = "needs_human_review"  # Decider unsure after allowed rounds
    ANALYSIS_ONLY = "analysis_only"  # run without a Decider decision


class IncidentReport(BaseModel):
    id: str
    created_at: datetime
    mode: Mode
    status: ReportStatus
    incident: IncidentSummary
    decision: DecisionResult | None
    evidence: EvidenceBundle
    analysis: IncidentAnalysis
    grounding: GroundingReport
    generation: Generation
    advisory_notice: str = ADVISORY_NOTICE
