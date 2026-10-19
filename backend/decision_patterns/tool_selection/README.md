# Tool Selection decision pattern (Strands Decider 2B)

A reusable recipe: let **Decider 2B** choose which tool an agent calls next, and act on the
choice only when the model is confident.

```
state (text) ──┐
typed question ─┼─► Decider 2B (choice) ─► option + probabilities + confidence
option set ────┘                                     │
                                                     ▼
                              confidence >= threshold ?
                       yes ─► invoke the selected tool
                       no  ─► collect more evidence, then ask again
                       still no ─► human review
```

## What Decider decides

One typed `choice` question over a fixed option set. For IncidentPilot:

> **Which diagnostic tool should the incident agent run next?**
> `investigate_load_balancer` · `investigate_ec2` · `investigate_database` ·
> `investigate_cloudwatch_logs` · `collect_more_evidence`

The model returns the chosen option, a probability per option, and a calibrated
`confidence`. We pass these through unmodified. We never recompute or invent them, and
the pattern never overrides the model's choice. It only decides what to *do* with it.

## Use it in your own agent

```bash
pip install strands-decider httpx
strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 9000
```

```python
from decision_patterns.tool_selection import HttpDeciderClient, ToolSelectionPattern

pattern = ToolSelectionPattern(
    question="Which tool should the agent call next?",
    options={  # {option_id: description}
        "search_orders": "The user asks about an existing order, delivery or refund.",
        "search_docs": "The user asks how a product or policy works.",
        "collect_more_evidence": "The request is too vague to pick a tool.",
    },
    client=HttpDeciderClient("http://localhost:9000"),
    confidence_threshold=0.6,
)

d = pattern.decide("Where is my package? It was due on Tuesday.")
(
    d.selected,
    d.confidence,
    d.latency_ms,
    d.action,
)  # action: invoke_tool | collect_more_evidence | human_review
```

See `example.py`. Copy `decision_patterns/tool_selection/` into your repo; it depends only
on `httpx`.

## Writing good options

Option **descriptions are part of the prompt** (they become the `criteria` of the
question). Describe the *evidence* that points to each option, not just its name.
Include an explicit "not enough information" option (`evidence_option`) so the model has
a legitimate way to say "don't pick yet".

## Failure behaviour (by design)

| Situation | Result |
|---|---|
| Server unreachable / timeout / unhealthy | `DeciderUnavailable`; the caller must surface it. No fallback decision |
| Non-200, non-JSON, wrong shape, choice not in options, confidence missing or outside [0,1] | `DeciderProtocolError` |
| Confidence below threshold | `collect_more_evidence` up to `max_evidence_rounds`, then `human_review` |
| Model picks the evidence option | honoured, also bounded by `max_evidence_rounds` |

## Choosing the threshold

The model card reports calibration measured on short classification tasks and warns that
the bands were not established on other data. Treat `0.60` as a starting point and
measure calibration on your own incidents before relying on it.

## Wire contract

`POST /v1/systemone` with
`{"state": str, "questions": {name: {"type": "choice", "instructions": str, "criteria": {option: description}}}}`.
Response: `answers[name] = {type, choice, probabilities, confidence}`, plus `model`,
`usage`, `latency_ms`. `tests/fixtures/strands_decider_schema.py` vendors the real schema
(Apache-2.0) so tests check requests against it.

## Wiring into a Strands agent

`ToolSelectionPattern.decide()` is synchronous and side-effect free, so it can be called
from a Strands `before_tool_call` intervention to gate or redirect a tool call (the
upstream `strands-decider` repo ships an `examples/strands/` intervention to follow).
IncidentPilot's own agent integration lands in Phase 3.

## Tests

`pytest backend/tests/decision_patterns` (gate policy and client validation, against test
doubles) and `pytest -m live_decider -s` (real model, skipped unless
`INCIDENTPILOT_DECIDER_URL` is reachable).
