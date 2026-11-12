"""Run the Decider 2B vs Bedrock-only routing benchmark against REAL endpoints.

    strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000
    python scripts/benchmark.py --decider-url http://localhost:9000 \
        --bedrock-model-id <your enabled model or inference profile> --region us-east-1 \
        --repeat 10 [--price-in 3.0 --price-out 15.0] [--decider-hardware "RTX 3090"]

Prices are USD per million tokens and are optional; without them no cost is shown.
Writes benchmark/results/<UTC time>.{json,md}. Exits 2 without writing anything if an
endpoint you asked for cannot be reached. There is no simulated mode.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.incident_pattern import build_pattern  # noqa: E402
from app.simulation.evidence import EVIDENCE, REFERENCE_LABELS  # noqa: E402
from app.state import render_state_text  # noqa: E402
from benchmark.harness import (  # noqa: E402
    BedrockArm,
    DeciderArm,
    render_markdown,
    run_benchmark,
)
from decision_patterns.tool_selection import DeciderError, HttpDeciderClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decider-url")
    ap.add_argument("--bedrock-model-id")
    ap.add_argument("--region", default=Settings().aws_region)
    ap.add_argument("--repeat", type=int, default=10)
    ap.add_argument("--price-in", type=float, help="USD per 1M input tokens")
    ap.add_argument("--price-out", type=float, help="USD per 1M output tokens")
    ap.add_argument("--decider-hardware", default="not stated")
    ap.add_argument("--out", default=str(ROOT.parent / "benchmark" / "results"))
    a = ap.parse_args()
    if not a.decider_url and not a.bedrock_model_id:
        print("Give --decider-url and/or --bedrock-model-id.", file=sys.stderr)
        return 2

    arms = []
    meta: dict[str, object] = {
        "date_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "client_host": platform.platform(),
    }
    if a.decider_url:
        client = HttpDeciderClient(a.decider_url, timeout=120.0)
        try:
            info = client.health()
        except DeciderError as e:
            print(f"Decider unavailable: {e}", file=sys.stderr)
            return 2
        meta.update(
            decider_url=a.decider_url,
            decider_model=info.get("model"),
            decider_device=info.get("device"),
            decider_hardware=a.decider_hardware,
        )
        arms.append(DeciderArm(build_pattern(Settings(), client)))
    if a.bedrock_model_id:
        meta.update(bedrock_model_id=a.bedrock_model_id, bedrock_region=a.region)
        arms.append(BedrockArm(a.bedrock_model_id, a.region))

    states = {k: render_state_text(v) for k, v in EVIDENCE.items()}
    result = run_benchmark(
        arms,
        states,
        REFERENCE_LABELS,
        repeat=a.repeat,
        meta=meta,
        price_in_per_mtok=a.price_in,
        price_out_per_mtok=a.price_out,
    )
    if all(s["calls"] == s["errors"] for s in result.summaries.values()):
        print("Every call failed; nothing written.", file=sys.stderr)
        for s in result.samples[:3]:
            print(" ", s.arm, s.error, file=sys.stderr)
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    (out / f"{stamp}.json").write_text(json.dumps(result.to_dict(), indent=2))
    (out / f"{stamp}.md").write_text(render_markdown(result))
    print(render_markdown(result))
    print(f"written to {out}/{stamp}.(json|md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
