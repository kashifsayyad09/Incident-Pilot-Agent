from app.agent.evidence import bundle_from_state
from app.agent.grounding import ground
from app.agent.report import Action, Fact, Hypothesis, IncidentAnalysis, RootCause
from app.config import Mode
from app.simulation.evidence import get_evidence


def bundle(incident="sim-alb-503"):
    return bundle_from_state(get_evidence(incident), Mode.SIMULATION)


def analysis(**kw):
    base = dict(
        summary="s",
        confirmed_facts=[],
        hypotheses=[],
        probable_root_causes=[],
        recommended_actions=[],
        impact_assessment="Not determinable from the available evidence.",
        evidence_gaps=[],
    )
    base.update(kw)
    return IncidentAnalysis(**base)


def test_bundle_ids_are_unique_stable_and_sequential():
    b = bundle()
    ids = [i.id for i in b.items]
    assert ids == [f"E{n}" for n in range(1, len(ids) + 1)]
    assert bundle().model_dump() == b.model_dump()
    assert b.mode is Mode.SIMULATION


def test_bundle_marks_unmeasured_values_and_invents_nothing():
    for sid in ("sim-alb-503", "sim-ec2-cpu", "sim-rds-connections", "sim-conflicting-signals"):
        text = " ".join(i.text for i in bundle(sid).items)
        state = get_evidence(sid)
        if state.alb is None or state.ec2 is None or state.rds is None:
            assert "memory" not in text.lower() or "not measured" in text.lower()


def test_fact_with_valid_id_and_matching_number_is_kept():
    b = bundle()
    item = b.items[0]
    nums = [t for t in item.text.replace(";", " ").replace(",", " ").split() if t[0].isdigit()]
    assert nums, "fixture evidence should contain a number"
    n = nums[0].rstrip("%s.")
    a, rep = ground(
        analysis(confirmed_facts=[Fact(statement=f"Value {n}", evidence_ids=[item.id])]), b
    )
    assert rep.facts_kept == 1 and a.confirmed_facts


def test_fact_with_unknown_id_is_demoted_to_hypothesis():
    a, rep = ground(
        analysis(confirmed_facts=[Fact(statement="Something", evidence_ids=["E999"])]), bundle()
    )
    assert not a.confirmed_facts
    assert rep.facts_demoted == 1 and rep.evidence_ids_removed == 1
    assert any(h.statement == "Something" for h in a.hypotheses)
    assert rep.warnings


def test_fact_with_number_not_in_evidence_is_demoted():
    b = bundle()
    a, rep = ground(
        analysis(confirmed_facts=[Fact(statement="CPU hit 424242 percent", evidence_ids=["E1"])]), b
    )
    assert rep.facts_demoted == 1 and not a.confirmed_facts


def test_number_comparison_is_numeric_not_textual():
    from app.agent.evidence import EvidenceBundle, EvidenceItem

    b = EvidenceBundle(
        incident_id="x",
        mode=Mode.SIMULATION,
        items=[EvidenceItem(id="E1", source="alb", text="CPU 96.0% over 5 min")],
    )
    a, rep = ground(
        analysis(confirmed_facts=[Fact(statement="CPU was 96", evidence_ids=["E1"])]), b
    )
    assert rep.facts_kept == 1


def test_unsupported_confirmed_root_cause_is_downgraded():
    a, rep = ground(
        analysis(
            probable_root_causes=[
                RootCause(description="Bad deploy", basis="confirmed", evidence_ids=["E77"])
            ]
        ),
        bundle(),
    )
    assert a.probable_root_causes[0].basis == "hypothesis"
    assert rep.root_causes_demoted == 1


def test_unknown_ids_removed_from_hypotheses_and_actions():
    a, rep = ground(
        analysis(
            hypotheses=[
                Hypothesis(
                    statement="h",
                    evidence_ids=["E1", "E50"],
                    what_would_confirm="c",
                    plausibility="leading",
                )
            ],
            recommended_actions=[
                Action(
                    description="d",
                    kind="read_only_check",
                    risk="low",
                    rationale="r",
                    evidence_ids=["E50"],
                )
            ],
        ),
        bundle(),
    )
    assert a.hypotheses[0].evidence_ids == ["E1"]
    assert a.recommended_actions[0].evidence_ids == []
    assert rep.evidence_ids_removed == 2
