"""Smoke test a running stack (stdlib only).

    python scripts/smoke.py http://localhost:8080            # nginx / docker compose
    python scripts/smoke.py http://localhost:3000            # Next.js dev rewrites
    python scripts/smoke.py http://localhost:8080 --full     # also run one investigation
    python scripts/smoke.py http://localhost:8080 --api-key KEY

--full needs a configured Decider 2B and Bedrock model; it fails (non-zero) if either is
unavailable, and prints the API's reason. Without --full only read paths are checked.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def call(base: str, path: str, key: str | None, body: dict | None = None):
    headers = {"Accept": "application/json"}
    if key:
        headers["X-API-Key"] = key
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError as e:
        return 0, str(e.reason).encode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--api-key")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    failures = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

    s, raw = call(a.base, "/health", None)
    check("GET /health", s == 200, f"HTTP {s}")
    if s != 200:
        return 1
    health = json.loads(raw)
    print(f"      mode={health['mode']}")
    for c in health["components"]:
        print(f"      {c['name']}: {'available' if c['available'] else 'UNAVAILABLE'}")

    s, raw = call(a.base, "/api/v1/incidents", a.api_key)
    items = json.loads(raw).get("incidents", []) if s == 200 else []
    check("GET /api/v1/incidents", s == 200, f"HTTP {s}, {len(items)} incident(s)")
    s, _ = call(a.base, "/api/v1/decision/status", a.api_key)
    check("GET /api/v1/decision/status", s == 200, f"HTTP {s}")
    s, _ = call(a.base, "/api/v1/reports", a.api_key)
    check("GET /api/v1/reports", s == 200, f"HTTP {s}")
    s, _ = call(a.base, "/api/v1/investigations", a.api_key, {"incident_id": "../x"})
    check("input validation rejects a bad incident id", s == 422, f"HTTP {s}")

    if a.full:
        if not items:
            check("full investigation", False, "no incident to run")
        else:
            s, raw = call(
                a.base, "/api/v1/investigations", a.api_key, {"incident_id": items[0]["id"]}
            )
            if s == 200:
                r = json.loads(raw)
                check(
                    "POST /api/v1/investigations",
                    True,
                    f"status={r['status']}, tool={(r.get('tool_run') or {}).get('tool')}",
                )
            else:
                check("POST /api/v1/investigations", False, f"HTTP {s}: {raw[:300].decode()}")
    print("\nsmoke:", "FAILED" if failures else "ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
