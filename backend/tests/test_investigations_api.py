"""Investigation API. ScriptedAnalyzer and the MockTransport Decider are TEST DOUBLES that
exercise our orchestration; they are not Bedrock or Decider 2B."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.agent.analyzer import AnalysisError, AnalysisUnavailable, AnalyzerResult
from app.agent.report import Fact, IncidentAnalysis
from app.agent.store import ReportStore
from app.config import Settings, get_settings
from app.deps import get_analyzer, get_decider_client, get_report_store
from app.main import create_app
from decision_patterns.tool_selection import HttpDeciderClient
from tests.test_decision_api import ok_handler, stub_answer


class ScriptedAnalyzer:
    model_id = "scripted-test-double"
    region = "test-region"

    def __init__(self, analysis=None, error=None):
        self.error = error
        self.analysis = analysis or IncidentAnalysis(
            summary="Scripted summary",
            confirmed_facts=[Fact(statement="Invented 31337 thing", evidence_ids=["E1"])],
            hypotheses=[],
            probable_root_causes=[],
            recommended_actions=[],
            impact_assessment="Not determinable from the available evidence.",
            evidence_gaps=[],
        )
        self.calls = 0
        self.last_decision = "unset"

    def analyze(self, bundle, decision):
        self.calls += 1
        self.last_decision = decision
        if self.error:
            raise self.error
        return AnalyzerResult(self.analysis, self.model_id, self.region, 12.5)


def make(tmp_path, analyzer=None, decider_handler=None):
    app = create_app()
    app.dependency_overrides[get_report_store] = lambda: ReportStore(tmp_path)
    app.dependency_overrides[get_analyzer] = lambda: analyzer
    if decider_handler:
        c = HttpDeciderClient(
            "http://decider.test", http=httpx.Client(transport=httpx.MockTransport(decider_handler))
        )
        app.dependency_overrides[get_decider_client] = lambda: c
    return TestClient(app)


def test_success_runs_decision_then_analysis_and_stores(tmp_path):
    an = ScriptedAnalyzer()
    c = make(tmp_path, an, ok_handler())
    r = c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["mode"] == "simulation" and rep["status"] == "complete"
    assert rep["decision"]["selected"] == "investigate_load_balancer"
    assert rep["generation"]["ai_generated"] is True
    assert "advisory" in rep["advisory_notice"].lower()
    # grounding demoted the fact with an invented number
    assert rep["grounding"]["facts_demoted"] == 1 and rep["analysis"]["confirmed_facts"] == []
    assert an.last_decision is not None
    assert c.get(f"/api/v1/reports/{rep['id']}").json()["id"] == rep["id"]
    assert [x["id"] for x in c.get("/api/v1/reports").json()] == [rep["id"]]


def test_low_confidence_decision_sets_status(tmp_path):
    h = ok_handler(stub_answer(confidence=0.2))
    c = make(tmp_path, ScriptedAnalyzer(), h)
    rep = c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"}).json()
    assert rep["status"] in {"needs_more_evidence", "needs_human_review"}


def test_analyzer_not_configured_is_503_and_nothing_saved(tmp_path):
    c = make(tmp_path, None, ok_handler())
    r = c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503 and "BEDROCK_MODEL_ID" in r.json()["detail"]
    assert c.get("/api/v1/reports").json() == []


def test_analyzer_unavailable_is_503_with_retry_hint(tmp_path):
    c = make(
        tmp_path,
        ScriptedAnalyzer(error=AnalysisUnavailable("throttled", retryable=True)),
        ok_handler(),
    )
    r = c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503 and r.headers.get("retry-after") == "10"
    assert c.get("/api/v1/reports").json() == []


def test_analysis_error_is_502(tmp_path):
    c = make(tmp_path, ScriptedAnalyzer(error=AnalysisError("bad")), ok_handler())
    assert c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"}).status_code == 502


def test_decider_unavailable_is_503_and_analyzer_not_called(tmp_path):
    an = ScriptedAnalyzer()
    c = make(tmp_path, an, None)  # no decider configured
    r = c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"})
    assert r.status_code == 503 and "Decider" in r.json()["detail"]
    assert an.calls == 0


def test_require_decision_false_gives_analysis_only(tmp_path):
    an = ScriptedAnalyzer()
    c = make(tmp_path, an, None)
    r = c.post(
        "/api/v1/investigations", json={"incident_id": "sim-alb-503", "require_decision": False}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "analysis_only" and r.json()["decision"] is None


def test_unknown_incident_404_and_live_mode_501(tmp_path, monkeypatch):
    c = make(tmp_path, ScriptedAnalyzer(), ok_handler())
    assert c.post("/api/v1/investigations", json={"incident_id": "nope"}).status_code == 404
    c.app.dependency_overrides[get_settings] = lambda: Settings(mode="live")
    assert c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"}).status_code == 501


@pytest.mark.parametrize("rid", ["nope", "../etc/passwd", "rpt_" + "0" * 32])
def test_unknown_or_invalid_report_id_is_404(tmp_path, rid):
    assert make(tmp_path).get(f"/api/v1/reports/{rid}").status_code == 404


def test_api_key_protects_investigations(tmp_path, monkeypatch):
    monkeypatch.setenv("INCIDENTPILOT_API_KEY", "secret")
    get_settings.cache_clear()
    c = make(tmp_path, ScriptedAnalyzer(), ok_handler())
    assert c.post("/api/v1/investigations", json={"incident_id": "sim-alb-503"}).status_code == 401
