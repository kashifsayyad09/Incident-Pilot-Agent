"""Reusable Tool Selection decision pattern.

    state (text) + typed question + option set  ->  Decider 2B  ->  Decision

The model picks ONE option and reports a calibrated confidence. This module adds only
the *policy around* that answer: a confidence gate and what to do when it is not met.
It never overrides the model's choice and never invents a confidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .client import DeciderClient


class Action(StrEnum):
    INVOKE_TOOL = "invoke_tool"  # confident: run the selected tool
    COLLECT_MORE_EVIDENCE = "collect_more_evidence"  # unsure (or model asked for it)
    HUMAN_REVIEW = "human_review"  # still unsure after the allowed evidence rounds


@dataclass(frozen=True)
class Decision:
    selected: str
    confidence: float  # exactly as returned by the model
    probabilities: dict[str, float]
    model: str | None
    latency_ms: float | None
    roundtrip_ms: float
    threshold: float
    meets_threshold: bool
    action: Action
    reason: str


@dataclass
class ToolSelectionPattern:
    """Configure once, call `decide(state)` many times.

    question:            the typed question shown to the model
    options:             {option_id: description}. Descriptions steer the model, so write
                         them like a rubric (what evidence points to this option).
    confidence_threshold: below this, the selection is not acted on automatically.
    evidence_option:     option id meaning "gather more evidence first" (or None).
    max_evidence_rounds: how many times to loop back for evidence before a human decides.
    """

    question: str
    options: Mapping[str, str]
    client: DeciderClient
    confidence_threshold: float = 0.60
    evidence_option: str | None = "collect_more_evidence"
    max_evidence_rounds: int = 1
    name: str = "tool"
    _ids: tuple[str, ...] = field(init=False, repr=False, default=())

    def __post_init__(self) -> None:
        if len(self.options) < 2:
            raise ValueError("A choice question needs at least 2 options.")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be within [0, 1].")
        if self.max_evidence_rounds < 0:
            raise ValueError("max_evidence_rounds must be >= 0.")
        if self.evidence_option is not None and self.evidence_option not in self.options:
            raise ValueError("evidence_option must be one of the options.")
        self._ids = tuple(self.options)

    def decide(self, state: str, *, evidence_rounds: int = 0) -> Decision:
        """Ask the model, then apply the confidence gate. Raises DeciderError on failure."""
        ans = self.client.ask_choice(state, self.question, self.options, name=self.name)
        meets = ans.confidence >= self.confidence_threshold
        can_loop = self.evidence_option is not None and evidence_rounds < self.max_evidence_rounds

        if ans.choice == self.evidence_option:
            action = Action.COLLECT_MORE_EVIDENCE if can_loop else Action.HUMAN_REVIEW
            reason = (
                "The model selected the evidence-gathering option."
                if can_loop
                else "The model asked for more evidence but the allowed rounds are used up."
            )
        elif meets:
            action = Action.INVOKE_TOOL
            reason = (
                f"Confidence {ans.confidence:.3f} meets the "
                f"{self.confidence_threshold:.2f} threshold."
            )
        elif can_loop:
            action = Action.COLLECT_MORE_EVIDENCE
            reason = (
                f"Confidence {ans.confidence:.3f} is below the {self.confidence_threshold:.2f} "
                "threshold; gather more evidence and ask again."
            )
        else:
            action = Action.HUMAN_REVIEW
            reason = (
                f"Confidence {ans.confidence:.3f} is below the {self.confidence_threshold:.2f} "
                "threshold and no evidence rounds remain."
            )

        return Decision(
            selected=ans.choice,
            confidence=ans.confidence,
            probabilities=ans.probabilities,
            model=ans.model,
            latency_ms=ans.latency_ms,
            roundtrip_ms=ans.roundtrip_ms,
            threshold=self.confidence_threshold,
            meets_threshold=meets,
            action=action,
            reason=reason,
        )
