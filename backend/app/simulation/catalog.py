"""Simulation scenario catalogue (metadata only).

Evidence payloads (metrics, logs, alarms) are added in Phase 4. Nothing here
is a measurement; these are descriptions of the five required sample scenarios.
"""

from __future__ import annotations

from app.config import Mode
from app.schemas import IncidentSummary, ServiceKind, Severity

_S = Mode.SIMULATION

SCENARIOS: list[IncidentSummary] = [
    IncidentSummary(
        id="sim-alb-503",
        title="ALB returning HTTP 503",
        summary="Load balancer reports 503s to clients; target health is in question.",
        category="load-balancer",
        severity=Severity.CRITICAL,
        affected_services=[ServiceKind.ALB, ServiceKind.CLOUDWATCH],
        mode=_S,
    ),
    IncidentSummary(
        id="sim-ec2-cpu",
        title="EC2 CPU saturation",
        summary="An application instance is pinned at high CPU and requests are slowing.",
        category="compute",
        severity=Severity.WARNING,
        affected_services=[ServiceKind.EC2, ServiceKind.CLOUDWATCH],
        mode=_S,
    ),
    IncidentSummary(
        id="sim-rds-connections",
        title="RDS nearing connection exhaustion",
        summary="Database connection count is approaching the instance limit.",
        category="database",
        severity=Severity.CRITICAL,
        affected_services=[ServiceKind.RDS, ServiceKind.CLOUDWATCH],
        mode=_S,
    ),
    IncidentSummary(
        id="sim-bad-deploy",
        title="Deployment causes elevated 5xx",
        summary="Error rate rose right after an application deployment.",
        category="deployment",
        severity=Severity.CRITICAL,
        affected_services=[ServiceKind.ALB, ServiceKind.EC2, ServiceKind.CLOUDWATCH],
        mode=_S,
    ),
    IncidentSummary(
        id="sim-conflicting-signals",
        title="Conflicting monitoring signals",
        summary="Alarms and metrics disagree; more evidence is needed before choosing a tool.",
        category="ambiguous",
        severity=Severity.WARNING,
        affected_services=[ServiceKind.ALB, ServiceKind.EC2, ServiceKind.RDS],
        mode=_S,
    ),
]


def list_scenarios() -> list[IncidentSummary]:
    return list(SCENARIOS)


def get_scenario(incident_id: str) -> IncidentSummary | None:
    return next((s for s in SCENARIOS if s.id == incident_id), None)
