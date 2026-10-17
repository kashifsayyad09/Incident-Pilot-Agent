"""Export the OpenAPI schema to shared/openapi.json (run from anywhere)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

out = Path(__file__).resolve().parents[2] / "shared" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"wrote {out}")
