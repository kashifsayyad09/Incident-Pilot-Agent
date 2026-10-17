# Architecture (Phase 1 baseline)

```
Browser (Next.js, TS, Tailwind, GSAP, R3F)
        │  HTTPS / JSON  (NEXT_PUBLIC_API_BASE_URL)
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
