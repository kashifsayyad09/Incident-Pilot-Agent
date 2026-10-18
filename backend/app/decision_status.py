"""Reports whether Decider 2B is usable right now, by probing the real server."""

from __future__ import annotations

from app.config import Settings
from app.schemas import DecisionStatus, ToolOption
from decision_patterns.tool_selection import DeciderClient, DeciderError

NOT_CONFIGURED = (
    "INCIDENTPILOT_DECIDER_URL is not set. Start the model with "
    "`strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000` "
    "and set INCIDENTPILOT_DECIDER_URL=http://localhost:9000."
)


def current_decision_status(settings: Settings, client: DeciderClient | None) -> DecisionStatus:
    base = dict(
        confidence_threshold=settings.decider_confidence_threshold, options=list(ToolOption)
    )
    if client is None:
        return DecisionStatus(available=False, adapter=None, reason=NOT_CONFIGURED, **base)
    try:
        info = client.health()
    except DeciderError as e:
        return DecisionStatus(available=False, adapter=settings.decider_url, reason=str(e), **base)
    model = info.get("model") or "unknown model"
    return DecisionStatus(
        available=True, adapter=f"{settings.decider_url} ({model})", reason=None, **base
    )
