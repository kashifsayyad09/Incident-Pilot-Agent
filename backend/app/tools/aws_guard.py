"""Read-only enforcement for every Boto3 client the app creates.

Two layers: (1) IAM, via the templates in infra/, and (2) this in-process allowlist, which
refuses any operation not listed, before a request is built. The allowlist is the single
source of truth; tests assert the IAM policy matches it and contains no write action.
"""

from __future__ import annotations

from typing import Any

from botocore.config import Config

# (boto3 service name, API operation) -> IAM action
ALLOWED_OPERATIONS: dict[tuple[str, str], str] = {
    ("elbv2", "DescribeTargetHealth"): "elasticloadbalancing:DescribeTargetHealth",
    ("elbv2", "DescribeTargetGroups"): "elasticloadbalancing:DescribeTargetGroups",
    ("elbv2", "DescribeLoadBalancers"): "elasticloadbalancing:DescribeLoadBalancers",
    ("cloudwatch", "GetMetricData"): "cloudwatch:GetMetricData",
    ("cloudwatch", "DescribeAlarms"): "cloudwatch:DescribeAlarms",
    ("ec2", "DescribeInstances"): "ec2:DescribeInstances",
    ("ec2", "DescribeInstanceStatus"): "ec2:DescribeInstanceStatus",
    ("rds", "DescribeDBInstances"): "rds:DescribeDBInstances",
    ("logs", "FilterLogEvents"): "logs:FilterLogEvents",
}


class ReadOnlyViolation(Exception):
    """An AWS operation outside the read-only allowlist was attempted."""


def readonly_client(session: Any, service: str, *, region: str, timeout_s: float = 10.0) -> Any:
    client = session.client(
        service,
        region_name=region,
        config=Config(
            connect_timeout=5,
            read_timeout=timeout_s,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )

    def _guard(params: Any, model: Any, **_: Any) -> None:
        if (service, model.name) not in ALLOWED_OPERATIONS:
            raise ReadOnlyViolation(f"{service}:{model.name} is not an allowed read-only call.")

    client.meta.events.register("before-parameter-build.*.*", _guard)
    return client
