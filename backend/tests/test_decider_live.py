"""LIVE integration test against a real `strands-decider serve` instance.

Skipped unless INCIDENTPILOT_DECIDER_URL points at a healthy server, so CI without the
model stays green. When it runs it checks the protocol and the invariants of a real
answer. It deliberately does NOT assert which tool the model picks.

    strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000
    INCIDENTPILOT_DECIDER_URL=http://localhost:9000 pytest -m live_decider -s
"""

import os

import pytest

from app.config import Settings
from app.incident_pattern import build_pattern
from app.schemas import ToolOption
from app.simulation.evidence import EVIDENCE, REFERENCE_LABELS
from app.state import render_state_text
from decision_patterns.tool_selection import DeciderUnavailable, HttpDeciderClient

URL = os.environ.get("INCIDENTPILOT_DECIDER_URL", "")


def _client():
    if not URL:
        pytest.skip("INCIDENTPILOT_DECIDER_URL not set")
    c = HttpDeciderClient(URL, timeout=60.0)
    try:
        c.health()
    except DeciderUnavailable as e:
        pytest.skip(f"Decider server not reachable: {e}")
    return c


pytestmark = pytest.mark.live_decider


@pytest.mark.parametrize("incident_id", sorted(EVIDENCE))
def test_real_model_answers_every_scenario(incident_id):
    pattern = build_pattern(Settings(), _client())
    d = pattern.decide(render_state_text(EVIDENCE[incident_id]))
    assert d.selected in {o.value for o in ToolOption}
    assert 0.0 <= d.confidence <= 1.0
    assert abs(sum(d.probabilities.values()) - 1.0) < 1e-2
    assert d.latency_ms is None or d.latency_ms > 0
    print(
        f"\n{incident_id}: {d.selected} conf={d.confidence:.3f} "
        f"latency={d.latency_ms}ms action={d.action.value} "
        f"(reference: {REFERENCE_LABELS[incident_id]})"
    )
