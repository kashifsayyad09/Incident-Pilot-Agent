# API Contract (v0.1.0)

Base URL: `http://localhost:8000`. Machine-readable schema: `shared/openapi.json`
(regenerate with `python backend/scripts/export_openapi.py`; CI fails if stale).
TypeScript mirror: `frontend/src/lib/types.ts`.

Auth: if `INCIDENTPILOT_API_KEY` is set, all `/api/v1/*` endpoints require header
`X-API-Key`. `/health` is always open.

| Method | Path | Purpose | Phase 1 behavior |
|---|---|---|---|
| GET | `/health` | Liveness, mode, per-component availability | Real |
| GET | `/api/v1/incidents` | List incidents | Simulation catalogue (5 scenarios, metadata only). Live mode returns empty list + notice |
| GET | `/api/v1/incidents/{id}` | Incident detail | Real for simulation; 404 unknown; 501 in live mode |
| GET | `/api/v1/decision/status` | Is Decider 2B usable, option set, threshold | Always `available: false` until Phase 2 |
| POST | `/api/v1/decision/run` | Run Decider 2B tool selection `{incident_id}` | Returns 503 while unavailable. Never returns a fabricated decision |

## Decision contract

`DecisionResult` fields `confidence` and `latency_ms` are nullable: null means the
model did not produce / we did not measure it, never zero. `outcome` is one of
`tool_invoked`, `escalated_low_confidence`, `unavailable`.

Typed options (`ToolOption`): `investigate_load_balancer`, `investigate_ec2`,
`investigate_database`, `investigate_cloudwatch_logs`, `collect_more_evidence`.

## Planned (not yet implemented)

- Phase 3: `POST /api/v1/investigations` (agent run), `GET /api/v1/reports`
- Phase 4: live evidence and tool-output payloads
