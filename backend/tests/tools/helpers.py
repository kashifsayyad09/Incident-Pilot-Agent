"""TEST DOUBLE of AWS API replies (botocore Stubber on real clients). These verify our request
building, parsing and read-only enforcement; they are not AWS behaviour."""

from datetime import UTC, datetime, timedelta

import boto3
from botocore.stub import Stubber

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


class StubSession:
    def __init__(self) -> None:
        self.clients: dict[str, object] = {}
        self.stubbers: dict[str, Stubber] = {}
        self._base = boto3.Session(aws_access_key_id="testing", aws_secret_access_key="testing")

    def client(self, service, region_name=None, config=None):
        if service not in self.clients:
            c = self._base.client(service, region_name=region_name, config=config)
            self.clients[service] = c
            self.stubbers[service] = Stubber(c)
            self.stubbers[service].activate()
        return self.clients[service]

    def queue(self, service, method, response=None, *, error=None, expected=None):
        if service not in self.clients:
            self.client(service, region_name="us-east-1")
        st = self.stubbers[service]
        if error:
            st.add_client_error(method, service_error_code=error, expected_params=expected)
        else:
            st.add_response(method, response, expected_params=expected)

    def assert_all_consumed(self):
        for st in self.stubbers.values():
            st.assert_no_pending_responses()


def metric(qid, values):
    return {
        "Id": qid,
        "Label": qid,
        "Timestamps": [NOW - timedelta(minutes=5 * i) for i in range(len(values))],
        "Values": values,
        "StatusCode": "Complete",
    }


def metric_response(**series):
    return {"MetricDataResults": [metric(k, v) for k, v in series.items()]}
