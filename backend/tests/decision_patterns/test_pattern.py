"""Confidence-gate policy. `ScriptedClient` is a test double that returns scripted
answers so the gate can be exercised at exact thresholds. It stands in for nothing the
product ships."""

import pytest

from decision_patterns.tool_selection import (
    Action,
    ChoiceResult,
    DeciderUnavailable,
    ToolSelectionPattern,
)

OPTS = {"tool_a": "a", "tool_b": "b", "collect_more_evidence": "more"}


class ScriptedClient:
    def __init__(self, choice, confidence):
        self.choice, self.confidence, self.calls = choice, confidence, 0

    def health(self):
        return {"status": "ok"}

    def ask_choice(self, state, question, options, *, name="choice"):
        self.calls += 1
        probs = {k: 0.0 for k in options}
        probs[self.choice] = 1.0
        return ChoiceResult(self.choice, probs, self.confidence, "scripted", 1.0, 2.0)


def pattern(choice, confidence, **kw):
    return ToolSelectionPattern(
        question="Q?", options=OPTS, client=ScriptedClient(choice, confidence), **kw
    )


def test_confident_selection_invokes_tool():
    d = pattern("tool_a", 0.9).decide("s")
    assert (d.selected, d.action, d.meets_threshold) == ("tool_a", Action.INVOKE_TOOL, True)


def test_threshold_is_inclusive():
    assert pattern("tool_a", 0.60).decide("s").action is Action.INVOKE_TOOL
    assert pattern("tool_a", 0.5999).decide("s").action is Action.COLLECT_MORE_EVIDENCE


def test_low_confidence_gathers_evidence_then_escalates_to_a_human():
    p = pattern("tool_a", 0.3)
    first = p.decide("s", evidence_rounds=0)
    assert first.action is Action.COLLECT_MORE_EVIDENCE and not first.meets_threshold
    assert first.selected == "tool_a"  # the model's choice is never overridden
    second = p.decide("s", evidence_rounds=1)
    assert second.action is Action.HUMAN_REVIEW


def test_model_choosing_the_evidence_option_is_honoured_even_when_confident():
    d = pattern("collect_more_evidence", 0.95).decide("s")
    assert d.action is Action.COLLECT_MORE_EVIDENCE


def test_evidence_loop_is_bounded():
    d = pattern("collect_more_evidence", 0.95).decide("s", evidence_rounds=1)
    assert d.action is Action.HUMAN_REVIEW


def test_no_evidence_option_means_straight_to_human_review():
    p = ToolSelectionPattern(
        question="Q?",
        options={"x": "x", "y": "y"},
        client=ScriptedClient("x", 0.1),
        evidence_option=None,
    )
    assert p.decide("s").action is Action.HUMAN_REVIEW


def test_confidence_is_passed_through_exactly():
    assert pattern("tool_a", 0.7341).decide("s").confidence == 0.7341


def test_client_failure_propagates_and_no_decision_is_made():
    class Down:
        def ask_choice(self, *a, **k):
            raise DeciderUnavailable("down")

        def health(self):
            raise DeciderUnavailable("down")

    p = ToolSelectionPattern(question="Q?", options=OPTS, client=Down())
    with pytest.raises(DeciderUnavailable):
        p.decide("s")


@pytest.mark.parametrize(
    "kw",
    [
        {"options": {"only": "one"}},
        {"confidence_threshold": 1.2},
        {"confidence_threshold": -0.1},
        {"max_evidence_rounds": -1},
        {"evidence_option": "not_an_option"},
    ],
)
def test_invalid_configuration_is_rejected(kw):
    args = {"question": "Q?", "options": OPTS, "client": ScriptedClient("tool_a", 1.0)}
    args.update(kw)
    with pytest.raises(ValueError):
        ToolSelectionPattern(**args)
