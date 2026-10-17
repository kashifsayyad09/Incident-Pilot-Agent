"""Runtime configuration, loaded from environment variables (prefix INCIDENTPILOT_)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(StrEnum):
    """Data source for incident evidence. Always surfaced to the UI."""

    SIMULATION = "simulation"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INCIDENTPILOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mode: Mode = Mode.SIMULATION
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    api_key: str = ""
    decider_confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    bedrock_model_id: str = ""

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard(cls, v: str) -> str:
        if any(o.strip() == "*" for o in v.split(",")):
            raise ValueError("Wildcard CORS origin is not allowed; list explicit origins.")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
