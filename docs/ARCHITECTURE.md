# Architecture (Phase 1 baseline)

```
Browser ──► nginx :8080 (single origin)
              ├─ /            ─► Next.js frontend :3000
              └─ /api /health /docs ─► FastAPI backend :8000
Next.js (TS, Tailwind, GSAP, R3F)  ·  JSON over same-origin /api
        ▼
FastAPI backend ── routers: health · incidents · decision
        │
        ├── simulation/   sample incidents (labeled SIMULATION)
        ├── decision_patterns/tool_selection  → HTTP → strands-decider serve :9000 (Phase 2)
        ├── Strands Agent → Amazon Bedrock          (Phase 3)
        └── Boto3 read-only: CloudWatch, ALB, EC2, RDS (Phase 4)
```

Principles: read-only AWS, explicit simulation/live separation, no fabricated
Decider output, secrets only via environment / IAM roles.

Status: API, simulation evidence, the Decider 2B tool-selection pattern and the UI exist.
Bedrock/Strands (Phase 3) and live AWS tools (Phase 4) do not.
