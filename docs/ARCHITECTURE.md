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
        ├── decision_status  → Decider 2B adapter   (Phase 2)
        ├── Strands Agent → Amazon Bedrock          (Phase 3)
        └── Boto3 read-only: CloudWatch, ALB, EC2, RDS (Phase 4)
```

Principles: read-only AWS, explicit simulation/live separation, no fabricated
Decider output, secrets only via environment / IAM roles.

Status: only the API skeleton, simulation catalogue metadata and frontend shell exist.
