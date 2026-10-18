"""IncidentPilot's instance of the reusable Tool Selection pattern."""

from __future__ import annotations

from app.config import Settings
from app.schemas import ToolOption
from decision_patterns.tool_selection import DeciderClient, ToolSelectionPattern

QUESTION = "Which diagnostic tool should the incident agent run next?"

# Descriptions are part of the prompt: they tell the model what evidence points to each option.
OPTION_DESCRIPTIONS: dict[str, str] = {
    ToolOption.INVESTIGATE_LOAD_BALANCER: (
        "Inspect the load balancer and its target group: elevated 5xx at the ALB, "
        "unhealthy or missing targets, failing health checks."
    ),
    ToolOption.INVESTIGATE_EC2: (
        "Inspect EC2 instances: sustained high CPU or memory pressure, saturated workers, "
        "slow responses while targets are healthy."
    ),
    ToolOption.INVESTIGATE_DATABASE: (
        "Inspect RDS: connections near the limit, connection errors, database CPU or "
        "storage pressure."
    ),
    ToolOption.INVESTIGATE_CLOUDWATCH_LOGS: (
        "Search application logs for the error cause: repeated exceptions, stack traces, "
        "errors that started right after a deployment."
    ),
    ToolOption.COLLECT_MORE_EVIDENCE: (
        "The evidence is conflicting, thin or ambiguous; gather more data before choosing "
        "a specific investigation."
    ),
}


def build_pattern(settings: Settings, client: DeciderClient) -> ToolSelectionPattern:
    return ToolSelectionPattern(
        question=QUESTION,
        options={str(k): v for k, v in OPTION_DESCRIPTIONS.items()},
        client=client,
        confidence_threshold=settings.decider_confidence_threshold,
        evidence_option=str(ToolOption.COLLECT_MORE_EVIDENCE),
        max_evidence_rounds=1,
        name="next_tool",
    )
