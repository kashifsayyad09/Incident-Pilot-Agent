from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings
from decision_patterns.tool_selection import DeciderClient, HttpDeciderClient


def get_decider_client(settings: Settings = Depends(get_settings)) -> DeciderClient | None:
    """None means Decider is not configured. Tests override this dependency."""
    if not settings.decider_url:
        return None
    return HttpDeciderClient(settings.decider_url, timeout=settings.decider_timeout_s)
