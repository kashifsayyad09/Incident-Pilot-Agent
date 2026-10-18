"""SIMULATION evidence for the five sample incidents.

All values below are synthetic, hand-written sample data. They are NOT measurements of
any real system. They exist so the Decision Lab can run end to end without AWS access.

`REFERENCE_LABELS` records which tool a human operator would reasonably pick first. It is
used ONLY by tests and by scripts/eval_decider.py to report how often the model agrees.
It is never read by the decision path.
"""

from __future__ import annotations

from app.state import AlarmInfo, AlbState, Ec2State, IncidentState, RdsState

EVIDENCE: dict[str, IncidentState] = {
    "sim-alb-503": IncidentState(
        incident_id="sim-alb-503",
        alb=AlbState(
            http_5xx_count_5m=1840,
            http_5xx_rate_pct=96.0,
            p95_latency_s=0.2,
            healthy_targets=0,
            total_targets=4,
        ),
        ec2=Ec2State(instances=4, cpu_avg_pct=21.0, cpu_max_pct=27.0),
        rds=RdsState(connections=38, max_connections=200, cpu_pct=18.0),
        alarms=[
            AlarmInfo(name="alb-5xx-high", state="ALARM", since_minutes=9),
            AlarmInfo(name="tg-healthy-hosts-low", state="ALARM", since_minutes=11),
        ],
        log_excerpts=[
            "elb: 503 Service Unavailable, no healthy targets in target group web-tg",
            "health check failed for all targets: connection timed out on /healthz",
        ],
    ),
    "sim-ec2-cpu": IncidentState(
        incident_id="sim-ec2-cpu",
        alb=AlbState(
            http_5xx_count_5m=22,
            http_5xx_rate_pct=0.4,
            p95_latency_s=4.8,
            healthy_targets=4,
            total_targets=4,
        ),
        ec2=Ec2State(instances=4, cpu_avg_pct=96.0, cpu_max_pct=99.0),
        rds=RdsState(connections=41, max_connections=200, cpu_pct=22.0),
        alarms=[AlarmInfo(name="ec2-cpu-high", state="ALARM", since_minutes=25)],
        log_excerpts=["app: worker pool exhausted, request queue length 340"],
    ),
    "sim-rds-connections": IncidentState(
        incident_id="sim-rds-connections",
        alb=AlbState(
            http_5xx_count_5m=310,
            http_5xx_rate_pct=6.0,
            p95_latency_s=2.1,
            healthy_targets=4,
            total_targets=4,
        ),
        ec2=Ec2State(instances=4, cpu_avg_pct=31.0, cpu_max_pct=38.0),
        rds=RdsState(connections=187, max_connections=200, cpu_pct=34.0),
        alarms=[AlarmInfo(name="rds-connections-high", state="ALARM", since_minutes=14)],
        log_excerpts=[
            "app: FATAL: remaining connection slots are reserved for non-replication superuser",
            "app: could not acquire database connection within 5000ms",
        ],
    ),
    "sim-bad-deploy": IncidentState(
        incident_id="sim-bad-deploy",
        alb=AlbState(
            http_5xx_count_5m=520,
            http_5xx_rate_pct=9.0,
            p95_latency_s=0.9,
            healthy_targets=4,
            total_targets=4,
        ),
        ec2=Ec2State(instances=4, cpu_avg_pct=52.0, cpu_max_pct=58.0),
        rds=RdsState(connections=64, max_connections=200, cpu_pct=27.0),
        alarms=[AlarmInfo(name="app-error-rate-high", state="ALARM", since_minutes=11)],
        recent_changes=["deployment of app v2.14.0 completed 12 minutes ago"],
        log_excerpts=[
            "app: NullPointerException at OrderService.checkout(OrderService.java:212)",
            "app: NullPointerException at OrderService.checkout(OrderService.java:212)",
            "app: 500 returned for POST /api/checkout",
        ],
    ),
    "sim-conflicting-signals": IncidentState(
        incident_id="sim-conflicting-signals",
        alb=AlbState(
            http_5xx_count_5m=40,
            http_5xx_rate_pct=0.8,
            p95_latency_s=1.4,
            healthy_targets=3,
            total_targets=4,
        ),
        ec2=Ec2State(instances=3, cpu_avg_pct=44.0, cpu_max_pct=68.0),
        rds=RdsState(connections=118, max_connections=200, cpu_pct=41.0),
        alarms=[
            AlarmInfo(name="alb-5xx-high", state="INSUFFICIENT_DATA", since_minutes=6),
            AlarmInfo(name="ec2-cpu-high", state="OK"),
            AlarmInfo(name="rds-connections-high", state="OK"),
        ],
        log_excerpts=[
            "app: upstream timeout after 3000ms (3 occurrences)",
            "elb: target i-0a1 is draining",
        ],
    ),
}

REFERENCE_LABELS: dict[str, str] = {
    "sim-alb-503": "investigate_load_balancer",
    "sim-ec2-cpu": "investigate_ec2",
    "sim-rds-connections": "investigate_database",
    "sim-bad-deploy": "investigate_cloudwatch_logs",
    "sim-conflicting-signals": "collect_more_evidence",
}


def get_evidence(incident_id: str) -> IncidentState | None:
    return EVIDENCE.get(incident_id)
