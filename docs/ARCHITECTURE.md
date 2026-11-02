# Architecture

```
Browser ──► nginx :8080 (single origin)
              ├─ /            ─► Next.js frontend :3000
              └─ /api /health /docs ─► FastAPI backend :8000
Next.js (TS, Tailwind, GSAP, R3F)  ·  JSON over same-origin /api
        ▼
FastAPI backend ── routers: health · incidents · decision · investigations
        │
        ├── simulation/   sample incidents (labeled SIMULATION)
        ├── decision_patterns/tool_selection  → HTTP → strands-decider serve :9000 (Phase 2)
        ├── agent/  Strands Agent (no tools) → Amazon Bedrock, evidence ids, grounding, report store (Phase 3)
        └── tools/  simulation backend · Boto3 read-only backend behind an operation allowlist (Phase 4)
```

Principles: read-only AWS, explicit simulation/live separation, no fabricated
Decider output, secrets only via environment / IAM roles.

Status: API, simulation evidence, the Decider 2B tool-selection pattern, the Bedrock analysis
agent with grounding and report storage, the diagnostic tools (simulation + live read-only AWS)
and the UI exist.

Investigation flow (`app/agent/workflow.py`): load incident from the backend → Decider 2B decision
(`decision_service.py`) → evidence bundle (E1..En) → read-only diagnostic tool on a confident
selection (findings appended as further items) → `StrandsBedrockAnalyzer` (structured
output `IncidentAnalysis`) → `ground()` demotes unsupported claims → `IncidentReport` saved
under `INCIDENTPILOT_DATA_DIR/reports/`. The analysis agent has no tools, so it cannot act.

### Bedrock IAM (least privilege)

```json
{"Version": "2012-10-17", "Statement": [{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
  "Resource": ["arn:aws:bedrock:<region>::foundation-model/<model-id>",
               "arn:aws:bedrock:<region>:<account>:inference-profile/<profile-id>"]
}]}
```

Use the resource(s) matching `INCIDENTPILOT_BEDROCK_MODEL_ID`; the model must be enabled in
your account.
