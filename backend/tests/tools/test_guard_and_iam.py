import json
import pathlib

import boto3
import pytest

from app.tools.aws_guard import ALLOWED_OPERATIONS, ReadOnlyViolation, readonly_client

INFRA = pathlib.Path(__file__).resolve().parents[3] / "infra"
WRITE_VERBS = ("Create", "Delete", "Put", "Update", "Terminate", "Modify", "Reboot", "Stop")


def session():
    return boto3.Session(aws_access_key_id="x", aws_secret_access_key="y")


@pytest.mark.parametrize(
    "service,call",
    [
        ("ec2", lambda c: c.terminate_instances(InstanceIds=["i-1"])),
        ("ec2", lambda c: c.stop_instances(InstanceIds=["i-1"])),
        ("rds", lambda c: c.reboot_db_instance(DBInstanceIdentifier="d")),
        ("logs", lambda c: c.delete_log_group(logGroupName="g")),
        ("cloudwatch", lambda c: c.put_metric_alarm(AlarmName="a")),
        ("elbv2", lambda c: c.deregister_targets(TargetGroupArn="a", Targets=[])),
    ],
)
def test_write_operations_are_refused_before_any_request(service, call):
    c = readonly_client(session(), service, region="us-east-1")
    with pytest.raises(ReadOnlyViolation):
        call(c)


def test_every_allowed_operation_exists_and_is_a_read_verb():
    for (service, op), action in ALLOWED_OPERATIONS.items():
        client = session().client(service, region_name="us-east-1")
        assert op in client.meta.service_model.operation_names
        assert not op.startswith(WRITE_VERBS)
        assert action.split(":")[1] == op


def policy_actions(path):
    doc = json.loads(path.read_text())
    return {a for st in doc["Statement"] for a in st["Action"]}


def test_readonly_policy_matches_allowlist_exactly():
    actions = policy_actions(INFRA / "iam" / "incidentpilot-readonly-policy.json")
    assert actions == set(ALLOWED_OPERATIONS.values())
    assert all(a.split(":")[1].startswith(("Describe", "Get", "Filter")) for a in actions)


def test_cloudformation_role_lists_the_same_actions():
    text = (INFRA / "cloudformation" / "incidentpilot-role.yaml").read_text()
    for action in ALLOWED_OPERATIONS.values():
        assert action in text
    for bad in ("iam:", "ec2:Terminate", "rds:Delete", 'Resource: "*"\n                Action'):
        assert bad not in text


def test_bedrock_policy_is_invoke_only():
    assert policy_actions(INFRA / "iam" / "bedrock-invoke-policy.json") == {
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
    }
