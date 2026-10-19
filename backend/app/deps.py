from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings
from decision_patterns.tool_selection import DeciderClient, HttpDeciderClient


def get_decider_client(settings: Settings = Depends(get_settings)) -> DeciderClient | None:
    """None means Decider is not configured. Tests override this dependency."""
    if not settings.decider_url:
        return None
    return HttpDeciderClient(settings.decider_url, timeout=settings.decider_timeout_s)


def get_analyzer(settings: Settings = Depends(get_settings)):
    """None means Bedrock analysis is not configured. Tests override this dependency."""
    if not settings.bedrock_model_id:
        return None
    from app.agent.analyzer import StrandsBedrockAnalyzer

    return StrandsBedrockAnalyzer(
        settings.bedrock_model_id,
        settings.aws_region,
        temperature=settings.bedrock_temperature,
        max_tokens=settings.bedrock_max_tokens,
        timeout_s=settings.bedrock_timeout_s,
    )


def get_report_store(settings: Settings = Depends(get_settings)):
    from app.agent.store import ReportStore

    return ReportStore(settings.data_dir)
