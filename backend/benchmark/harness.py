"""Decider 2B vs Bedrock-only routing benchmark: measurement code.

Both arms answer the SAME question over the SAME five options and the SAME incident state:
  - decider: a real Strands Decider 2B server (System One API)
  - bedrock: a real Amazon Bedrock model through the Strands Agents SDK, structured output
Nothing here produces numbers by itself: every figure comes from a call an arm made. The
CLI (scripts/benchmark.py) refuses to run without real endpoints. Tests use fake arms and
never write result files.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from app.incident_pattern import OPTION_DESCRIPTIONS, QUESTION


@dataclass
class Sample:
    arm: str
    scenario: str
    run: int
    choice: str | None
    wall_ms: float  # measured by this harness around the call
    server_ms: float | None = None  # Decider server-reported inference time
    confidence: float | None = None  # Decider only; passed through unmodified
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


class Arm(Protocol):
    name: str

    def call(self, scenario: str, state_text: str) -> dict[str, Any]:
        """Return keys: choice, and optionally server_ms, confidence, input_tokens,
        output_tokens. Raise on failure; the harness records the error."""


def run_arm(arm: Arm, states: dict[str, str], repeat: int) -> list[Sample]:
    out: list[Sample] = []
    for scenario in sorted(states):
        for i in range(repeat):
            t0 = time.perf_counter()
            try:
                r = arm.call(scenario, states[scenario])
                err = None
            except Exception as e:  # noqa: BLE001 - recorded, never hidden
                r, err = {}, f"{type(e).__name__}: {str(e)[:200]}"
            out.append(
                Sample(
                    arm=arm.name,
                    scenario=scenario,
                    run=i,
                    choice=r.get("choice"),
                    wall_ms=(time.perf_counter() - t0) * 1000,
                    server_ms=r.get("server_ms"),
                    confidence=r.get("confidence"),
                    input_tokens=r.get("input_tokens"),
                    output_tokens=r.get("output_tokens"),
                    error=err,
                )
            )
    return out


def percentile(values: list[float], p: float) -> float | None:
    """Linear-interpolated percentile (p in 0..100). None for no data."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(samples: list[Sample], reference: dict[str, str]) -> dict[str, Any]:
    ok = [s for s in samples if s.error is None]
    wall = [s.wall_ms for s in ok]
    srv = [s.server_ms for s in ok if s.server_ms is not None]
    tin = [s.input_tokens for s in ok if s.input_tokens is not None]
    tout = [s.output_tokens for s in ok if s.output_tokens is not None]
    agree = sum(1 for s in ok if reference.get(s.scenario) == s.choice)
    return {
        "calls": len(samples),
        "errors": len(samples) - len(ok),
        "agreement_with_reference": {"matches": agree, "of": len(ok)},
        "wall_ms": {
            "p50": percentile(wall, 50),
            "p95": percentile(wall, 95),
            "min": min(wall, default=None),
            "max": max(wall, default=None),
        },
        "server_ms_p50": percentile([float(x) for x in srv], 50),
        "mean_input_tokens": statistics.fmean(tin) if tin else None,
        "mean_output_tokens": statistics.fmean(tout) if tout else None,
    }


def per_call_cost_usd(
    summary: dict[str, Any], price_in_per_mtok: float | None, price_out_per_mtok: float | None
) -> float | None:
    """Only when the caller supplied both prices AND token counts were measured."""
    if price_in_per_mtok is None or price_out_per_mtok is None:
        return None
    i, o = summary["mean_input_tokens"], summary["mean_output_tokens"]
    if i is None or o is None:
        return None
    return (i * price_in_per_mtok + o * price_out_per_mtok) / 1_000_000


@dataclass
class BenchmarkResult:
    meta: dict[str, Any]
    summaries: dict[str, dict[str, Any]]
    samples: list[Sample] = field(default_factory=list)
    comparison: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["samples"] = [asdict(s) for s in self.samples]
        return d


def run_benchmark(
    arms: list[Arm],
    states: dict[str, str],
    reference: dict[str, str],
    *,
    repeat: int,
    meta: dict[str, Any],
    price_in_per_mtok: float | None = None,
    price_out_per_mtok: float | None = None,
) -> BenchmarkResult:
    samples: list[Sample] = []
    summaries: dict[str, dict[str, Any]] = {}
    for arm in arms:
        got = run_arm(arm, states, repeat)
        samples += got
        summaries[arm.name] = summarize(got, reference)
        summaries[arm.name]["cost_usd_per_call"] = per_call_cost_usd(
            summaries[arm.name], price_in_per_mtok, price_out_per_mtok
        )
    comparison: dict[str, Any] = {}
    d, b = summaries.get("decider"), summaries.get("bedrock")
    if d and b and d["wall_ms"]["p50"] and b["wall_ms"]["p50"]:
        comparison["bedrock_p50_over_decider_p50"] = b["wall_ms"]["p50"] / d["wall_ms"]["p50"]
    return BenchmarkResult(
        meta={**meta, "repeat": repeat, "scenarios": sorted(states)},
        summaries=summaries,
        samples=samples,
        comparison=comparison,
    )


# ---- arms -------------------------------------------------------------------------------------


class DeciderArm:
    name = "decider"

    def __init__(self, pattern: Any) -> None:
        self._pattern = pattern

    def call(self, scenario: str, state_text: str) -> dict[str, Any]:
        d = self._pattern.decide(state_text)
        return {
            "choice": str(d.selected),
            "server_ms": d.latency_ms,
            "confidence": d.confidence,
        }


class RoutingChoice(BaseModel):
    choice: Literal[
        "investigate_load_balancer",
        "investigate_ec2",
        "investigate_database",
        "investigate_cloudwatch_logs",
        "collect_more_evidence",
    ]
    reason: str = Field(description="One sentence.")


def routing_prompt(state_text: str) -> str:
    opts = "\n".join(f"- {k}: {v}" for k, v in OPTION_DESCRIPTIONS.items())
    return (
        f"{QUESTION}\n\nOptions:\n{opts}\n\nIncident state:\n<state>\n{state_text}\n</state>\n\n"
        "Choose exactly one option."
    )


class BedrockArm:
    """Bedrock-only baseline: the same routing question answered by a general model."""

    name = "bedrock"

    def __init__(
        self,
        model_id: str,
        region: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        model_factory: Any | None = None,
    ) -> None:
        self.model_id, self.region = model_id, region
        self._temperature, self._max_tokens = temperature, max_tokens
        self._factory = model_factory

    def _model(self) -> Any:
        if self._factory:
            return self._factory()
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=self.model_id,
            region_name=self.region,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

    def call(self, scenario: str, state_text: str) -> dict[str, Any]:
        from strands import Agent

        agent = Agent(
            model=self._model(),
            tools=[],
            system_prompt="You route incidents to the next diagnostic. Answer only the question.",
            callback_handler=None,
        )
        res = agent(routing_prompt(state_text), structured_output_model=RoutingChoice)
        usage = getattr(res.metrics, "accumulated_usage", None) or {}
        return {
            "choice": res.structured_output.choice,
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
        }


# ---- report -----------------------------------------------------------------------------------

CAVEATS = (
    "Agreement is measured against reference labels the authors wrote for five hand-written "
    "simulation scenarios. It is a smoke check, not an accuracy benchmark.",
    "Latency is wall-clock time measured from the machine that ran this script, including "
    "network. Decider 2B was served from the host named in the metadata; Bedrock from the "
    "stated region. Results do not transfer to other hardware, regions, or load.",
    "The Bedrock arm answers only the routing question. It is not the production incident "
    "analysis call.",
    "Cost is reported only when per-token prices were supplied, and covers Bedrock tokens "
    "only. Decider 2B is self-hosted: its infrastructure cost is not included.",
)


def _f(v: float | None, spec: str = ".1f") -> str:
    return "not measured" if v is None else format(v, spec)


def render_markdown(r: BenchmarkResult) -> str:
    L = ["# Decider 2B vs Bedrock-only routing", ""]
    L += [f"- {k}: {v}" for k, v in r.meta.items()]
    L += ["", "| Arm | Calls | Errors | Agree | p50 ms | p95 ms | Mean in/out tokens | USD/call |"]
    L += ["|---|---|---|---|---|---|---|---|"]
    for name, s in r.summaries.items():
        a = s["agreement_with_reference"]
        L.append(
            f"| {name} | {s['calls']} | {s['errors']} | {a['matches']}/{a['of']} | "
            f"{_f(s['wall_ms']['p50'])} | {_f(s['wall_ms']['p95'])} | "
            f"{_f(s['mean_input_tokens'], '.0f')} / {_f(s['mean_output_tokens'], '.0f')} | "
            f"{_f(s['cost_usd_per_call'], '.6f')} |"
        )
    if r.comparison:
        L += [
            "",
            f"Bedrock p50 / Decider p50 = {r.comparison['bedrock_p50_over_decider_p50']:.1f}x",
        ]
    L += ["", "## Read this first", ""] + [f"- {c}" for c in CAVEATS]
    return "\n".join(L) + "\n"
