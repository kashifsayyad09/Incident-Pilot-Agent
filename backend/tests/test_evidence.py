from app.schemas import ToolOption
from app.simulation import catalog
from app.simulation.evidence import EVIDENCE, REFERENCE_LABELS
from app.state import AlbState, IncidentState, render_state_text


def test_every_catalogue_scenario_has_evidence_and_a_reference_label():
    ids = {s.id for s in catalog.list_scenarios()}
    assert ids == set(EVIDENCE) == set(REFERENCE_LABELS)
    valid = {o.value for o in ToolOption}
    assert set(REFERENCE_LABELS.values()) <= valid


def test_scenarios_cover_all_five_options_as_the_reference_choice():
    assert set(REFERENCE_LABELS.values()) == {o.value for o in ToolOption}


def test_unmeasured_values_render_as_not_measured_never_zero():
    s = IncidentState(incident_id="x", alb=AlbState(http_5xx_count_5m=None, healthy_targets=2))
    text = render_state_text(s)
    assert "5xx count (5m) not measured" in text
    assert "healthy targets 2 of not measured" in text
    assert "EC2: no data." in text
    assert "memory" not in text  # no EC2 block, so no invented memory number


def test_rendering_is_deterministic_and_contains_the_facts():
    text = render_state_text(EVIDENCE["sim-rds-connections"])
    assert text == render_state_text(EVIDENCE["sim-rds-connections"])
    assert "connections 187 of max 200" in text
    assert "rds-connections-high is ALARM" in text
    assert "remaining connection slots" in text


def test_ec2_memory_is_not_measured_in_samples():
    assert "memory not measured" in render_state_text(EVIDENCE["sim-ec2-cpu"])
