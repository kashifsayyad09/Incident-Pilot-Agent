# Security notes

IncidentPilot is a read-only investigation tool. These are the controls that exist, how each
is checked, and what is **not** covered.

## Controls

| Area | Control | Check |
|---|---|---|
| AWS access | Two layers: least-privilege IAM (`infra/iam/`) and an in-process allowlist of nine read-only operations that refuses everything else before a request is built | `tests/tools/test_guard_and_iam.py` (write calls refused; policy equals allowlist) |
| Model output | Treated as untrusted. Facts need valid evidence ids and numbers present in the cited evidence, else they are demoted to hypotheses | `tests/agent/test_grounding_evidence.py` |
| Prompt injection | Evidence (log lines, change notes) is placed inside an `<evidence>` block as data; angle brackets are neutralised so text cannot close the block or forge tags. The analysis agent has **no tools**, so injected instructions cannot act | `test_security.py`, `test_analyzer.py` |
| Input | `incident_id` is limited to `[A-Za-z0-9_.-]{1,64}`; report ids are validated before touching disk | `test_security.py`, `test_investigations_api.py` |
| Cost abuse | Full investigations (each a Bedrock call) are limited to 10/min per process (`INCIDENTPILOT_MAX_INVESTIGATIONS_PER_MINUTE`, 0 = off); 429 + `Retry-After` | `test_security.py` |
| Auth | Optional `X-API-Key` (constant-time compare) on every route except `/health` | `test_security.py` |
| Errors | Unhandled errors return a generic 500; only the exception type is logged | `test_security.py` |
| Transport headers | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-store` on `/api/`; nginx adds the same | `test_security.py` |
| Secrets | No `.env` is tracked; the frontend has no env file; a scanner checks tracked files for AWS keys and private keys | `scripts/scan_secrets.py` (CI + test) |
| Containers | Backend runs as a non-root user; reports are written to a mounted `/data` volume | not exercised (no Docker in the dev sandbox) |
| Dependencies | `pip-audit` and `npm audit --omit=dev` reported no known vulnerabilities on 2026-11-12 | re-run in CI |

## Not covered (be aware)

- **The browser UI cannot send `X-API-Key`**: it has no env file by design. If you set
  `INCIDENTPILOT_API_KEY` the key protects direct API access, and the UI will get 401. To
  expose the UI beyond localhost put it behind your own authentication (SSO proxy, VPN) and
  keep the API key for scripts. The compose file publishes nginx on port 8080 with no
  authentication.
- The rate limiter is in memory and per process; several workers each get their own budget.
- Reports are stored unencrypted as JSON in the data directory. They can contain log lines
  from your systems.
- Live-mode log text is sent to Amazon Bedrock as part of the analysis prompt. Do not point
  it at log groups holding data you may not send there.
- No penetration test, no TLS (terminate it in front of nginx), no screen-reader audit.
- Real AWS, Decider 2B and Bedrock paths have not been exercised end to end.
