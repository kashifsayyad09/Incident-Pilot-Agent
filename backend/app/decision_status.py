"""Reports whether the Decider 2B adapter is usable.

Phase 1: the adapter does not exist yet, so this always reports unavailable.
Phase 2 replaces this with a real probe of the model interface. The UI relies
on this to show an explicit "unavailable" state instead of any fallback.
"""

from __future__ import annotations

from app.config import Settings
from app.schemas import DecisionStatus, ToolOption


def current_decision_status(settings: Settings) -> DecisionStatus:
    return DecisionStatus(
        available=False,
        adapter=None,
        reason="Decider 2B adapter not implemented yet (Phase 2).",
        confidence_threshold=settings.decider_confidence_threshold,
        options=list(ToolOption),
    )
