"""Decision API. `stub_client` is a test double for the Decider HTTP server."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.deps import get_decider_client
from app.main import create_app
from decision_patterns.tool_selection import HttpDeciderClient

OPTION_IDS = [
    "investigate_load_balancer",
    "investigate_ec2",
    "investigate_database",
    "investigate_cloudwatch_logs",
    "collect_more_evidence",
]


def stub_answer(choice="investigate_load_balancer", confidence=0.83, **kw):
    probs = {o: 0.05 for o in OPTION_IDS}
    probs[choice] = 0.8
    body = {
        "model": "stub-test-double",
        "answers": {
            "next_tool": {
                "type": "choice",
                "choice": choice,
                "probabilities": probs,
                "confidence": confidence,
            }
        },
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "latency_ms": 111.1,
    }
    body.update(kw)
    return body


def app_with(handler):
    app = create_app()
    client = HttpDeciderClient(
        "http://decider.test", http=httpx.Client(transport=httpx.MockTransport(handler))
    )
    app.dependency_overrides[get_decider_client] = lambda: client
    return TestClient(app)


def ok_handler(body=None):
    def h(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "model": "stub-test-double"})
        return httpx.Response(200, json=body or stub_answer())

    return h


def test_unconfigured_decider_is_reported_unavailable_and_run_returns_503(client):
    st = client.get("/api/v1/decision/status").json()
    assert st["available"] is False and "INCIDENTPILOT_DECIDER_URL" in st["reason"]
    r = client.post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503
    assert "selected" not in r.json()  # no fabricated decision


def test_status_available_when_server_healthy(monkeypatch):
    monkeypatch.setenv("INCIDENTPILOT_DECIDER_URL", "http://decider.test")
    get_settings.cache_clear()
    c = app_with(ok_handler())
    st = c.get("/api/v1/decision/status").json()
    assert st["available"] is True and "stub-test-double" in st["adapter"]


def test_run_returns_model_numbers_unmodified_with_full_trace():
    c = app_with(ok_handler(stub_answer(confidence=0.8312)))
    r = c.post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["selected"] == "investigate_load_balancer"
    assert d["confidence"] == 0.8312
    assert d["latency_ms"] == 111.1
    assert d["model"] == "stub-test-double"
    assert d["meets_threshold"] is True and d["outcome"] == "tool_selected"
    assert d["tool_invoked"] is None  # tools arrive in Phase 4
    assert d["options"] == OPTION_IDS and d["mode"] == "simulation"
    assert "healthy targets 0 of 4" in d["state_text"]
    assert d["input_state"]["incident_id"] == "sim-alb-503"
    assert d["question"]


def test_low_confidence_requests_more_evidence():
    c = app_with(ok_handler(stub_answer("investigate_ec2", confidence=0.31)))
    d = c.post("/api/v1/decision/run", json={"incident_id": "sim-ec2-cpu"}).json()
    assert d["selected"] == "investigate_ec2"  # model's choice kept
    assert d["meets_threshold"] is False
    assert d["outcome"] == "evidence_requested"


def test_unreachable_server_returns_503_not_a_fallback():
    def boom(request):
        raise httpx.ConnectError("refused")

    r = app_with(boom).post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503 and "selected" not in r.json()


def test_garbage_from_server_returns_502():
    bad = stub_answer(confidence=None)
    r = app_with(ok_handler(bad)).post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 502


def test_unknown_incident_404_and_live_mode_501(monkeypatch):
    c = app_with(ok_handler())
    assert c.post("/api/v1/decision/run", json={"incident_id": "nope"}).status_code == 404
    monkeypatch.setenv("INCIDENTPILOT_MODE", "live")
    get_settings.cache_clear()
    c2 = app_with(ok_handler())
    assert c2.post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"}).status_code == 501


def test_health_reflects_decider_availability(monkeypatch):
    monkeypatch.setenv("INCIDENTPILOT_DECIDER_URL", "http://decider.test")
    get_settings.cache_clear()
    comps = {c["name"]: c for c in app_with(ok_handler()).get("/health").json()["components"]}
    assert comps["decider_2b"]["available"] is True


@pytest.mark.parametrize("bad", [{}, {"incident_id": 5}])
def test_bad_request_body_is_422(bad):
    assert app_with(ok_handler()).post("/api/v1/decision/run", json=bad).status_code == 422
