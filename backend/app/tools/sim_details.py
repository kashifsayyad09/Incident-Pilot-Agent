"""SIMULATION tool output: synthetic, hand-written detail for the five sample incidents.

NOT measurements of any real system. Each entry is consistent with the headline numbers in
`app.simulation.evidence` so a run reads like a plausible diagnostic. Every tool result is
labelled simulation in the report and UI.
"""

from __future__ import annotations

from app.schemas import ToolOption as T

LB, EC2, DB, LOGS = (
    T.INVESTIGATE_LOAD_BALANCER,
    T.INVESTIGATE_EC2,
    T.INVESTIGATE_DATABASE,
    T.INVESTIGATE_CLOUDWATCH_LOGS,
)

TOOL_DETAILS: dict[str, dict[T, list[str]]] = {
    "sim-alb-503": {
        LB: [
            "Target group web-tg: i-0a1 unhealthy (Target.Timeout), i-0a2 unhealthy "
            "(Target.Timeout), i-0a3 unhealthy (Target.Timeout), i-0a4 unhealthy (Target.Timeout).",
            "Health check config: HTTP /healthz, interval 30s, timeout 5s, unhealthy threshold 2.",
        ],
        EC2: [
            "4 instances running, instance status checks 4 of 4 passing.",
            "Per-instance CPU average: i-0a1 27%, i-0a2 22%, i-0a3 19%, i-0a4 16%.",
        ],
        DB: ["RDS instance status available; connections 38 of 200; CPU 18%."],
        LOGS: [
            "Log group /app/web, last 30 min: 3 matching lines, all 'connection timed out on "
            "/healthz'; no application errors before the health checks began failing.",
        ],
    },
    "sim-ec2-cpu": {
        LB: [
            "Target group web-tg: 4 of 4 targets healthy; p95 target response time 4.8s.",
        ],
        EC2: [
            "4 instances running; CPU average per instance: i-0b1 99%, i-0b2 97%, i-0b3 95%, "
            "i-0b4 93%.",
            "Instance status checks 4 of 4 passing; no instance state changes in the window.",
        ],
        DB: ["RDS instance status available; connections 41 of 200; CPU 22%."],
        LOGS: [
            "Log group /app/web, last 30 min: 'worker pool exhausted, request queue length 340' "
            "repeated on all four instances.",
        ],
    },
    "sim-rds-connections": {
        LB: ["Target group web-tg: 4 of 4 targets healthy; 5xx rate 6.0%; p95 latency 2.1s."],
        EC2: [
            "4 instances running; CPU average 31%, max 38%; instance status checks 4 of 4 passing."
        ],
        DB: [
            "RDS instance status available; connections 187 of 200; CPU 34%.",
            "Connection count rose steadily over the window with no drop; instance class "
            "db.r6g.large, single AZ.",
        ],
        LOGS: [
            "Log group /app/web, last 30 min: 'remaining connection slots are reserved' and "
            "'could not acquire database connection within 5000ms' on all instances.",
        ],
    },
    "sim-bad-deploy": {
        LB: ["Target group web-tg: 4 of 4 targets healthy; 5xx rate 9.0%; p95 latency 0.9s."],
        EC2: [
            "4 instances running; CPU average 52%, max 58%; all instances launched with the "
            "same image as before.",
        ],
        DB: ["RDS instance status available; connections 64 of 200; CPU 27%."],
        LOGS: [
            "Log group /app/web, last 30 min: NullPointerException at "
            "OrderService.checkout(OrderService.java:212) on POST /api/checkout; the first "
            "occurrence is after deployment of app v2.14.0.",
            "No matching errors before the deployment in the same window.",
        ],
    },
    "sim-conflicting-signals": {
        LB: [
            "Target group web-tg: 3 of 4 targets healthy; i-0c3 is draining "
            "(Target.DeregistrationInProgress).",
        ],
        EC2: [
            "3 instances running; CPU average 44%, max 68% (i-0c2).",
        ],
        DB: ["RDS instance status available; connections 118 of 200; CPU 41%."],
        LOGS: [
            "Log group /app/web, last 30 min: 'upstream timeout after 3000ms' 3 occurrences; "
            "no other error patterns.",
        ],
    },
}
