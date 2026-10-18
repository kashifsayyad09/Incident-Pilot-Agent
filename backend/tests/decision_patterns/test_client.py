"""HttpDeciderClient against a stubbed HTTP transport.

The transport below is a TEST DOUBLE for the network layer. It is not the model and no
test here claims anything about the model's accuracy. What is verified: the request we
send is valid under the REAL strands-decider wire schema, and every way a response can be
wrong is rejected rather than passed on.
"""

import json

import httpx
import pytest

from decision_patterns.tool_selection import (
    DeciderProtocolError,
    DeciderUnavailable,
    HttpDeciderClient,
)
from tests.fixtures.strands_decider_schema import SystemOneRequest

OPTIONS = {"a": "option a", "b": "option b", "c": "option c"}


def ok_body(**over):
    body = {
        "model": "stub-model",
        "answers": {
            "q": {
                "type": "choice",
                "choice": "a",
                "probabilities": {"a": 0.7, "b": 0.2, "c": 0.1},
                "confidence": 0.55,
            }
        },
        "usage": {"input_tokens": 10, "output_tokens": 1},
        "latency_ms": 123.4,
    }
    body.update(over)
    return body


def client_for(handler):
    return HttpDeciderClient(
        "http://decider.test", http=httpx.Client(transport=httpx.MockTransport(handler))
    )


def test_request_is_valid_under_the_real_wire_schema():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=ok_body())

    client_for(handler).ask_choice("some state", "Which?", OPTIONS, name="q")
    assert seen["path"] == "/v1/systemone"
    req = SystemOneRequest.model_validate(seen["body"])  # the real server's request model
    assert req.questions["q"].type == "choice"
    assert dict(req.questions["q"].criteria) == OPTIONS


def test_confidence_and_probabilities_pass_through_unmodified():
    r = client_for(lambda req: httpx.Response(200, json=ok_body())).ask_choice(
        "s", "Which?", OPTIONS, name="q"
    )
    assert r.choice == "a"
    assert r.confidence == 0.55  # NOT the 0.7 top probability: never recomputed
    assert r.probabilities == {"a": 0.7, "b": 0.2, "c": 0.1}
    assert r.latency_ms == 123.4
    assert r.model == "stub-model"
    assert r.roundtrip_ms >= 0


def test_missing_latency_is_none_not_zero():
    body = ok_body()
    del body["latency_ms"]
    r = client_for(lambda req: httpx.Response(200, json=body)).ask_choice(
        "s", "Which?", OPTIONS, name="q"
    )
    assert r.latency_ms is None


def _answer(**over):
    a = {
        "type": "choice",
        "choice": "a",
        "probabilities": {"a": 0.7, "b": 0.2, "c": 0.1},
        "confidence": 0.55,
    }
    a.update(over)
    return ok_body(answers={"q": a})


@pytest.mark.parametrize(
    "body",
    [
        _answer(choice="zzz"),  # not an offered option
        _answer(confidence=None),  # no confidence: never invented
        _answer(confidence=1.5),  # out of range
        _answer(confidence=True),  # bool is not a number
        _answer(probabilities={"a": 1.0}),  # options mismatch
        _answer(probabilities={"a": "x", "b": 0.2, "c": 0.1}),  # non-numeric
        _answer(type="score"),  # wrong answer type
        ok_body(answers={}),  # answer missing
        ok_body(answers=None),
        ["not", "an", "object"],
    ],
)
def test_invalid_responses_are_rejected(body):
    c = client_for(lambda req: httpx.Response(200, json=body))
    with pytest.raises(DeciderProtocolError):
        c.ask_choice("s", "Which?", OPTIONS, name="q")


def test_http_error_and_non_json_are_protocol_errors():
    with pytest.raises(DeciderProtocolError, match="422"):
        client_for(lambda r: httpx.Response(422, json={"detail": "bad"})).ask_choice(
            "s", "Q", OPTIONS, name="q"
        )
    with pytest.raises(DeciderProtocolError, match="non-JSON"):
        client_for(lambda r: httpx.Response(200, text="<html>")).ask_choice(
            "s", "Q", OPTIONS, name="q"
        )


def test_unreachable_server_is_unavailable():
    def boom(request):
        raise httpx.ConnectError("refused")

    c = client_for(boom)
    with pytest.raises(DeciderUnavailable, match="ConnectError"):
        c.ask_choice("s", "Q", OPTIONS, name="q")
    with pytest.raises(DeciderUnavailable):
        c.health()


def test_timeout_is_unavailable():
    def slow(request):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(DeciderUnavailable, match="ReadTimeout"):
        client_for(slow).ask_choice("s", "Q", OPTIONS, name="q")


def test_health_requires_status_ok():
    assert client_for(lambda r: httpx.Response(200, json={"status": "ok", "model": "m"})).health()
    for resp in (
        httpx.Response(500),
        httpx.Response(200, json={"status": "loading"}),
        httpx.Response(200, text="nope"),
    ):
        with pytest.raises(DeciderUnavailable):
            client_for(lambda r, resp=resp: resp).health()
