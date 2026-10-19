"""Evidence bundle: the numbered facts the analysis model is allowed to rely on.

Each item has a stable id (E1, E2, ...). The model must cite these ids, and the grounding
step checks that its confirmed facts are actually supported by the items it cites.
Phase 4's real AWS tools will produce the same bundle shape from live API responses.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.config import Mode
from app.state import IncidentState, fmt

Source = Literal["alb", "ec2", "rds", "cloudwatch_alarm", "change", "log"]


class EvidenceItem(BaseModel):
    id: str
    source: Source
    text: str


class EvidenceBundle(BaseModel):
    incident_id: str
    mode: Mode
    items: list[EvidenceItem]

    def ids(self) -> set[str]:
        return {i.id for i in self.items}

    def by_id(self) -> dict[str, EvidenceItem]:
        return {i.id: i for i in self.items}


def bundle_from_state(state: IncidentState, mode: Mode) -> EvidenceBundle:
    texts: list[tuple[Source, str]] = []
    w = state.window_minutes
    if state.alb is not None:
        a = state.alb
        texts.append(
            (
                "alb",
                f"Load balancer (last {w} min): 5xx count over 5 min {fmt(a.http_5xx_count_5m)}; "
                f"5xx rate {fmt(a.http_5xx_rate_pct, '%')}; "
                f"p95 latency {fmt(a.p95_latency_s, 's')}; "
                f"healthy targets {fmt(a.healthy_targets)} of {fmt(a.total_targets)}.",
            )
        )
    if state.ec2 is not None:
        e = state.ec2
        texts.append(
            (
                "ec2",
                f"EC2 ({fmt(e.instances)} instances, last {w} min): CPU average "
                f"{fmt(e.cpu_avg_pct, '%')}; CPU maximum {fmt(e.cpu_max_pct, '%')}; "
                f"memory {fmt(e.memory_pct, '%')}.",
            )
        )
    if state.rds is not None:
        r = state.rds
        texts.append(
            (
                "rds",
                f"RDS (last {w} min): connections {fmt(r.connections)} of maximum "
                f"{fmt(r.max_connections)}; CPU {fmt(r.cpu_pct, '%')}.",
            )
        )
    for al in state.alarms:
        since = f" for {al.since_minutes} minutes" if al.since_minutes else ""
        texts.append(("cloudwatch_alarm", f"CloudWatch alarm {al.name} is {al.state}{since}."))
    for c in state.recent_changes:
        texts.append(("change", f"Recent change: {c}."))
    for line in state.log_excerpts:
        texts.append(("log", f"Log line: {line}"))

    return EvidenceBundle(
        incident_id=state.incident_id,
        mode=mode,
        items=[EvidenceItem(id=f"E{n}", source=s, text=t) for n, (s, t) in enumerate(texts, 1)],
    )
