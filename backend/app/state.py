"""Structured incident state: the input handed to Decider 2B.

Every field is optional on purpose. `None` means "not measured / not available" and is
rendered as such to the model; it is never rendered as 0 or as healthy.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AlbState(BaseModel):
    http_5xx_count_5m: int | None = None
    http_5xx_rate_pct: float | None = None
    p95_latency_s: float | None = None
    healthy_targets: int | None = None
    total_targets: int | None = None


class Ec2State(BaseModel):
    instances: int | None = None
    cpu_avg_pct: float | None = None
    cpu_max_pct: float | None = None
    memory_pct: float | None = None  # needs the CloudWatch agent; None if not instrumented


class RdsState(BaseModel):
    connections: int | None = None
    max_connections: int | None = None
    cpu_pct: float | None = None


class AlarmInfo(BaseModel):
    name: str
    state: str  # ALARM | OK | INSUFFICIENT_DATA
    since_minutes: int | None = None


class IncidentState(BaseModel):
    incident_id: str
    window_minutes: int = 30
    alb: AlbState | None = None
    ec2: Ec2State | None = None
    rds: RdsState | None = None
    alarms: list[AlarmInfo] = Field(default_factory=list)
    recent_changes: list[str] = Field(default_factory=list)
    log_excerpts: list[str] = Field(default_factory=list)


def _v(x: object, unit: str = "") -> str:
    return "not measured" if x is None else f"{x}{unit}"


def render_state_text(s: IncidentState) -> str:
    """Deterministic plain-text rendering. This exact string is what the model reads."""
    lines = [f"Incident evidence (last {s.window_minutes} minutes)."]
    if s.alb is None:
        lines.append("Load balancer: no data.")
    else:
        a = s.alb
        lines.append(
            "Load balancer: "
            f"5xx count (5m) {_v(a.http_5xx_count_5m)}, 5xx rate {_v(a.http_5xx_rate_pct, '%')}, "
            f"p95 latency {_v(a.p95_latency_s, 's')}, "
            f"healthy targets {_v(a.healthy_targets)} of {_v(a.total_targets)}."
        )
    if s.ec2 is None:
        lines.append("EC2: no data.")
    else:
        e = s.ec2
        lines.append(
            f"EC2 ({_v(e.instances)} instances): CPU avg {_v(e.cpu_avg_pct, '%')}, "
            f"CPU max {_v(e.cpu_max_pct, '%')}, memory {_v(e.memory_pct, '%')}."
        )
    if s.rds is None:
        lines.append("RDS: no data.")
    else:
        r = s.rds
        lines.append(
            f"RDS: connections {_v(r.connections)} of max {_v(r.max_connections)}, "
            f"CPU {_v(r.cpu_pct, '%')}."
        )
    if s.alarms:
        lines.append(
            "CloudWatch alarms: "
            + "; ".join(
                f"{a.name} is {a.state}" + (f" for {a.since_minutes}m" if a.since_minutes else "")
                for a in s.alarms
            )
            + "."
        )
    else:
        lines.append("CloudWatch alarms: none reported.")
    if s.recent_changes:
        lines.append("Recent changes: " + "; ".join(s.recent_changes) + ".")
    if s.log_excerpts:
        lines.append("Log excerpts:")
        lines.extend(f"  {x}" for x in s.log_excerpts)
    return "\n".join(lines)
