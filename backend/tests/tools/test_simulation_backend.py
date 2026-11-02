import pytest

from app.schemas import ToolOption as T
from app.simulation.catalog import SCENARIOS
from app.tools.base import RUNNABLE_TOOLS, DiagnosticsError
from app.tools.simulation import SimulationBackend

B = SimulationBackend()


def test_lists_all_scenarios_and_unknown_is_none():
    items, notice = B.list_incidents()
    assert len(items) == 5 and notice is None
    assert B.get_incident("nope") is None


@pytest.mark.parametrize("scenario", [s.id for s in SCENARIOS])
@pytest.mark.parametrize("tool", RUNNABLE_TOOLS)
def test_every_scenario_has_output_for_every_runnable_tool(scenario, tool):
    _, state = B.get_incident(scenario)
    run = B.run_tool(tool, state)
    assert run.findings and run.backend == "simulation" and run.mode.value == "simulation"
    assert run.api_calls == []  # simulation makes no AWS calls


def test_collect_more_evidence_is_not_runnable():
    _, state = B.get_incident("sim-alb-503")
    with pytest.raises(DiagnosticsError):
        B.run_tool(T.COLLECT_MORE_EVIDENCE, state)
