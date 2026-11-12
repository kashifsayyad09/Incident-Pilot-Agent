"""Runtime configuration, loaded from environment variables (prefix INCIDENTPILOT_)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
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
    aws_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices(
            "INCIDENTPILOT_AWS_REGION", "AWS_REGION", "AWS_DEFAULT_REGION"
        ),
    )
    bedrock_temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    bedrock_max_tokens: int = Field(default=4096, ge=256, le=32000)
    bedrock_timeout_s: float = Field(default=60.0, gt=0.0, le=300.0)
    data_dir: str = "data"  # report store; git-ignored
    decider_url: str = ""  # base URL of `strands-decider serve`; empty = not configured
    decider_timeout_s: float = Field(default=10.0, gt=0.0, le=120.0)
    # Live mode targets (read-only). Set at least one; unset parts are reported "not measured".
    live_target_group_arn: str = ""  # ALB target group: health, ALB metrics, EC2 instances
    live_db_instance_id: str = ""  # RDS DB instance identifier
    live_log_group: str = ""  # CloudWatch Logs group searched for errors
    live_alarm_name_prefix: str = ""  # only consider alarms whose name starts with this
    # Bedrock calls cost money: cap full investigations per minute (0 = unlimited).
    # In-memory, per process.
    max_investigations_per_minute: int = Field(default=10, ge=0, le=1000)
    live_window_minutes: int = Field(default=30, ge=5, le=180)

    @property
    def live_configured(self) -> bool:
        return bool(self.live_target_group_arn or self.live_db_instance_id or self.live_log_group)

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
