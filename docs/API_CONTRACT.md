# API Contract (v0.1.0)

Base URL: same origin as the UI (`http://localhost:8080` via nginx, or `http://localhost:3000` in dev via Next.js rewrites); the backend itself listens on `:8000`. Machine-readable schema: `shared/openapi.json`
(regenerate with `python backend/scripts/export_openapi.py`; CI fails if stale).
TypeScript mirror: `frontend/src/lib/types.ts`.

Auth: if `INCIDENTPILOT_API_KEY` is set, all `/api/v1/*` endpoints require header
`X-API-Key`. `/health` is always open.

| Method | Path | Purpose | Phase 1 behavior |
|---|---|---|---|
| GET | `/health` | Liveness, mode, per-component availability | Real |
| GET | `/api/v1/incidents` | List incidents | Simulation catalogue (5 scenarios, metadata only). Live mode returns empty list + notice |
| GET | `/api/v1/incidents/{id}` | Incident detail | Real for simulation; 404 unknown; 501 in live mode |
| GET | `/api/v1/decision/status` | Probes the Decider server; option set, threshold | `available: true` only if `INCIDENTPILOT_DECIDER_URL` answers `/health` |
| POST | `/api/v1/decision/run` | Real Decider 2B tool selection `{incident_id}` | 200 with the model's own numbers; 503 if unavailable; 502 if the server answers invalidly; 404 unknown; 501 live mode. Never a fabricated decision |

## Decision contract

`DecisionResult` carries the whole trace: `input_state` (structured), `state_text` (the
exact text the model read), `question`, `options`, `selected`, `confidence` and
`probabilities` (the model's own values, unmodified), `model`, `latency_ms`
(server-reported; null if absent), `roundtrip_ms` (measured by the API),
`confidence_threshold`, `meets_threshold`, `outcome`, `reason`.

`outcome`: `tool_selected` (confident), `evidence_requested` (below threshold or the model
chose `collect_more_evidence`), `human_review` (evidence rounds exhausted).
`tool_invoked` is always `null` until diagnostic tools exist (Phase 4).

Typed options (`ToolOption`): `investigate_load_balancer`, `investigate_ec2`,
`investigate_database`, `investigate_cloudwatch_logs`, `collect_more_evidence`.

## Investigations and reports (Phase 3)

| Method | Path | Behavior |
|---|---|---|
| POST | `/api/v1/investigations` | `{incident_id, require_decision=true}`. Runs Decider 2B, then Amazon Bedrock analysis via the Strands Agents SDK, grounds the output, stores and returns an `IncidentReport`. 503 if Decider (when required) or Bedrock is unavailable/unconfigured (`Retry-After` on transient errors); 502 if Bedrock's answer is unusable; 404 unknown incident; 501 live mode. Nothing is stored on failure and nothing is mocked |
| GET | `/api/v1/reports` | Stored reports, newest first |
| GET | `/api/v1/reports/{id}` | One report; 404 for unknown or malformed ids |

`IncidentReport`: `id`, `created_at`, `mode`, `status` (`complete`, `needs_more_evidence`,
`needs_human_review`, `analysis_only`), `incident`, `decision` (the full `DecisionResult`, or
null for `analysis_only`), `evidence` (numbered items E1..En the model may cite),
`analysis`, `grounding`, `generation` (`ai_generated`, model id, region, latency),
`advisory_notice`.

`analysis` keeps **confirmed_facts** (each cites evidence ids and is checked against them)
separate from **hypotheses** (with `what_would_confirm`), `probable_root_causes`,
`recommended_actions` (`read_only_check` or `human_executed_change`, with risk),
`impact_assessment`, `evidence_gaps`. `grounding` reports facts kept/demoted and unknown
evidence ids removed. Model output is untrusted: a fact without valid evidence, or stating
a number absent from the cited evidence, is demoted to a hypothesis.

In Phase 3 the evidence bundle comes from the simulation data. The Decider's selected tool
is recorded, but real tool execution arrives in Phase 4.

## Planned (not yet implemented)

- Phase 4: live evidence and tool-output payloads
