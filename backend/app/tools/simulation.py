"""Simulation backend: serves the bundled sample incidents. Makes no AWS calls."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from app.config import Mode
from app.schemas import IncidentSummary, ToolOption
from app.simulation import catalog
from app.simulation.evidence import get_evidence
from app.state import IncidentState

from .base import RUNNABLE_TOOLS, DiagnosticsError, ToolRun
from .sim_details import TOOL_DETAILS


class SimulationBackend:
    mode = Mode.SIMULATION

    def list_incidents(self) -> tuple[list[IncidentSummary], str | None]:
        return catalog.list_scenarios(), None

    def get_incident(self, incident_id: str) -> tuple[IncidentSummary, IncidentState] | None:
        scenario, state = catalog.get_scenario(incident_id), get_evidence(incident_id)
        if scenario is None or state is None:
            return None
        return scenario, state

    def run_tool(self, tool: ToolOption, state: IncidentState) -> ToolRun:
        started = time.perf_counter()
        if tool not in RUNNABLE_TOOLS:
            raise DiagnosticsError(f"{tool.value} is not a runnable diagnostic tool.")
        findings = TOOL_DETAILS.get(state.incident_id, {}).get(tool)
        if not findings:
            raise DiagnosticsError(f"No simulation data for {state.incident_id}/{tool.value}.")
        return ToolRun(
            tool=tool,
            mode=Mode.SIMULATION,
            backend="simulation",
            findings=list(findings),
            api_calls=[],
            duration_ms=(time.perf_counter() - started) * 1000,
            executed_at=datetime.now(UTC),
        )
