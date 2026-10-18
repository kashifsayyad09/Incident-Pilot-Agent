"""Run the five sample incidents through a REAL Decider 2B server and report the results.

    strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000
    python scripts/eval_decider.py http://localhost:9000 [--repeat 5]

Prints, per scenario: the model's choice, its confidence, server-reported latency, and
whether it agrees with the human reference label (REFERENCE_LABELS). Agreement on five
hand-written scenarios is a smoke check, NOT an accuracy benchmark. Nothing is printed
that the server did not return. Exits non-zero if the server cannot be reached.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.incident_pattern import build_pattern  # noqa: E402
from app.simulation.evidence import EVIDENCE, REFERENCE_LABELS  # noqa: E402
from app.state import render_state_text  # noqa: E402
from decision_patterns.tool_selection import DeciderError, HttpDeciderClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--repeat", type=int, default=1, help="calls per scenario (latency stats)")
    args = ap.parse_args()

    client = HttpDeciderClient(args.url, timeout=120.0)
    try:
        info = client.health()
    except DeciderError as e:
        print(f"Decider unavailable: {e}", file=sys.stderr)
        return 2
    print(f"server: {args.url}  model: {info.get('model')}  device: {info.get('device')}")
    pattern = build_pattern(Settings(), client)

    agree = 0
    lat: list[float] = []
    rtt: list[float] = []
    for iid in sorted(EVIDENCE):
        text = render_state_text(EVIDENCE[iid])
        for i in range(args.repeat):
            d = pattern.decide(text)
            if d.latency_ms is not None:
                lat.append(d.latency_ms)
            rtt.append(d.roundtrip_ms)
            if i == 0:
                ok = d.selected == REFERENCE_LABELS[iid]
                agree += ok
                print(
                    f"{iid:26s} -> {d.selected:28s} conf={d.confidence:.3f} "
                    f"action={d.action.value:22s} ref={'match' if ok else 'DIFFERS'}"
                )
    print(f"\nagreement with reference labels: {agree}/{len(EVIDENCE)} (smoke check only)")
    if lat:
        print(
            f"server latency ms: median={statistics.median(lat):.1f} "
            f"max={max(lat):.1f} (n={len(lat)})"
        )
    print(
        f"round-trip ms:     median={statistics.median(rtt):.1f} max={max(rtt):.1f} (n={len(rtt)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
