import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.schemas import ToolOption


def test_health_reports_simulation_and_unavailable_components(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "simulation"
    comps = {c["name"]: c for c in body["components"]}
    assert comps["api"]["available"] is True
    assert comps["decider_2b"]["available"] is False
    assert comps["decider_2b"]["detail"]


def test_incidents_lists_five_labeled_simulation_scenarios(client):
    r = client.get("/api/v1/incidents")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "simulation"
    assert len(body["incidents"]) == 5
    assert all(i["mode"] == "simulation" for i in body["incidents"])
    assert len({i["id"] for i in body["incidents"]}) == 5


def test_incident_detail_and_404(client):
    assert client.get("/api/v1/incidents/sim-alb-503").status_code == 200
    assert client.get("/api/v1/incidents/nope").status_code == 404


def test_live_mode_does_not_serve_simulation_data(monkeypatch):
    monkeypatch.setenv("INCIDENTPILOT_MODE", "live")
    get_settings.cache_clear()
    c = TestClient(create_app())
    body = c.get("/api/v1/incidents").json()
    assert body["mode"] == "live"
    assert body["incidents"] == []
    assert c.get("/api/v1/incidents/sim-alb-503").status_code == 501


def test_decision_status_is_explicitly_unavailable(client):
    body = client.get("/api/v1/decision/status").json()
    assert body["available"] is False
    assert body["reason"]
    assert body["options"] == [o.value for o in ToolOption]
    assert body["confidence_threshold"] == 0.60


def test_decision_run_never_fabricates_a_result(client):
    r = client.post("/api/v1/decision/run", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"].lower()


def test_api_key_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("INCIDENTPILOT_API_KEY", "s3cret")
    get_settings.cache_clear()
    c = TestClient(create_app())
    assert c.get("/health").status_code == 200  # health stays open
    assert c.get("/api/v1/incidents").status_code == 401
    assert c.get("/api/v1/incidents", headers={"X-API-Key": "wrong"}).status_code == 401
    assert c.get("/api/v1/incidents", headers={"X-API-Key": "s3cret"}).status_code == 200


def test_cors_allows_only_configured_origin(client):
    ok = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.options(
        "/health",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_wildcard_cors_rejected():
    with pytest.raises(ValueError):
        Settings(cors_origins="*")


def test_invalid_confidence_threshold_rejected():
    with pytest.raises(ValueError):
        Settings(decider_confidence_threshold=1.5)
