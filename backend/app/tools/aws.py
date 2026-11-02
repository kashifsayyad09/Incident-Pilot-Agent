"""Live AWS backend. Read-only: every client is wrapped by `readonly_client`.

Targets come from settings (target group ARN, DB instance id, log group). Anything not
configured or not returned by AWS stays None / "not measured"; nothing is estimated.
Log text is untrusted data: it is truncated and later passed to the model as evidence only.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    CredentialRetrievalError,
    NoCredentialsError,
    NoRegionError,
    PartialCredentialsError,
    ProfileNotFound,
)

from app.config import Mode, Settings
from app.schemas import IncidentSummary, ServiceKind, Severity, ToolOption
from app.state import AlarmInfo, AlbState, Ec2State, IncidentState, RdsState

from .aws_guard import ALLOWED_OPERATIONS, readonly_client
from .base import RUNNABLE_TOOLS, DiagnosticsError, DiagnosticsUnavailable, ToolRun

LIVE_ID = "live-current"
MAX_LOG_LINES = 15
MAX_LOG_CHARS = 300
MAX_INSTANCES = 20
_DENIED = {
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedOperation",
    "UnrecognizedClientException",
    "ExpiredToken",
    "ExpiredTokenException",
    "InvalidClientTokenId",
    "AuthFailure",
}


def _truncate(s: str, n: int = MAX_LOG_CHARS) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _map(e: Exception) -> Exception:
    if isinstance(
        e,
        NoCredentialsError | PartialCredentialsError | CredentialRetrievalError | ProfileNotFound,
    ):
        return DiagnosticsUnavailable(
            "AWS credentials not found. Use an IAM role, SSO profile or environment credentials "
            "with the read-only policy from infra/iam/."
        )
    if isinstance(e, NoRegionError):
        return DiagnosticsUnavailable("No AWS region configured. Set AWS_REGION.")
    if isinstance(e, ClientError):
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", "")
        if code in _DENIED:
            return DiagnosticsUnavailable(
                f"AWS denied the read-only call ({code}). Check the IAM policy. {msg}".strip()
            )
        if code in {"Throttling", "ThrottlingException", "RequestLimitExceeded"}:
            return DiagnosticsUnavailable(f"AWS throttled the request ({code}).", retryable=True)
        return DiagnosticsError(f"AWS returned {code}: {msg}")
    if isinstance(e, BotoCoreError):
        return DiagnosticsUnavailable(
            f"Could not reach AWS ({type(e).__name__}). Check network access and region.",
            retryable=True,
        )
    return DiagnosticsError(f"Unexpected AWS failure ({type(e).__name__}).")


def _latest(values: list[float]) -> float | None:
    return values[0] if values else None  # series are requested newest-first


class AwsBackend:
    mode = Mode.LIVE

    def __init__(
        self,
        settings: Settings,
        *,
        session: Any | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        import boto3

        self._s = settings
        self._session = session or boto3.Session()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._clients: dict[str, Any] = {}
        self._calls: list[str] = []

    # ---- plumbing -----------------------------------------------------------------------
    def _client(self, service: str) -> Any:
        if service not in self._clients:
            self._clients[service] = readonly_client(
                self._session, service, region=self._s.aws_region
            )
        return self._clients[service]

    def _call(self, service: str, op: str, **kwargs: Any) -> Any:
        if (service, op) not in ALLOWED_OPERATIONS:
            raise DiagnosticsError(f"{service}:{op} is not an allowed read-only call.")
        self._calls.append(ALLOWED_OPERATIONS[(service, op)])
        client = self._client(service)
        # botocore's own operation -> python method table (handles names like DescribeDBInstances)
        method = {v: k for k, v in client.meta.method_to_api_mapping.items()}[op]
        try:
            return getattr(client, method)(**kwargs)
        except (ClientError, BotoCoreError) as e:
            raise _map(e) from e

    def _window(self) -> tuple[datetime, datetime]:
        end = self._clock()
        return end - timedelta(minutes=self._s.live_window_minutes), end

    def _metrics(self, queries: list[dict[str, Any]]) -> dict[str, list[float]]:
        """GetMetricData for the window; returns id -> values, newest first."""
        if not queries:
            return {}
        start, end = self._window()
        out: dict[str, list[float]] = {}
        token: str | None = None
        while True:
            kw: dict[str, Any] = {
                "MetricDataQueries": queries,
                "StartTime": start,
                "EndTime": end,
                "ScanBy": "TimestampDescending",
            }
            if token:
                kw["NextToken"] = token
            r = self._call("cloudwatch", "GetMetricData", **kw)
            for res in r.get("MetricDataResults", []):
                out.setdefault(res["Id"], []).extend(res.get("Values", []))
            token = r.get("NextToken")
            if not token:
                return out

    @staticmethod
    def _q(qid: str, ns: str, metric: str, dims: dict[str, str], stat: str) -> dict[str, Any]:
        return {
            "Id": qid,
            "MetricStat": {
                "Metric": {
                    "Namespace": ns,
                    "MetricName": metric,
                    "Dimensions": [{"Name": k, "Value": v} for k, v in dims.items()],
                },
                "Period": 300,
                "Stat": stat,
            },
            "ReturnData": True,
        }

    # ---- resource lookups ---------------------------------------------------------------
    def _targets(self) -> list[dict[str, Any]]:
        if not self._s.live_target_group_arn:
            return []
        r = self._call(
            "elbv2", "DescribeTargetHealth", TargetGroupArn=self._s.live_target_group_arn
        )
        return r.get("TargetHealthDescriptions", [])

    def _lb_dimension(self) -> tuple[str, str] | None:
        """(LoadBalancer, TargetGroup) CloudWatch dimension values."""
        arn = self._s.live_target_group_arn
        if not arn:
            return None
        r = self._call("elbv2", "DescribeTargetGroups", TargetGroupArns=[arn])
        groups = r.get("TargetGroups", [])
        if not groups or not groups[0].get("LoadBalancerArns"):
            return None
        lb_arn = groups[0]["LoadBalancerArns"][0]
        lb = lb_arn.split(":loadbalancer/", 1)[-1]
        tg = arn.rsplit(":", 1)[-1]
        return lb, tg

    def _instance_ids(self, targets: list[dict[str, Any]]) -> list[str]:
        ids = [
            t["Target"]["Id"]
            for t in targets
            if str(t.get("Target", {}).get("Id", "")).startswith("i-")
        ]
        return list(dict.fromkeys(ids))[:MAX_INSTANCES]

    def _alarms(self) -> list[dict[str, Any]]:
        kw: dict[str, Any] = {"StateValue": "ALARM", "MaxRecords": 50}
        if self._s.live_alarm_name_prefix:
            kw["AlarmNamePrefix"] = self._s.live_alarm_name_prefix
        return self._call("cloudwatch", "DescribeAlarms", **kw).get("MetricAlarms", [])

    # ---- incident snapshot --------------------------------------------------------------
    def _snapshot(self) -> IncidentState:
        w = self._s.live_window_minutes
        targets = self._targets()
        alb = ec2 = rds = None
        queries: list[dict[str, Any]] = []
        dim = self._lb_dimension() if targets or self._s.live_target_group_arn else None
        if dim:
            lb_only = {"LoadBalancer": dim[0]}
            queries += [
                self._q("e5", "AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", lb_only, "Sum"),
                self._q("req", "AWS/ApplicationELB", "RequestCount", lb_only, "Sum"),
                self._q("p95", "AWS/ApplicationELB", "TargetResponseTime", lb_only, "p95"),
            ]
        ids = self._instance_ids(targets)
        for i, iid in enumerate(ids):
            dims = {"InstanceId": iid}
            queries += [
                self._q(f"ca{i}", "AWS/EC2", "CPUUtilization", dims, "Average"),
                self._q(f"cm{i}", "AWS/EC2", "CPUUtilization", dims, "Maximum"),
            ]
        if self._s.live_db_instance_id:
            dims = {"DBInstanceIdentifier": self._s.live_db_instance_id}
            queries += [
                self._q("dbc", "AWS/RDS", "DatabaseConnections", dims, "Maximum"),
                self._q("dbu", "AWS/RDS", "CPUUtilization", dims, "Average"),
            ]
        m = self._metrics(queries)

        if self._s.live_target_group_arn:
            healthy = sum(1 for t in targets if t.get("TargetHealth", {}).get("State") == "healthy")
            e5 = _latest(m.get("e5", []))
            req = _latest(m.get("req", []))
            alb = AlbState(
                http_5xx_count_5m=None if e5 is None else int(e5),
                http_5xx_rate_pct=(round(e5 / req * 100, 2) if e5 is not None and req else None),
                p95_latency_s=(lambda v: None if v is None else round(v, 3))(
                    _latest(m.get("p95", []))
                ),
                healthy_targets=healthy,
                total_targets=len(targets),
            )
        if ids:
            avgs = [sum(m[f"ca{i}"]) / len(m[f"ca{i}"]) for i in range(len(ids)) if m.get(f"ca{i}")]
            maxs = [max(m[f"cm{i}"]) for i in range(len(ids)) if m.get(f"cm{i}")]
            ec2 = Ec2State(
                instances=len(ids),
                cpu_avg_pct=round(sum(avgs) / len(avgs), 1) if avgs else None,
                cpu_max_pct=round(max(maxs), 1) if maxs else None,
                memory_pct=None,  # needs the CloudWatch agent; never estimated
            )
        if self._s.live_db_instance_id:
            c, u = _latest(m.get("dbc", [])), _latest(m.get("dbu", []))
            rds = RdsState(
                connections=None if c is None else int(c),
                max_connections=None,  # not a CloudWatch metric; not measured
                cpu_pct=None if u is None else round(u, 1),
            )
        now = self._clock()
        alarms = [
            AlarmInfo(
                name=a["AlarmName"],
                state=a.get("StateValue", "ALARM"),
                since_minutes=(
                    max(0, int((now - a["StateUpdatedTimestamp"]).total_seconds() // 60))
                    if a.get("StateUpdatedTimestamp")
                    else None
                ),
            )
            for a in self._alarms()
        ]
        return IncidentState(
            incident_id=LIVE_ID,
            window_minutes=w,
            alb=alb,
            ec2=ec2,
            rds=rds,
            alarms=alarms,
            recent_changes=[],  # change history (CloudTrail) is out of scope: not measured
            log_excerpts=[],
        )

    @staticmethod
    def _summary(state: IncidentState) -> IncidentSummary:
        in_alarm = [a for a in state.alarms if a.state == "ALARM"]
        services = []
        if state.alb:
            services.append(ServiceKind.ALB)
        if state.ec2:
            services.append(ServiceKind.EC2)
        if state.rds:
            services.append(ServiceKind.RDS)
        services.append(ServiceKind.CLOUDWATCH)
        sev = Severity.CRITICAL if in_alarm else Severity.INFO
        return IncidentSummary(
            id=LIVE_ID,
            title="Current state of the configured AWS resources",
            summary=(
                f"{len(in_alarm)} CloudWatch alarm(s) in ALARM: "
                + ", ".join(a.name for a in in_alarm[:5])
                if in_alarm
                else "No CloudWatch alarm is in ALARM for the configured scope."
            ),
            category="live",
            severity=sev,
            affected_services=services,
            mode=Mode.LIVE,
        )

    # ---- DiagnosticBackend --------------------------------------------------------------
    def list_incidents(self) -> tuple[list[IncidentSummary], str | None]:
        _, state = self.get_incident(LIVE_ID)  # type: ignore[misc]
        return [self._summary(state)], None

    def get_incident(self, incident_id: str) -> tuple[IncidentSummary, IncidentState] | None:
        if incident_id != LIVE_ID:
            return None
        self._calls = []
        state = self._snapshot()
        return self._summary(state), state

    def run_tool(self, tool: ToolOption, state: IncidentState) -> ToolRun:
        if tool not in RUNNABLE_TOOLS:
            raise DiagnosticsError(f"{tool.value} is not a runnable diagnostic tool.")
        self._calls = []
        started = time.perf_counter()
        fn = {
            ToolOption.INVESTIGATE_LOAD_BALANCER: self._tool_alb,
            ToolOption.INVESTIGATE_EC2: self._tool_ec2,
            ToolOption.INVESTIGATE_DATABASE: self._tool_db,
            ToolOption.INVESTIGATE_CLOUDWATCH_LOGS: self._tool_logs,
        }[tool]
        findings = fn()
        return ToolRun(
            tool=tool,
            mode=Mode.LIVE,
            backend="aws-readonly",
            findings=findings,
            api_calls=sorted(set(self._calls)),
            duration_ms=(time.perf_counter() - started) * 1000,
            executed_at=self._clock(),
        )

    # ---- tools --------------------------------------------------------------------------
    def _need(self, value: str, name: str) -> None:
        if not value:
            raise DiagnosticsUnavailable(
                f"{name} is not configured, so this diagnostic cannot run."
            )

    def _tool_alb(self) -> list[str]:
        self._need(self._s.live_target_group_arn, "INCIDENTPILOT_LIVE_TARGET_GROUP_ARN")
        arn = self._s.live_target_group_arn
        out: list[str] = []
        for t in self._targets():
            th = t.get("TargetHealth", {})
            reason = th.get("Reason")
            desc = th.get("Description")
            out.append(
                f"Target {t.get('Target', {}).get('Id', '?')}: {th.get('State', 'unknown')}"
                + (f" ({reason})" if reason else "")
                + (f" - {_truncate(desc, 120)}" if desc else "")
                + "."
            )
        if not out:
            out.append("The target group has no registered targets.")
        groups = self._call("elbv2", "DescribeTargetGroups", TargetGroupArns=[arn]).get(
            "TargetGroups", []
        )
        if groups:
            g = groups[0]
            out.append(
                f"Health check: {g.get('HealthCheckProtocol', '?')} "
                f"{g.get('HealthCheckPath', '')}, "
                f"interval {g.get('HealthCheckIntervalSeconds', 'not reported')}s, "
                f"timeout {g.get('HealthCheckTimeoutSeconds', 'not reported')}s, "
                f"unhealthy threshold {g.get('UnhealthyThresholdCount', 'not reported')}."
            )
        dim = self._lb_dimension()
        if dim:
            lb = {"LoadBalancer": dim[0]}
            m = self._metrics(
                [
                    self._q("e5", "AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", lb, "Sum"),
                    self._q("t5", "AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", lb, "Sum"),
                ]
            )
            for key, label in (("e5", "ELB 5xx"), ("t5", "target 5xx")):
                v = m.get(key, [])
                out.append(
                    f"{label} count per 5 min over the window: "
                    + (f"latest {int(v[0])}, peak {int(max(v))}." if v else "no datapoints.")
                )
        return out

    def _tool_ec2(self) -> list[str]:
        self._need(self._s.live_target_group_arn, "INCIDENTPILOT_LIVE_TARGET_GROUP_ARN")
        ids = self._instance_ids(self._targets())
        if not ids:
            return ["The target group has no EC2 instance targets."]
        out: list[str] = []

        def launched(i: dict[str, Any]) -> str:
            t = i.get("LaunchTime")
            return t.isoformat() if t else "not reported"

        r = self._call("ec2", "DescribeInstances", InstanceIds=ids)
        for res in r.get("Reservations", []):
            for i in res.get("Instances", []):
                out.append(
                    f"Instance {i['InstanceId']}: {i.get('State', {}).get('Name', 'unknown')}, "
                    f"{i.get('InstanceType', 'type not reported')}, "
                    f"{i.get('Placement', {}).get('AvailabilityZone', 'AZ not reported')}, "
                    f"launched {launched(i)}."
                )
        st = self._call("ec2", "DescribeInstanceStatus", InstanceIds=ids, IncludeAllInstances=True)
        for s in st.get("InstanceStatuses", []):
            out.append(
                f"Instance {s['InstanceId']} status checks: system "
                f"{s.get('SystemStatus', {}).get('Status', 'unknown')}, instance "
                f"{s.get('InstanceStatus', {}).get('Status', 'unknown')}."
            )
        qs = [
            self._q(f"c{n}", "AWS/EC2", "CPUUtilization", {"InstanceId": iid}, "Average")
            for n, iid in enumerate(ids)
        ]
        m = self._metrics(qs)
        for n, iid in enumerate(ids):
            v = m.get(f"c{n}", [])
            out.append(
                f"Instance {iid} CPU average per 5 min: "
                + (f"latest {v[0]:.1f}%, peak {max(v):.1f}%." if v else "no datapoints.")
            )
        return out

    def _tool_db(self) -> list[str]:
        self._need(self._s.live_db_instance_id, "INCIDENTPILOT_LIVE_DB_INSTANCE_ID")
        dbid = self._s.live_db_instance_id
        out: list[str] = []
        for d in self._call("rds", "DescribeDBInstances", DBInstanceIdentifier=dbid).get(
            "DBInstances", []
        ):
            out.append(
                f"DB {d.get('DBInstanceIdentifier', dbid)}: "
                f"status {d.get('DBInstanceStatus', '?')}, "
                f"{d.get('DBInstanceClass', 'class not reported')}, "
                f"{d.get('Engine', 'engine not reported')}, "
                f"multi-AZ {d.get('MultiAZ', 'not reported')}."
            )
        dims = {"DBInstanceIdentifier": dbid}
        m = self._metrics(
            [
                self._q("dc", "AWS/RDS", "DatabaseConnections", dims, "Maximum"),
                self._q("du", "AWS/RDS", "CPUUtilization", dims, "Average"),
                self._q("dm", "AWS/RDS", "FreeableMemory", dims, "Average"),
            ]
        )
        for key, label, fmt in (
            ("dc", "Connections (max per 5 min)", "{:.0f}"),
            ("du", "CPU average per 5 min", "{:.1f}%"),
            ("dm", "Freeable memory (bytes)", "{:.0f}"),
        ):
            v = m.get(key, [])
            out.append(
                f"{label}: "
                + (
                    f"latest {fmt.format(v[0])}, peak {fmt.format(max(v))}, "
                    f"lowest {fmt.format(min(v))}."
                    if v
                    else "no datapoints."
                )
            )
        return out

    def _tool_logs(self) -> list[str]:
        self._need(self._s.live_log_group, "INCIDENTPILOT_LIVE_LOG_GROUP")
        start, end = self._window()
        r = self._call(
            "logs",
            "FilterLogEvents",
            logGroupName=self._s.live_log_group,
            startTime=int(start.timestamp() * 1000),
            endTime=int(end.timestamp() * 1000),
            filterPattern="?ERROR ?Error ?Exception ?FATAL ?timeout ?5xx",
            limit=MAX_LOG_LINES,
        )
        events = r.get("events", [])
        if not events:
            return [
                f"Log group {self._s.live_log_group}: no lines matching error patterns in the last "
                f"{self._s.live_window_minutes} minutes."
            ]
        out = [
            f"Log group {self._s.live_log_group}: {len(events)} matching line(s) shown "
            f"(limit {MAX_LOG_LINES}), newest window {self._s.live_window_minutes} min."
        ]
        out += [f"log: {_truncate(e.get('message', ''))}" for e in events]
        return out
