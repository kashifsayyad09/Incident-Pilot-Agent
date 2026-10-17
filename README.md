# IncidentPilot AI

> From Cloud Chaos to Clarity.

Read-only AWS incident investigation agent for the **AWS Strands Decider Agent
Hackathon** (category: Tool Selection, `#strands-decider-2b #tool-selection`).

**Pipeline:** Incident → Strands Decider 2B picks the next diagnostic tool →
read-only AWS diagnostic → Amazon Bedrock analysis → incident report → dashboard.

## Status: Phase 1 (foundation) complete

| Area | State |
|---|---|
| FastAPI backend skeleton, config, schemas, API-key option, CORS | Done, tested |
| Next.js frontend, 5 routes, shared nav, mode badge, API client | Done, builds |
| Simulation catalogue (5 scenarios, metadata only) | Done |
| Decider 2B inference | **Not implemented** (Phase 2). API reports `unavailable` |
| Bedrock / Strands agent | **Not implemented** (Phase 3) |
| AWS diagnostics (CloudWatch, ALB, EC2, RDS) | **Not implemented** (Phase 4) |
| 3D background, GSAP animation, full dashboard visuals | **Not implemented** (Phase 5) |

Nothing in the UI is faked: unavailable components are shown as unavailable.

## Run locally

Requirements: Python 3.11+ (tested 3.13), Node 20.9+ (tested 22).

```bash
cp .env.example .env

# backend  → http://localhost:8000  (docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# frontend → http://localhost:3000   (new terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Or with Docker: `docker compose up --build`.

## Checks

```bash
cd backend  && ruff check . && pytest -q
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

## Layout

```
backend/    FastAPI app, schemas, simulation catalogue, tests
frontend/   Next.js app (App Router, Tailwind v4)
shared/     openapi.json (generated)
docs/       API_CONTRACT.md, ARCHITECTURE.md
design.md   visual language       SKILL.md   design-engineering rules
```

## Security notes

- No credentials in the repo; use IAM roles / SSO. `.env` is git-ignored.
- AWS access is read-only by design. Wildcard CORS is rejected.
- Set `INCIDENTPILOT_API_KEY` to require `X-API-Key` on `/api/v1/*`.

## License

MIT
